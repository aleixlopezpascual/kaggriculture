#!/usr/bin/env python3
"""Run multi-seed confirmation tournament for Prvsiyan V3 (with Lot Metering).

Evaluates V3 against V2 (A/B), Shepherd Sovereign, and DECEM across 8 fresh
seeds
in both Seat 0 and Seat 1 with process-isolated execution.
"""

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

CONFIRMATION_SEEDS = [
    838084248,
    690003990,
    400914000,
    839524396,
    946313351,
    911995953,
    996328792,
    134302223,
]


def _run_single_match(task: tuple) -> dict:
    match_id, agent0, agent1, seed, name0, name1 = task
    code = f"""
import json, time, kaggle_environments

env = kaggle_environments.make("kaggriculture", configuration={{"seed": {seed}}})
t0 = time.perf_counter()
steps = env.run(["{agent0}", "{agent1}"])
elapsed = (time.perf_counter() - t0) * 1000.0

r0 = float(steps[-1][0]["reward"])
r1 = float(steps[-1][1]["reward"])
s0 = str(steps[-1][0]["status"])
s1 = str(steps[-1][1]["status"])

out = {{
    "reward0": r0, "reward1": r1,
    "status0": s0, "status1": s1,
    "elapsed_ms": elapsed
}}
print(json.dumps(out))
"""
    try:
        raw = (
            subprocess.check_output([sys.executable, "-c", code])
            .decode()
            .strip()
        )
        res = json.loads(raw)
        return {
            "match_id": match_id,
            "seed": seed,
            "agent0_name": name0,
            "agent1_name": name1,
            "reward0": res["reward0"],
            "reward1": res["reward1"],
            "status0": res["status0"],
            "status1": res["status1"],
            "elapsed_ms": res["elapsed_ms"],
        }
    except Exception as e:
        return {
            "match_id": match_id,
            "seed": seed,
            "agent0_name": name0,
            "agent1_name": name1,
            "error": str(e),
            "reward0": 0.0,
            "reward1": 0.0,
            "status0": "ERROR",
            "status1": "ERROR",
            "elapsed_ms": 0.0,
        }


def main():
    v3_path = str(Path("submission/prvsiyan_v3_package/main.py").resolve())
    v2_path = str(Path("submission/prvsiyan_v2_package/main.py").resolve())
    shep_path = str(
        Path("competitors/notebooks/shepherd_sovereign_main.py").resolve()
    )
    decem_path = str(
        Path(
            "docs/experiments/agent_selection/decem_evaluation/decem_tape_agent.py"
        ).resolve()
    )

    opponents = [
        ("Prvsiyan_V2", v2_path),
        ("Shepherd_Sovereign", shep_path),
        ("DECEM_Replay", decem_path),
    ]

    tasks = []
    match_counter = 0

    for opp_name, opp_path in opponents:
        for seed in CONFIRMATION_SEEDS:
            # Seat 0: V3 as Player 0
            tasks.append((
                match_counter,
                v3_path,
                opp_path,
                seed,
                "Prvsiyan_V3",
                opp_name,
            ))
            match_counter += 1

            # Seat 1: V3 as Player 1
            tasks.append((
                match_counter,
                opp_path,
                v3_path,
                seed,
                opp_name,
                "Prvsiyan_V3",
            ))
            match_counter += 1

    n_seeds = len(CONFIRMATION_SEEDS)
    print(f"=== Starting V3 Tournament: {len(tasks)} matches ({n_seeds} seeds) ===")
    start_time = time.time()

    results = []
    workers = min(6, os.cpu_count() or 4)
    print(f"Executing with {workers} parallel worker processes...")

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_run_single_match, t): t for t in tasks}
        for completed, f in enumerate(as_completed(futures), start=1):
            res = f.result()
            results.append(res)
            if completed % 8 == 0 or completed == len(tasks):
                pct = completed * 100 / len(tasks)
                print(f"  [{completed}/{len(tasks)}] finished ({pct:.1f}%)")

    total_time = time.time() - start_time
    print(f"\nTournament completed in {total_time:.2f} seconds.")

    # Aggregate by opponent
    by_opp = {}
    for opp_name, _ in opponents:
        by_opp[opp_name] = {
            "v3_wins": 0,
            "v3_losses": 0,
            "ties": 0,
            "v3_total_gold": 0.0,
            "opp_total_gold": 0.0,
            "v3_margins": [],
            "matches": 0,
        }

    for r in results:
        is_p0 = r["agent0_name"] == "Prvsiyan_V3"
        opp_name = r["agent1_name"] if is_p0 else r["agent0_name"]
        v3_reward = r["reward0"] if is_p0 else r["reward1"]
        opp_reward = r["reward1"] if is_p0 else r["reward0"]

        entry = by_opp[opp_name]
        entry["matches"] += 1
        entry["v3_total_gold"] += v3_reward
        entry["opp_total_gold"] += opp_reward
        margin = v3_reward - opp_reward
        entry["v3_margins"].append(margin)

        if margin > 0:
            entry["v3_wins"] += 1
        elif margin < 0:
            entry["v3_losses"] += 1
        else:
            entry["ties"] += 1

    print("\n" + "=" * 70)
    print("                     PRVSIYAN V3 TOURNAMENT SUMMARY")
    print("=" * 70)
    for opp_name, stats in by_opp.items():
        n = stats["matches"]
        w = stats["v3_wins"]
        losses = stats["v3_losses"]
        ties = stats["ties"]
        wr = (w + 0.5 * ties) / n * 100.0 if n else 0.0
        v3_avg = stats["v3_total_gold"] / n if n else 0.0
        opp_avg = stats["opp_total_gold"] / n if n else 0.0
        avg_m = (
            sum(stats["v3_margins"]) / len(stats["v3_margins"])
            if stats["v3_margins"]
            else 0.0
        )
        print(f"Opponent: {opp_name:18s} | Matches: {n:2d}")
        print(
            f"  Record: {w:2d}W - {losses:2d}L - {ties:2d}T | Points Rate: {wr:5.1f}%"
        )
        print(
            f"  V3 Avg: ${v3_avg:9,.0f} | Opp Avg: ${opp_avg:9,.0f} | "
            f"Avg Margin: {avg_m:+9,.0f}"
        )
        print("-" * 70)

    # Save summary
    out_dir = Path("docs/experiments/agent_selection/p3_v3_lot_metering")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "confirmation_summary.json"

    with summary_path.open("w", encoding="utf-8") as fp:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "total_matches": len(results),
                "total_duration_sec": total_time,
                "seeds": CONFIRMATION_SEEDS,
                "opponents_summary": by_opp,
                "matches": results,
            },
            fp,
            indent=2,
        )

    print(f"Detailed confirmation telemetry saved to: {summary_path}")


if __name__ == "__main__":
    main()
