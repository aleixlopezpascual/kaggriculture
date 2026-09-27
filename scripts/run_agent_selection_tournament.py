import argparse
import contextlib
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import random
import sys
import time
import uuid
from pathlib import Path
from typing import Any

with contextlib.suppress(ImportError):
    import kaggle_environments


class TournamentError(Exception):
    pass


def check_engine_version() -> None:
    try:
        version = importlib.metadata.version("kaggle-environments")
    except importlib.metadata.PackageNotFoundError:
        version = None
    if version != "1.32.7":
        print(
            f"Error: Required kaggle-environments version 1.32.7, " f"but got {version}"
        )
        sys.exit(1)


def verify_candidate(source_path: str, expected_hash: str) -> str:
    path = Path(source_path)
    if not path.is_file():
        raise TournamentError(f"Candidate source file not found: {source_path}")
    if path.suffix == ".ipynb":
        raise TournamentError(f"Candidate source cannot be a notebook: {source_path}")
    if path.suffix != ".py":
        raise TournamentError(f"Candidate source must be a .py file: {source_path}")
    source_bytes = path.read_bytes()
    actual_hash = hashlib.sha256(source_bytes).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(
            f"SHA256 mismatch for {source_path}: expected {expected_hash}, "
            f"got {actual_hash}"
        )
    return source_bytes.decode("utf-8")


def load_agent(source_code: str, source_path: str, module_name: str) -> tuple[Any, Any]:
    parent_dir = str(Path(source_path).parent.resolve())
    path_added = False
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        path_added = True

    try:
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        if spec is None:
            raise TournamentError(f"Cannot load module {module_name}")
        module = importlib.util.module_from_spec(spec)
        module.__file__ = str(Path(source_path).resolve())
        sys.modules[module_name] = module
        exec(compile(source_code, source_path, "exec"), module.__dict__)

        agent_fn = getattr(module, "agent", None)
        if not callable(agent_fn):
            raise TournamentError(
                f"No callable 'agent' function found in {source_path}"
            )
        return agent_fn, module
    finally:
        if path_added:
            sys.path.remove(parent_dir)


def validate_seed(seed: int, phase: str, manifest: dict) -> None:
    design = manifest.get("design", {})
    seeds = design.get(f"{phase}_seeds", [])
    if len(seeds) != len(set(seeds)):
        raise ValueError(f"Duplicate seeds found in manifest for phase {phase}")
    if seed not in seeds:
        raise ValueError(f"Seed {seed} not listed in manifest for phase {phase}")


def generate_schedule(
    candidates: list[dict], phase: str, finalists: list[str] | None = None
) -> list[dict]:
    schedule = []
    candidate_ids = [c["id"] for c in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Duplicate candidate IDs found in manifest.")

    if phase == "screening":
        for i in range(len(candidate_ids)):
            for j in range(i + 1, len(candidate_ids)):
                schedule.append(
                    {"agent_0": candidate_ids[i], "agent_1": candidate_ids[j]}
                )
                schedule.append(
                    {"agent_0": candidate_ids[j], "agent_1": candidate_ids[i]}
                )
    elif phase == "confirmation":
        if not finalists or len(finalists) != 2:
            raise TournamentError("Confirmation phase requires exactly two finalists.")
        if len(set(finalists)) != 2:
            raise ValueError("Duplicate finalists provided.")
        if finalists[0] not in candidate_ids or finalists[1] not in candidate_ids:
            raise TournamentError("Finalists must be valid candidate IDs.")

        f1, f2 = finalists
        schedule.append({"agent_0": f1, "agent_1": f2})
        schedule.append({"agent_0": f2, "agent_1": f1})

        for cid in candidate_ids:
            if cid not in finalists:
                schedule.append({"agent_0": f1, "agent_1": cid})
                schedule.append({"agent_0": cid, "agent_1": f1})
                schedule.append({"agent_0": f2, "agent_1": cid})
                schedule.append({"agent_0": cid, "agent_1": f2})
    else:
        raise TournamentError(f"Unknown phase: {phase}")

    for match in schedule:
        if match["agent_0"] == match["agent_1"]:
            raise ValueError("Self-match detected in schedule.")

    return sorted(schedule, key=lambda x: (x["agent_0"], x["agent_1"]))


def capture_telemetry(agent_fn: Any, module: Any) -> dict:
    telemetry = {}
    if hasattr(agent_fn, "telemetry") and isinstance(agent_fn.telemetry, dict):
        telemetry.update(copy.deepcopy(agent_fn.telemetry))
    for k, v in vars(module).items():
        if (
            isinstance(k, str)
            and (k.endswith("_REPORT") or k.endswith("_STATS"))
            and isinstance(v, dict)
        ):
            telemetry[k] = copy.deepcopy(v)
    return telemetry


def wrap_agent(agent_fn: Any) -> tuple[Any, list[dict]]:
    callbacks: list[dict] = []

    def wrapped(observation: Any, configuration: Any) -> Any:
        start = time.perf_counter()
        try:
            action = agent_fn(observation, configuration)
            elapsed = time.perf_counter() - start
            callbacks.append({"elapsed": elapsed, "error": None})
            return action
        except Exception as e:
            elapsed = time.perf_counter() - start
            callbacks.append({"elapsed": elapsed, "error": str(e)})
            raise

    return wrapped, callbacks


def compute_agent_stats(callbacks: list[dict]) -> dict:
    times = [c["elapsed"] for c in callbacks]
    errors = sum(1 for c in callbacks if c.get("error"))
    if not times:
        return {
            "calls": 0,
            "max_ms": 0.0,
            "p95_ms": 0.0,
            "over_100ms": 0,
            "total_ms": 0.0,
            "errors": 0,
        }
    times.sort()
    return {
        "calls": len(times),
        "max_ms": round(times[-1] * 1000, 2),
        "p95_ms": round(
            (
                times[int(0.95 * len(times))] * 1000
                if len(times) >= 20
                else times[-1] * 1000
            ),
            2,
        ),
        "over_100ms": sum(1 for t in times if t > 0.100),
        "total_ms": round(sum(times) * 1000, 2),
        "errors": errors,
    }


def run_match(seed: int, agent_0_info: dict, agent_1_info: dict) -> dict:
    match_start = time.perf_counter()
    mod_name_0 = f"agent_{agent_0_info['id']}_{uuid.uuid4().hex[:8]}"
    mod_name_1 = f"agent_{agent_1_info['id']}_{uuid.uuid4().hex[:8]}"

    status_0 = status_1 = "ERROR"
    reward_0 = reward_1 = 0
    error_0 = error_1 = ""
    calls_0: list[dict] = []
    calls_1: list[dict] = []
    tel_0: dict = {}
    tel_1: dict = {}

    try:
        fn_0, mod_0 = load_agent(
            agent_0_info["source"], agent_0_info["path"], mod_name_0
        )
        fn_1, mod_1 = load_agent(
            agent_1_info["source"], agent_1_info["path"], mod_name_1
        )

        wrapped_0, calls_0 = wrap_agent(fn_0)
        wrapped_1, calls_1 = wrap_agent(fn_1)

        env = kaggle_environments.make(
            "kaggriculture", configuration={"seed": seed, "episodeSteps": 720}
        )
        _ = env.run([wrapped_0, wrapped_1])

        state_0 = env.steps[-1][0]
        state_1 = env.steps[-1][1]

        reward_0 = state_0["reward"] or 0
        reward_1 = state_1["reward"] or 0

        status_0 = state_0["status"]
        status_1 = state_1["status"]

        info_0 = state_0.get("info", {})
        info_1 = state_1.get("info", {})

        error_0 = state_0.get("error", "") or info_0.get("error", "")
        error_1 = state_1.get("error", "") or info_1.get("error", "")

        tel_0 = capture_telemetry(fn_0, mod_0)
        tel_1 = capture_telemetry(fn_1, mod_1)

    except Exception as e:
        status_0 = status_1 = "ERROR"
        reward_0 = reward_1 = 0
        error_0 = error_1 = f"Runner exception: {e}"
    finally:
        sys.modules.pop(mod_name_0, None)
        sys.modules.pop(mod_name_1, None)

    match_duration = time.perf_counter() - match_start

    margin_0 = reward_0 - reward_1
    margin_1 = reward_1 - reward_0

    valid_match = True
    fail_0 = status_0 != "DONE" or bool(error_0)
    fail_1 = status_1 != "DONE" or bool(error_1)
    scoring_basis = "coins"

    if fail_0 and fail_1:
        pts_0, pts_1 = None, None
        win_0, win_1 = "invalid", "invalid"
        scoring_basis = "invalid"
        valid_match = False
    elif fail_0:
        pts_0, pts_1 = 0.0, 1.0
        win_0, win_1 = "loss", "win"
        scoring_basis = "forfeit"
    elif fail_1:
        pts_0, pts_1 = 1.0, 0.0
        win_0, win_1 = "win", "loss"
        scoring_basis = "forfeit"
    else:
        if reward_0 > reward_1:
            pts_0, pts_1 = 1.0, 0.0
            win_0, win_1 = "win", "loss"
        elif reward_0 < reward_1:
            pts_0, pts_1 = 0.0, 1.0
            win_0, win_1 = "loss", "win"
        else:
            pts_0, pts_1 = 0.5, 0.5
            win_0, win_1 = "tie", "tie"

    return {
        "seed": seed,
        "valid_match": valid_match,
        "scoring_basis": scoring_basis,
        "duration_sec": round(match_duration, 2),
        "agent_0": {
            "id": agent_0_info["id"],
            "hash": agent_0_info["hash"],
            "terminal_status": status_0,
            "error": error_0,
            "coins": float(reward_0),
            "margin": float(margin_0),
            "outcome": win_0,
            "points": pts_0,
            "stats": compute_agent_stats(calls_0),
            "telemetry": tel_0,
        },
        "agent_1": {
            "id": agent_1_info["id"],
            "hash": agent_1_info["hash"],
            "terminal_status": status_1,
            "error": error_1,
            "coins": float(reward_1),
            "margin": float(margin_1),
            "outcome": win_1,
            "points": pts_1,
            "stats": compute_agent_stats(calls_1),
            "telemetry": tel_1,
        },
    }


def aggregate_results(
    inputs: list[str], expected_phase: str, output: str, force: bool
) -> None:
    out_path = Path(output)
    if out_path.exists() and not force:
        print(f"Error: Output file {output} exists. Use --force to overwrite.")
        sys.exit(1)

    all_results = []
    manifest_hash = None
    finalists = None
    candidate_ids = None
    planned_seeds = None
    smoke_test = None
    seeds_processed = set()

    for inp in inputs:
        with Path(inp).open(encoding="utf-8") as f:
            data = json.load(f)

        required_fields = [
            "phase",
            "manifest_hash",
            "engine_version",
            "seed",
            "candidate_ids",
            "planned_seeds",
            "planned_games",
            "completed_games",
            "smoke_test",
            "results",
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field {field} in {inp}")

        if data["phase"] != expected_phase:
            raise ValueError(
                f"Input {inp} is phase {data['phase']}, expected {expected_phase}"
            )
        if manifest_hash is None:
            manifest_hash = data["manifest_hash"]
        elif manifest_hash != data["manifest_hash"]:
            raise ValueError(f"Manifest hash mismatch in {inp}")
        if data["engine_version"] != "1.32.7":
            raise ValueError(f"Engine version mismatch in {inp}")

        if candidate_ids is None:
            candidate_ids = sorted(data["candidate_ids"])
        elif candidate_ids != sorted(data["candidate_ids"]):
            raise ValueError(f"Candidate IDs mismatch in {inp}")

        if planned_seeds is None:
            planned_seeds = data["planned_seeds"]
        elif planned_seeds != data["planned_seeds"]:
            raise ValueError(f"Planned seeds mismatch in {inp}")

        if smoke_test is None:
            smoke_test = data["smoke_test"]
        elif smoke_test != data["smoke_test"]:
            raise ValueError(f"Smoke test flag mismatch in {inp}")

        if expected_phase == "confirmation":
            if "finalists" not in data:
                raise ValueError(f"Missing finalists in {inp}")
            if finalists is None:
                finalists = tuple(sorted(data["finalists"]))
            elif finalists != tuple(sorted(data["finalists"])):
                raise ValueError(f"Finalists mismatch in {inp}")

        seed = data["seed"]
        if seed not in planned_seeds:
            raise ValueError(f"Seed {seed} is not in planned_seeds in {inp}")
        if seed in seeds_processed:
            raise ValueError(f"Duplicate or mixed seeds found: {seed} is duplicated")
        seeds_processed.add(seed)

        if data["planned_games"] != data["completed_games"]:
            raise ValueError(
                f"Planned games ({data['planned_games']}) != "
                f"completed games ({data['completed_games']}) in {inp}"
            )
        if len(data["results"]) != data["planned_games"]:
            raise ValueError(
                f"Results count ({len(data['results'])}) != "
                f"planned games ({data['planned_games']}) in {inp}"
            )

        for r in data["results"]:
            if r.get("seed") != seed:
                raise ValueError(
                    f"Mismatched result seed {r.get('seed')} in file for seed {seed}"
                )
            if not r.get("valid_match", True):
                if r.get("scoring_basis") != "invalid":
                    raise ValueError(
                        f"valid_match=False but scoring_basis is not 'invalid': {r}"
                    )
                out0 = r.get("agent_0", {}).get("outcome")
                out1 = r.get("agent_1", {}).get("outcome")
                if out0 != "invalid" or out1 != "invalid":
                    raise ValueError(
                        f"valid_match=False but outcomes are not 'invalid': {r}"
                    )
                pts0 = r.get("agent_0", {}).get("points")
                pts1 = r.get("agent_1", {}).get("points")
                if pts0 is not None or pts1 is not None:
                    raise ValueError(f"valid_match=False but points are not None: {r}")
            else:
                basis = r.get("scoring_basis")
                if basis not in ("coins", "forfeit"):
                    raise ValueError(
                        f"valid_match=True but scoring_basis invalid: {basis}"
                    )

                a0 = r.get("agent_0", {})
                a1 = r.get("agent_1", {})

                if basis == "coins":
                    if (
                        a0.get("terminal_status") != "DONE"
                        or a1.get("terminal_status") != "DONE"
                    ):
                        raise ValueError("valid_match=True with coins but not DONE")
                    if bool(a0.get("error")) or bool(a1.get("error")):
                        raise ValueError("valid_match=True with coins but has error")

                    c0 = a0.get("coins", 0)
                    c1 = a1.get("coins", 0)

                    if c0 > c1:
                        exp_out0, exp_out1 = "win", "loss"
                        exp_pts0, exp_pts1 = 1.0, 0.0
                    elif c0 < c1:
                        exp_out0, exp_out1 = "loss", "win"
                        exp_pts0, exp_pts1 = 0.0, 1.0
                    else:
                        exp_out0, exp_out1 = "tie", "tie"
                        exp_pts0, exp_pts1 = 0.5, 0.5

                    if a0.get("outcome") != exp_out0 or a1.get("outcome") != exp_out1:
                        raise ValueError(
                            "valid_match=True with coins but outcome mismatch"
                        )
                    if a0.get("points") != exp_pts0 or a1.get("points") != exp_pts1:
                        raise ValueError(
                            "valid_match=True with coins but points mismatch"
                        )
                elif basis == "forfeit":
                    fail0 = a0.get("terminal_status") != "DONE" or bool(a0.get("error"))
                    fail1 = a1.get("terminal_status") != "DONE" or bool(a1.get("error"))
                    if fail0 == fail1:
                        raise ValueError(
                            "valid_match=True with forfeit must have exactly one "
                            "failed player"
                        )

                    if fail0:
                        exp_out0, exp_out1 = "loss", "win"
                        exp_pts0, exp_pts1 = 0.0, 1.0
                    else:
                        exp_out0, exp_out1 = "win", "loss"
                        exp_pts0, exp_pts1 = 1.0, 0.0

                    if a0.get("outcome") != exp_out0 or a1.get("outcome") != exp_out1:
                        raise ValueError(
                            "valid_match=True with forfeit but outcome mismatch"
                        )
                    if a0.get("points") != exp_pts0 or a1.get("points") != exp_pts1:
                        raise ValueError(
                            "valid_match=True with forfeit but points mismatch"
                        )

            all_results.append(r)

    if not all_results:
        raise ValueError("No results found in any input files")

    if planned_seeds is not None and len(planned_seeds) != len(set(planned_seeds)):
        raise ValueError(f"Duplicate values found in planned_seeds: {planned_seeds}")

    if planned_seeds is not None and seeds_processed != set(planned_seeds):
        missing_seeds = set(planned_seeds) - seeds_processed
        raise ValueError(
            "Not all planned seeds were provided in the input set. "
            f"Missing planned seed(s): {sorted(missing_seeds)}"
        )

    expected_schedule = generate_schedule(
        [{"id": cid} for cid in candidate_ids],
        expected_phase,
        list(finalists) if finalists else None,
    )
    expected_pairs = [(m["agent_0"], m["agent_1"]) for m in expected_schedule]
    expected_pairs_set = set(expected_pairs)

    seed_pairs = {}
    for r in all_results:
        s = r["seed"]
        a0 = r["agent_0"]["id"]
        a1 = r["agent_1"]["id"]
        if s not in seed_pairs:
            seed_pairs[s] = []
        seed_pairs[s].append((a0, a1))

    for s, pairs in seed_pairs.items():
        if len(pairs) != len(set(pairs)):
            raise ValueError(f"Duplicate matches in seed {s}")
        if set(pairs) != expected_pairs_set:
            missing = expected_pairs_set - set(pairs)
            extra = set(pairs) - expected_pairs_set
            raise ValueError(
                f"Matches for seed {s} do not exactly match expected schedule. "
                f"Missing: {missing}, Extra: {extra}"
            )

    agent_data = {}
    for r in all_results:
        for p_key, _ in [("agent_0", "agent_1"), ("agent_1", "agent_0")]:
            aid = r[p_key]["id"]
            if aid not in agent_data:
                agent_data[aid] = []
            agent_data[aid].append(r)

    aggregated = {}
    seeds_list = sorted(seeds_processed)

    rng = random.Random(42)
    n_boot = 10_000

    def ci(arr: list[float]) -> tuple[float, float]:
        if not arr:
            return (0.0, 0.0)
        return (arr[int(0.025 * len(arr))], arr[int(0.975 * len(arr))])

    for aid, matches in agent_data.items():
        boot_points = []
        boot_win_rate = []
        boot_margin = []
        boot_coins = []
        boot_opp_coins = []

        seed_matches = {s: [] for s in seeds_list}
        for m in matches:
            seed_matches[m["seed"]].append(m)

        for _ in range(n_boot):
            sample_seeds = rng.choices(seeds_list, k=len(seeds_list))
            s_points = s_wins = s_margin = s_coins = s_opp_coins = 0.0
            count = 0
            for s in sample_seeds:
                for m in seed_matches[s]:
                    if not m.get("valid_match", True):
                        continue
                    is_p0 = m["agent_0"]["id"] == aid
                    p = m["agent_0"] if is_p0 else m["agent_1"]
                    opp = m["agent_1"] if is_p0 else m["agent_0"]

                    if p.get("points") is not None:
                        s_points += p["points"]
                    s_wins += 1.0 if p["outcome"] == "win" else 0.0
                    s_margin += p["margin"]
                    s_coins += p["coins"]
                    s_opp_coins += opp["coins"]
                    count += 1
            if count > 0:
                boot_points.append(s_points / count)
                boot_win_rate.append(s_wins / count)
                boot_margin.append(s_margin / count)
                boot_coins.append(s_coins / count)
                boot_opp_coins.append(s_opp_coins / count)

        boot_points.sort()
        boot_win_rate.sort()
        boot_margin.sort()
        boot_coins.sort()
        boot_opp_coins.sort()

        pts = 0.0
        wins, losses, ties = 0, 0, 0
        margin = coins = opp_coins = 0.0
        valid_count = technical_errors = callback_errors = 0
        pairwise = {}

        for m in matches:
            is_p0 = m["agent_0"]["id"] == aid
            p = m["agent_0"] if is_p0 else m["agent_1"]
            opp = m["agent_1"] if is_p0 else m["agent_0"]
            opp_id = opp["id"]

            if opp_id not in pairwise:
                pairwise[opp_id] = {
                    "wins": 0,
                    "losses": 0,
                    "ties": 0,
                    "points": 0.0,
                    "matches": 0,
                    "invalid": 0,
                }

            if p["terminal_status"] == "ERROR" or bool(p["error"]):
                technical_errors += 1

            callback_errors += p.get("stats", {}).get("errors", 0)

            if not m.get("valid_match", True):
                pairwise[opp_id]["invalid"] += 1
                pairwise[opp_id]["matches"] += 1
                continue

            valid_count += 1
            pairwise[opp_id]["matches"] += 1

            if p.get("points") is not None:
                pts += p["points"]
                pairwise[opp_id]["points"] += p["points"]

            if p["outcome"] == "win":
                wins += 1
                pairwise[opp_id]["wins"] += 1
            elif p["outcome"] == "loss":
                losses += 1
                pairwise[opp_id]["losses"] += 1
            elif p["outcome"] == "tie":
                ties += 1
                pairwise[opp_id]["ties"] += 1

            margin += p["margin"]
            coins += p["coins"]
            opp_coins += opp["coins"]

        for pw in pairwise.values():
            valid_pw_count = pw["matches"] - pw["invalid"]
            pw["points_rate"] = (
                pw["points"] / valid_pw_count if valid_pw_count > 0 else 0.0
            )

        aggregated[aid] = {
            "matches": len(matches),
            "valid_matches": valid_count,
            "invalid_matches": len(matches) - valid_count,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "technical_errors": technical_errors,
            "callback_errors": callback_errors,
            "win_rate": wins / valid_count if valid_count else 0.0,
            "win_rate_ci_95": ci(boot_win_rate),
            "match_points_rate": pts / valid_count if valid_count else 0.0,
            "match_points_rate_ci_95": ci(boot_points),
            "mean_margin": margin / valid_count if valid_count else 0.0,
            "mean_margin_ci_95": ci(boot_margin),
            "mean_coins": coins / valid_count if valid_count else 0.0,
            "mean_coins_ci_95": ci(boot_coins),
            "mean_opp_coins": opp_coins / valid_count if valid_count else 0.0,
            "mean_opp_coins_ci_95": ci(boot_opp_coins),
            "pairwise": pairwise,
        }

    out_data = {
        "phase": expected_phase,
        "manifest_hash": manifest_hash,
        "engine_version": "1.32.7",
        "seeds_aggregated": seeds_list,
        "total_matches": len(all_results),
        "agent_summaries": aggregated,
    }

    if expected_phase == "confirmation" and finalists:
        f1, f2 = finalists
        f1_matches = [
            m
            for m in all_results
            if (
                (m["agent_0"]["id"] == f1 and m["agent_1"]["id"] == f2)
                or (m["agent_0"]["id"] == f2 and m["agent_1"]["id"] == f1)
            )
        ]

        valid_f1_matches = [m for m in f1_matches if m.get("valid_match", True)]
        seed_f1_matches = {s: [] for s in seeds_list}
        for m in f1_matches:
            seed_f1_matches[m["seed"]].append(m)

        boot_diff = []
        for _ in range(n_boot):
            sample_seeds = rng.choices(seeds_list, k=len(seeds_list))
            s_f1_pts = 0.0
            count = 0
            for s in sample_seeds:
                for m in seed_f1_matches[s]:
                    if not m.get("valid_match", True):
                        continue
                    is_f1_p0 = m["agent_0"]["id"] == f1
                    p = m["agent_0"] if is_f1_p0 else m["agent_1"]
                    if p.get("points") is not None:
                        s_f1_pts += p["points"]
                    count += 1
            if count > 0:
                f1_rate = s_f1_pts / count
                f2_rate = 1.0 - f1_rate
                boot_diff.append(f1_rate - f2_rate)

        boot_diff.sort()
        f1_wins = ties = 0
        f1_pts = f1_margin = 0.0

        for m in valid_f1_matches:
            is_f1_p0 = m["agent_0"]["id"] == f1
            p = m["agent_0"] if is_f1_p0 else m["agent_1"]
            if p["outcome"] == "win":
                f1_wins += 1
            elif p["outcome"] == "tie":
                ties += 1
            if p.get("points") is not None:
                f1_pts += p["points"]
            f1_margin += p["margin"]

        count_valid = len(valid_f1_matches)
        f1_points_rate = f1_pts / count_valid if count_valid > 0 else 0.0
        f2_points_rate = 1.0 - f1_points_rate if count_valid > 0 else 0.0
        diff = f1_points_rate - f2_points_rate

        out_data["confirmation_stats"] = {
            "head_to_head_matches": len(f1_matches),
            "valid_matches": count_valid,
            f"{f1}_wins": f1_wins,
            f"{f2}_wins": count_valid - f1_wins - ties,
            "ties": ties,
            f"{f1}_points_rate": f1_points_rate,
            f"{f2}_points_rate": f2_points_rate,
            f"{f1}_mean_margin": f1_margin / count_valid if count_valid > 0 else 0.0,
            "point_rate_diff": diff,
            "bootstrap_95_ci": ci(boot_diff),
        }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, sort_keys=True)
    print(f"Aggregated results saved to {out_path}")


def run_tournament(args: argparse.Namespace) -> None:
    check_engine_version()

    manifest_path = Path(args.manifest).resolve()
    with manifest_path.open(encoding="utf-8") as f:
        manifest_raw = f.read()
        manifest_hash = hashlib.sha256(manifest_raw.encode("utf-8")).hexdigest()
        manifest = json.loads(manifest_raw)

    validate_seed(args.seed, args.phase, manifest)

    candidates_info = []
    all_candidate_ids = [c["id"] for c in manifest.get("candidates", [])]

    if args.candidate_ids:
        if len(args.candidate_ids) != len(set(args.candidate_ids)):
            print("Error: Duplicate candidate IDs provided.")
            sys.exit(1)
        for cid in args.candidate_ids:
            if cid not in all_candidate_ids:
                print(f"Error: Unknown candidate ID {cid}")
                sys.exit(1)

    for c in manifest.get("candidates", []):
        if args.candidate_ids and c["id"] not in args.candidate_ids:
            continue

        raw_path = Path(c["source_path"])
        if raw_path.is_absolute():
            resolved_path = raw_path
        else:
            resolved_path = (manifest_path.parent / raw_path).resolve()

        source_code = verify_candidate(str(resolved_path), c["source_sha256"])
        candidates_info.append(
            {
                "id": c["id"],
                "path": str(resolved_path),
                "hash": c["source_sha256"],
                "source": source_code,
            }
        )

    if not candidates_info:
        print("No candidates matched or found in manifest.")
        sys.exit(1)

    schedule = generate_schedule(
        manifest.get("candidates", []), args.phase, args.finalists
    )

    is_smoke = False
    if args.candidate_ids:
        is_smoke = True
        schedule = [
            m
            for m in schedule
            if m["agent_0"] in args.candidate_ids and m["agent_1"] in args.candidate_ids
        ]

        # Verify smoke subsets schedule exactly selected candidates
        scheduled_agents = set()
        for m in schedule:
            scheduled_agents.add(m["agent_0"])
            scheduled_agents.add(m["agent_1"])
        if scheduled_agents != set(args.candidate_ids):
            print(
                "Error: Smoke subset failed to schedule exactly the "
                "selected candidates."
            )
            sys.exit(1)

    if args.output:
        out_path = Path(args.output)
        if out_path.exists() and not args.force:
            print(f"Error: Output file {args.output} exists. Use --force to overwrite.")
            sys.exit(1)

    results = []
    agent_info_map = {c["id"]: c for c in candidates_info}

    for match in schedule:
        res = run_match(
            args.seed,
            agent_info_map[match["agent_0"]],
            agent_info_map[match["agent_1"]],
        )
        results.append(res)

    out_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": args.phase,
        "seed": args.seed,
        "engine_version": "1.32.7",
        "manifest_hash": manifest_hash,
        "candidate_ids": [c["id"] for c in candidates_info],
        "planned_seeds": manifest.get("design", {}).get(f"{args.phase}_seeds", []),
        "planned_games": len(schedule),
        "completed_games": len(results),
        "smoke_test": is_smoke,
        "results": results,
    }

    if args.phase == "confirmation":
        out_data["finalists"] = args.finalists

    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, sort_keys=True)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(out_data, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproducible local Kaggriculture agent-selection tournament."
    )
    parser.add_argument("--aggregate", action="store_true", help="Run aggregation mode")
    parser.add_argument(
        "--inputs", type=str, nargs="+", help="Input JSON files for aggregation"
    )
    parser.add_argument("--manifest", type=str, help="Path to candidates.json manifest")
    parser.add_argument(
        "--phase",
        type=str,
        choices=["screening", "confirmation"],
        help="Tournament phase",
    )
    parser.add_argument("--seed", type=int, help="Single seed for this batch")
    parser.add_argument(
        "--finalists",
        type=str,
        nargs="+",
        help="Exactly two candidate IDs for confirmation phase",
    )
    parser.add_argument(
        "--candidate-ids",
        type=str,
        nargs="+",
        help="Subset of candidate IDs for smoke testing",
    )
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite output file if it exists"
    )

    args = parser.parse_args()

    if args.aggregate:
        if not args.inputs or not args.phase or not args.output:
            parser.error("--aggregate requires --inputs, --phase, and --output")
        aggregate_results(args.inputs, args.phase, args.output, args.force)
    else:
        if not args.manifest or not args.phase or args.seed is None:
            parser.error("Run mode requires --manifest, --phase, and --seed")
        if args.phase == "confirmation" and (
            not args.finalists or len(args.finalists) != 2
        ):
            parser.error("--phase confirmation requires exactly two --finalists")
        run_tournament(args)


if __name__ == "__main__":
    main()
