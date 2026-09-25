import argparse
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

from kaggle_environments import make


class OverrideError(Exception):
    pass


class AggregationError(Exception):
    pass


def create_candidate_source(baseline_source: str) -> str:
    target = "V9_RACE_DEFAULT = 40"
    replacement = "V9_RACE_DEFAULT = 41"

    count = baseline_source.count(target)
    if count == 0:
        raise OverrideError(f"Target '{target}' not found in baseline source.")
    if count > 1:
        raise OverrideError(
            f"Target '{target}' found {count} times in baseline source. "
            "Expected exactly 1."
        )

    return baseline_source.replace(target, replacement)


def build_environment_config(seed: int) -> dict:
    return {"seed": seed, "episodeSteps": 720}


def load_agent_module(source_text: str, source_path: Path, module_name: str):
    parent_dir = str(source_path.parent.resolve())
    added_to_path = False
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        added_to_path = True

    try:
        spec = importlib.util.spec_from_loader(
            module_name, loader=None, origin=str(source_path)
        )
        mod = importlib.util.module_from_spec(spec)
        mod.__file__ = str(source_path.resolve())
        sys.modules[module_name] = mod
        try:
            exec(compile(source_text, str(source_path), "exec"), mod.__dict__)
        except Exception:
            del sys.modules[module_name]
            raise
        return mod
    finally:
        if added_to_path:
            sys.path.remove(parent_dir)


def capture_telemetry(agent_fn, module=None) -> dict:
    telemetry = {}
    if hasattr(agent_fn, "telemetry") and isinstance(agent_fn.telemetry, dict):
        telemetry = copy.deepcopy(agent_fn.telemetry)
    if module is not None:
        for k, v in vars(module).items():
            if (
                isinstance(k, str)
                and (k.endswith("_REPORT") or k.endswith("_STATS"))
                and isinstance(v, dict)
            ):
                telemetry[k] = copy.deepcopy(v)
    return telemetry


def generate_seeds(rng_seed: int, count: int, exclude: list[int]) -> list[int]:
    rng = random.Random(rng_seed)
    seeds = []
    while len(seeds) < count:
        s = rng.randint(0, 1_000_000_000)
        if s not in exclude and s not in seeds:
            seeds.append(s)
    return seeds


def aggregate_results(results: list[dict]) -> dict:
    paired = {}
    for r in results:
        key = (r["seed"], r["opponent"], r["seat"])
        if key not in paired:
            paired[key] = {}
        if r["arm"] not in ("baseline", "candidate"):
            raise AggregationError(f"Unknown arm label: {r['arm']}")
        if r["match_points"] not in (0, 0.5, 1):
            raise AggregationError(f"Invalid match_points: {r['match_points']}")
        if r["arm"] in paired[key]:
            raise AggregationError(f"Duplicate arm for {key}")
        paired[key][r["arm"]] = r

    pairs = []
    points_deltas = []
    margin_deltas = []
    cash_deltas = []

    for key, group in paired.items():
        if "baseline" not in group or "candidate" not in group:
            raise AggregationError(f"Missing arm for {key}")

        b = group["baseline"]
        c = group["candidate"]

        p_delta = c["match_points"] - b["match_points"]
        m_delta = c["margin"] - b["margin"]
        c_delta = c["own_cash"] - b["own_cash"]

        pairs.append(
            {
                "key": key,
                "baseline": b,
                "candidate": c,
                "points_delta": p_delta,
                "margin_delta": m_delta,
                "cash_delta": c_delta,
            }
        )
        points_deltas.append(p_delta)
        margin_deltas.append(m_delta)
        cash_deltas.append(c_delta)

    seeds = sorted({k[0] for k in paired})
    seed_groups = {s: [] for s in seeds}
    for p in pairs:
        seed_groups[p["key"][0]].append(p)

    rng = random.Random(42)
    n_boot = 10_000
    boot_points = []
    boot_margin = []

    if seeds and pairs:
        for _ in range(n_boot):
            sample_seeds = rng.choices(seeds, k=len(seeds))
            sample_points = 0
            sample_margin = 0
            count = 0
            for s in sample_seeds:
                for p in seed_groups[s]:
                    sample_points += p["points_delta"]
                    sample_margin += p["margin_delta"]
                    count += 1
            if count > 0:
                boot_points.append(sample_points / count)
                boot_margin.append(sample_margin / count)

        boot_points.sort()
        boot_margin.sort()
        ci_points = (boot_points[int(0.025 * n_boot)], boot_points[int(0.975 * n_boot)])
        ci_margin = (boot_margin[int(0.025 * n_boot)], boot_margin[int(0.975 * n_boot)])
    else:
        ci_points = (0, 0)
        ci_margin = (0, 0)

    mean_points_delta = sum(points_deltas) / len(points_deltas) if points_deltas else 0
    mean_margin_delta = sum(margin_deltas) / len(margin_deltas) if margin_deltas else 0
    mean_cash_delta = sum(cash_deltas) / len(cash_deltas) if cash_deltas else 0

    seed_breakdown = {}
    opponent_breakdown = {}

    for p in pairs:
        s = p["key"][0]
        o = p["key"][1]

        if s not in seed_breakdown:
            seed_breakdown[s] = {
                "points_delta": 0,
                "margin_delta": 0,
                "cash_delta": 0,
                "matches": 0,
            }
        seed_breakdown[s]["points_delta"] += p["points_delta"]
        seed_breakdown[s]["margin_delta"] += p["margin_delta"]
        seed_breakdown[s]["cash_delta"] += p["cash_delta"]
        seed_breakdown[s]["matches"] += 1

        if o not in opponent_breakdown:
            opponent_breakdown[o] = {
                "points_delta": 0,
                "margin_delta": 0,
                "cash_delta": 0,
                "matches": 0,
            }
        opponent_breakdown[o]["points_delta"] += p["points_delta"]
        opponent_breakdown[o]["margin_delta"] += p["margin_delta"]
        opponent_breakdown[o]["cash_delta"] += p["cash_delta"]
        opponent_breakdown[o]["matches"] += 1

    for b_data in seed_breakdown.values():
        b_data["mean_points_delta"] = b_data["points_delta"] / b_data["matches"]
        b_data["mean_margin_delta"] = b_data["margin_delta"] / b_data["matches"]
        b_data["mean_cash_delta"] = b_data["cash_delta"] / b_data["matches"]

    for b_data in opponent_breakdown.values():
        b_data["mean_points_delta"] = b_data["points_delta"] / b_data["matches"]
        b_data["mean_margin_delta"] = b_data["margin_delta"] / b_data["matches"]
        b_data["mean_cash_delta"] = b_data["cash_delta"] / b_data["matches"]

    return {
        "pairs": pairs,
        "mean_points_delta": mean_points_delta,
        "mean_margin_delta": mean_margin_delta,
        "mean_cash_delta": mean_cash_delta,
        "ci_95_points": ci_points,
        "ci_95_margin": ci_margin,
        "absolute_records": {
            "baseline": {
                "wins": sum(1 for p in pairs if p["baseline"]["match_points"] == 1.0),
                "losses": sum(1 for p in pairs if p["baseline"]["match_points"] == 0.0),
                "ties": sum(1 for p in pairs if p["baseline"]["match_points"] == 0.5),
            },
            "candidate": {
                "wins": sum(1 for p in pairs if p["candidate"]["match_points"] == 1.0),
                "losses": sum(
                    1 for p in pairs if p["candidate"]["match_points"] == 0.0
                ),
                "ties": sum(1 for p in pairs if p["candidate"]["match_points"] == 0.5),
            },
        },
        "breakdowns": {"by_seed": seed_breakdown, "by_opponent": opponent_breakdown},
    }


def has_telemetry_error(telemetry: dict) -> bool:
    def scan(obj, current_key=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if scan(v, str(k)):
                    return True
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                if scan(item, current_key):
                    return True
        elif isinstance(obj, bool):
            return False
        elif isinstance(obj, (int, float)) and obj > 0:
            k_lower = current_key.lower()
            if "error" in k_lower or "exception" in k_lower or "failure" in k_lower:
                return True
        return False

    return scan(telemetry)


def get_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="A/B Experiment for RACE Horizon")
    parser.add_argument("--smoke", action="store_true", help="Run short smoke panel")
    parser.add_argument("--seeds", type=int, nargs="+", help="Explicit seeds to run")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    engine_version = importlib.metadata.version("kaggle-environments")
    if engine_version != "1.32.7":
        print(
            f"Error: kaggle-environments version {engine_version} "
            "found, expected 1.32.7"
        )
        sys.exit(1)

    project_root = Path(__file__).resolve().parents[1]
    baseline_path = (
        project_root / "competitors" / "notebooks" / "shepherd_sovereign_main.py"
    )

    if not baseline_path.exists():
        print(f"Error: Baseline not found at {baseline_path}")
        sys.exit(1)

    baseline_source = baseline_path.read_text(encoding="utf-8")

    try:
        candidate_source = create_candidate_source(baseline_source)
    except OverrideError as e:
        print(f"Error creating candidate: {e}")
        sys.exit(1)

    baseline_hash = get_sha256(baseline_source)
    candidate_hash = get_sha256(candidate_source)

    print(f"Baseline SHA256:  {baseline_hash}")
    print(f"Candidate SHA256: {candidate_hash}")

    exclude_seeds = [7, 42, 100, 1234, 2026]
    smoke_seeds = generate_seeds(999, 2, exclude_seeds)
    partial_run_seeds = [
        85969798,
        962560180,
        936831680,
        609656798,
        616064966,
        573057581,
        526730281,
        519030931,
        141810288,
        942954012,
        857558765,
        695136327,
    ]

    rng_seed_used = None
    used_exclusions = []

    if args.seeds:
        if len(set(args.seeds)) != len(args.seeds):
            print("Error: duplicate explicit seeds.")
            sys.exit(1)
        seeds = args.seeds
    elif args.smoke:
        seeds = smoke_seeds
        rng_seed_used = 999
        used_exclusions = exclude_seeds
    else:
        rng_seed_used = 20260924
        used_exclusions = exclude_seeds + smoke_seeds + partial_run_seeds
        seeds = generate_seeds(rng_seed_used, 12, used_exclusions)

    print(f"Running panel with seeds: {seeds}")

    opponents = {
        "The 2950 Peak Farm": project_root
        / "competitors"
        / "notebooks"
        / "peak_2950_main.py",
        "Reyhan Dynamic Route Agent": project_root
        / "competitors"
        / "notebooks"
        / "reyhan_dynamic_router.py",
        "Herd-Safe Race": project_root
        / "competitors"
        / "notebooks"
        / "herd_safe_main.py",
        "V57 Invariant": project_root / "competitors" / "notebooks" / "v57_main.py",
        "Jaxa 2802 Variant B": project_root
        / "competitors"
        / "notebooks"
        / "jaxa_2802_router"
        / "main_variant_b_h24.py",
    }

    if args.smoke:
        first_opp = next(iter(opponents))
        opponents = {first_opp: opponents[first_opp]}

    opp_hashes = {}
    for opp_name, opp_path in opponents.items():
        if not opp_path.exists():
            print(f"Fatal: Opponent not found at {opp_path}")
            sys.exit(1)
        opp_hashes[opp_name] = get_sha256(opp_path.read_text(encoding="utf-8"))

    planned_games = len(seeds) * len(opponents) * 2 * 2
    print(f"Planned games: {planned_games}")

    results = []
    inconclusive_reason = None
    all_ok = True

    for seed in seeds:
        if not all_ok:
            break
        for opp_name, opp_path in opponents.items():
            if not all_ok:
                break
            opp_source = opp_path.read_text(encoding="utf-8")

            for seat in [0, 1]:
                if not all_ok:
                    break
                for arm_name, arm_source in [
                    ("baseline", baseline_source),
                    ("candidate", candidate_source),
                ]:
                    print(
                        f"[{arm_name}] Seed: {seed} | Opp: {opp_name} "
                        f"| Seat: {seat}...",
                        end=" ",
                        flush=True,
                    )

                    env_conf = build_environment_config(seed)
                    start_t = time.time()

                    match_id = uuid.uuid4().hex[:8]
                    arm_mod_name = f"arm_{arm_name}_{match_id}"
                    opp_mod_name = f"opp_{opp_name.replace(' ', '_')}_{match_id}"

                    arm_mod_loaded = False
                    opp_mod_loaded = False

                    try:
                        arm_mod = load_agent_module(
                            arm_source, baseline_path, arm_mod_name
                        )
                        arm_mod_loaded = True
                        opp_mod = load_agent_module(opp_source, opp_path, opp_mod_name)
                        opp_mod_loaded = True

                        arm_agent = getattr(arm_mod, "agent", None)
                        if not callable(arm_agent):
                            raise TypeError(
                                f"Agent attribute in {arm_name} is not callable"
                            )

                        opp_agent = getattr(opp_mod, "agent", None)
                        if not callable(opp_agent):
                            raise TypeError(
                                f"Agent attribute in {opp_name} is not callable"
                            )

                        env = make("kaggriculture", configuration=env_conf)

                        if seat == 0:
                            agents = [arm_agent, opp_agent]
                        else:
                            agents = [opp_agent, arm_agent]

                        _ = env.run(agents)

                        status_0 = env.steps[-1][0]["status"]
                        status_1 = env.steps[-1][1]["status"]

                        reward_0 = env.steps[-1][0]["reward"] or 0
                        reward_1 = env.steps[-1][1]["reward"] or 0

                        info_0 = env.steps[-1][0].get("info")
                        if not isinstance(info_0, dict):
                            info_0 = {}
                        info_1 = env.steps[-1][1].get("info")
                        if not isinstance(info_1, dict):
                            info_1 = {}

                        error_0 = env.steps[-1][0].get("error", "") or info_0.get(
                            "error", ""
                        )
                        error_1 = env.steps[-1][1].get("error", "") or info_1.get(
                            "error", ""
                        )

                        if seat == 0:
                            arm_status, opp_status = status_0, status_1
                            arm_reward, opp_reward = reward_0, reward_1
                            arm_error, opp_error = error_0, error_1
                            arm_telemetry = capture_telemetry(arm_agent, arm_mod)
                            opp_telemetry = capture_telemetry(opp_agent, opp_mod)
                        else:
                            arm_status, opp_status = status_1, status_0
                            arm_reward, opp_reward = reward_1, reward_0
                            arm_error, opp_error = error_1, error_0
                            arm_telemetry = capture_telemetry(arm_agent, arm_mod)
                            opp_telemetry = capture_telemetry(opp_agent, opp_mod)

                    except Exception as e:
                        print(f"ERROR RUN | {0:.1f}s")
                        inconclusive_reason = f"Execution exception: {e}"
                        all_ok = False
                        break
                    finally:
                        if arm_mod_loaded and arm_mod_name in sys.modules:
                            del sys.modules[arm_mod_name]
                        if opp_mod_loaded and opp_mod_name in sys.modules:
                            del sys.modules[opp_mod_name]

                    duration = time.time() - start_t

                    if arm_reward > opp_reward:
                        pts_arm = 1.0
                    elif arm_reward < opp_reward:
                        pts_arm = 0.0
                    else:
                        pts_arm = 0.5

                    res_entry = {
                        "seed": seed,
                        "opponent": opp_name,
                        "opponent_path": str(opp_path),
                        "seat": seat,
                        "arm": arm_name,
                        "status": arm_status,
                        "opp_status": opp_status,
                        "own_cash": arm_reward,
                        "opp_cash": opp_reward,
                        "margin": arm_reward - opp_reward,
                        "match_points": pts_arm,
                        "duration": duration,
                        "error": arm_error,
                        "opp_error": opp_error,
                        "telemetry": arm_telemetry,
                        "opp_telemetry": opp_telemetry,
                    }
                    results.append(res_entry)

                    print(
                        f"{arm_status} | Pts: {res_entry['match_points']} | "
                        f"Mar: {res_entry['margin']} | {duration:.1f}s"
                    )

                    if arm_status != "DONE" or opp_status != "DONE":
                        inconclusive_reason = (
                            f"Match status not DONE (arm: {arm_status}, "
                            f"opp: {opp_status})."
                        )
                        all_ok = False
                        break

                    if arm_error:
                        inconclusive_reason = f"Arm error: {arm_error}"
                        all_ok = False
                        break

                    if opp_error:
                        inconclusive_reason = f"Opp error: {opp_error}"
                        all_ok = False
                        break

                    if has_telemetry_error(arm_telemetry) or has_telemetry_error(
                        opp_telemetry
                    ):
                        inconclusive_reason = "Telemetry error counter > 0."
                        all_ok = False
                        break

    if all_ok:
        try:
            agg = aggregate_results(results)
        except AggregationError as e:
            inconclusive_reason = f"Aggregation failed: {e}"
            all_ok = False
            agg = {}
    else:
        agg = {}

    output_data = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine_version": engine_version,
        "hashes": {"baseline": baseline_hash, "candidate": candidate_hash},
        "patch": {
            "target": "V9_RACE_DEFAULT = 40",
            "replacement": "V9_RACE_DEFAULT = 41",
        },
        "rng_seed": rng_seed_used,
        "excluded_seeds": used_exclusions,
        "seeds": seeds,
        "opponents": list(opponents.keys()),
        "opponent_paths": {k: str(v) for k, v in opponents.items()},
        "opponent_hashes": opp_hashes,
        "all_games_completed_successfully": all_ok,
        "inconclusive_reason": inconclusive_reason,
        "aggregates": agg,
        "raw_games": results,
    }

    out_path_str = args.output
    if not out_path_str:
        if args.smoke:
            out_path_str = "docs/experiments/race_horizon_41_smoke.json"
        else:
            out_path_str = "docs/experiments/race_horizon_41.json"

    out_path = Path(out_path_str)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
    print(f"\nResults saved to {out_path}")

    if not all_ok:
        print(f"\nWARNING: Experiment INCONCLUSIVE. Reason: {inconclusive_reason}")
    else:
        print("\nExperiment completed successfully.")


if __name__ == "__main__":
    main()
