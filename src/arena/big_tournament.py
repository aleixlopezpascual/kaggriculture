"""Large-Scale Local Tournament Runner.

SOTA Public Meta Benchmark (September 23, 2026).
"""

import importlib.util
import json
import sys
import time
from pathlib import Path

from kaggle_environments import make

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

KAGGLE_ELO_MAP = {
    "The 2950 Peak Farm": "2950+ Verified SOTA (v13+Pipe16)",
    "Shepherd Sovereign": "2900+ Frontier (Sept 23 Release)",
    "Thomas 2945 Farm": "2944.7 Official Live Elo (v9/4)",
    "Herd-Safe Race": "Top Benchmark (COURIER + HERD2)",
    "V57 Invariant": "280-0 Order-Book Invariant",
    "Jaxa 2802 Variant B": "1816.5 Live Elo (Peaked 2008.2)",
}

CANDIDATES = {
    "The 2950 Peak Farm": "competitors/notebooks/peak_2950_main.py",
    "Shepherd Sovereign": "competitors/notebooks/shepherd_sovereign_main.py",
    "Thomas 2945 Farm": "competitors/notebooks/thomas_2945_main.py",
    "Herd-Safe Race": "competitors/notebooks/herd_safe_main.py",
    "V57 Invariant": "competitors/notebooks/v57_main.py",
    "Jaxa 2802 Variant B": (
        "competitors/notebooks/jaxa_2802_router/main_variant_b_h24.py"
    ),
}


def load_agent_fn(rel_path: str):
    path = PROJECT_ROOT / rel_path
    module_dir = str(path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    module_name = path.stem + "_" + str(int(time.time() * 1000) % 100000)
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def run_match(seed: int, name_0: str, name_1: str, turns: int = 720):
    start_t = time.time()
    try:
        fn_0 = load_agent_fn(CANDIDATES[name_0])
        fn_1 = load_agent_fn(CANDIDATES[name_1])

        env = make("kaggriculture", configuration={"episodeSteps": turns, "seed": seed})
        env.run([fn_0, fn_1])

        g0 = float(env.state[0].reward if env.state[0].reward is not None else 0.0)
        g1 = float(env.state[1].reward if env.state[1].reward is not None else 0.0)

        winner = name_0 if g0 > g1 else (name_1 if g1 > g0 else "Tie")
        return {
            "seed": seed,
            "agent_0": name_0,
            "agent_1": name_1,
            "gold_0": g0,
            "gold_1": g1,
            "winner": winner,
            "duration": time.time() - start_t,
            "success": True,
            "error": None,
        }
    except Exception as e:
        return {
            "seed": seed,
            "agent_0": name_0,
            "agent_1": name_1,
            "gold_0": 0.0,
            "gold_1": 0.0,
            "winner": "Error",
            "duration": time.time() - start_t,
            "success": False,
            "error": str(e),
        }


def main():
    print("=" * 80)
    print("      KAGGRICULTURE SOTA PUBLIC META TOURNAMENT (SEPTEMBER 23, 2026)")
    print("=" * 80)

    agent_names = list(CANDIDATES.keys())
    seeds = [42, 100, 2026]

    matches = []
    for s in seeds:
        for i, a0 in enumerate(agent_names):
            for j, a1 in enumerate(agent_names):
                if i != j:
                    matches.append((s, a0, a1))

    total_matches = len(matches)
    print(f"Candidates ({len(agent_names)}): {', '.join(agent_names)}")
    print(f"Seeds ({len(seeds)}):      {seeds}")
    print(f"Total Matches:    {total_matches} (both seats across all seeds)")
    print("-" * 80)

    results = []
    t0 = time.time()

    for idx, (seed, a0, a1) in enumerate(matches, 1):
        res = run_match(seed, a0, a1)
        results.append(res)
        w_tag = f"Winner: {res['winner']}" if res["winner"] != "Tie" else "TIE"
        print(
            f"[{idx:2d}/{total_matches}] Seed {seed:4d} | "
            f"{a0[:18]:18s} vs {a1[:18]:18s} | "
            f"Gold: {res['gold_0']:10,.0f} vs {res['gold_1']:10,.0f} | "
            f"{w_tag} ({res['duration']:.2f}s)"
        )

    elapsed = time.time() - t0
    print("-" * 80)
    print(
        f"Tournament completed in {elapsed:.1f}s "
        f"({elapsed/total_matches:.2f}s per match)."
    )
    print("=" * 80)

    stats = {
        name: {
            "matches": 0,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "gold_scored": 0.0,
            "gold_conceded": 0.0,
        }
        for name in agent_names
    }

    head_to_head = {
        a0: {a1: {"W": 0, "L": 0, "T": 0} for a1 in agent_names if a0 != a1}
        for a0 in agent_names
    }

    for r in results:
        if not r["success"]:
            continue
        a0, a1 = r["agent_0"], r["agent_1"]
        g0, g1 = r["gold_0"], r["gold_1"]

        stats[a0]["matches"] += 1
        stats[a1]["matches"] += 1
        stats[a0]["gold_scored"] += g0
        stats[a0]["gold_conceded"] += g1
        stats[a1]["gold_scored"] += g1
        stats[a1]["gold_conceded"] += g0

        if r["winner"] == a0:
            stats[a0]["wins"] += 1
            stats[a1]["losses"] += 1
            head_to_head[a0][a1]["W"] += 1
            head_to_head[a1][a0]["L"] += 1
        elif r["winner"] == a1:
            stats[a1]["wins"] += 1
            stats[a0]["losses"] += 1
            head_to_head[a1][a0]["W"] += 1
            head_to_head[a0][a1]["L"] += 1
        else:
            stats[a0]["ties"] += 1
            stats[a1]["ties"] += 1
            head_to_head[a0][a1]["T"] += 1
            head_to_head[a1][a0]["T"] += 1

    print("\n" + " " * 22 + "FINAL SOTA TOURNAMENT STANDINGS")
    print("-" * 115)
    print(
        f"{'Agent Name':22s} | {'Wins':4s} | {'Loss':4s} | "
        f"{'Tie':3s} | {'Win Rate':8s} | "
        f"{'Local Avg Gold':14s} | {'Avg Margin':11s} | {'Kaggle Public Benchmark':25s}"
    )
    print("-" * 115)

    ranked_agents = sorted(
        agent_names,
        key=lambda x: (
            stats[x]["wins"] / max(1, stats[x]["matches"]),
            (stats[x]["gold_scored"] - stats[x]["gold_conceded"])
            / max(1, stats[x]["matches"]),
        ),
        reverse=True,
    )

    summary_rows = []
    for rank, name in enumerate(ranked_agents, 1):
        s = stats[name]
        m = max(1, s["matches"])
        win_rate = (s["wins"] / m) * 100.0
        avg_gold = s["gold_scored"] / m
        avg_margin = (s["gold_scored"] - s["gold_conceded"]) / m
        lb_elo = KAGGLE_ELO_MAP.get(name, "N/A")

        summary_rows.append(
            {
                "rank": rank,
                "agent": name,
                "wins": s["wins"],
                "losses": s["losses"],
                "ties": s["ties"],
                "win_rate": round(win_rate, 1),
                "avg_gold": round(avg_gold, 1),
                "avg_margin": round(avg_margin, 1),
                "benchmark_elo": lb_elo,
            }
        )

        print(
            f"{name:22s} | {s['wins']:4d} | {s['losses']:4d} | "
            f"{s['ties']:3d} | {win_rate:7.1f}% | "
            f"${avg_gold:13,.0f} | {avg_margin:+11,.0f} | {lb_elo:25s}"
        )
    print("-" * 115)

    output_path = PROJECT_ROOT / "docs" / "sota_tournament_results_2026_09_23.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "matches_count": total_matches,
                "seeds": seeds,
                "standings": summary_rows,
                "head_to_head": head_to_head,
            },
            f,
            indent=2,
        )
    print(f"\nDetailed SOTA tournament results saved to: {output_path}")


if __name__ == "__main__":
    main()
