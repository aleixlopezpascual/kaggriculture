"""Quick Sequential Head-to-Head Evaluator for Kaggriculture."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.arena.run_tournament import run_single_match


def run_h2h(agent_a, agent_b, seeds):
    print("=" * 70)
    print(f"   SEQUENTIAL HEAD-TO-HEAD: {agent_a} vs {agent_b}")
    print("=" * 70)

    match_tasks = []
    # Both seat configurations for each seed
    for seed in seeds:
        match_tasks.append((seed, agent_a, agent_b))
        match_tasks.append((seed, agent_b, agent_a))

    results = []
    start_time = time.time()

    # Run matches sequentially to prevent standard stream redirection conflicts
    for i, (seed, a0, a1) in enumerate(match_tasks, 1):
        print(
            f"[{i}/{len(match_tasks)}] Running: Seed {seed} | {a0} vs {a1}...",
            end="",
            flush=True,
        )
        res = run_single_match(seed, a0, a1)
        results.append(res)
        if res["success"]:
            winner_str = f"Winner: {res['winner']}" if res["winner"] != "Tie" else "Tie"
            print(
                f"\r[{i}/{len(match_tasks)}] Match Seed {seed:5d} | "
                f"{a0:25s} vs {a1:25s} | "
                f"Gold: {res['gold_0']:10,.0f} vs {res['gold_1']:10,.0f} | "
                f"{winner_str} ({res['duration']:.1f}s)"
            )
        else:
            print(
                f"\r[{i}/{len(match_tasks)}] Match Seed {seed:5d} | "
                f"{a0:25s} vs {a1:25s} | FAILED: "
                f"{res['error'].splitlines()[0] if res['error'] else 'Unknown Error'}"
            )

    duration = time.time() - start_time
    print(f"Completed {len(match_tasks)} matches in {duration:.2f} seconds.")
    print("-" * 70)

    # Statistics
    stats = {
        agent_a: {"wins": 0, "losses": 0, "ties": 0, "gold": 0.0},
        agent_b: {"wins": 0, "losses": 0, "ties": 0, "gold": 0.0},
    }

    for res in sorted(results, key=lambda x: (x["seed"], x["agent_0"])):
        if not res["success"]:
            continue

        a0, a1 = res["agent_0"], res["agent_1"]
        g0, g1 = res["gold_0"], res["gold_1"]
        winner = res["winner"]

        stats[a0]["gold"] += g0
        stats[a1]["gold"] += g1

        if winner == a0:
            stats[a0]["wins"] += 1
            stats[a1]["losses"] += 1
        elif winner == a1:
            stats[a1]["wins"] += 1
            stats[a0]["losses"] += 1
        else:
            stats[a0]["ties"] += 1
            stats[a1]["ties"] += 1

    print("=" * 70)
    print("                           SUMMARY STATISTICS")
    print("-" * 70)
    for agent in [agent_a, agent_b]:
        s = stats[agent]
        total_matches = s["wins"] + s["losses"] + s["ties"]
        avg_gold = s["gold"] / max(1, total_matches)
        win_pct = (s["wins"] / max(1, total_matches)) * 100
        print(
            f"{agent:30s} | Wins: {s['wins']} | "
            f"Losses: {s['losses']} | Ties: {s['ties']} | "
            f"Win %: {win_pct:5.1f}% | Avg Gold: {avg_gold:12,.0f}"
        )
    print("=" * 70)


if __name__ == "__main__":
    # Let's run a concise set of 3 seeds first to keep execution fast and clean
    seeds = [42, 100, 2026]
    run_h2h("Heuristic v2 (Escalation)", "Jaxa 2802 Elo Router", seeds)
