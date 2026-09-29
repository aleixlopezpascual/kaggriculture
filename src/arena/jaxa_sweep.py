"""Systematic Parameter Sweep for Jaxa 2802 Elo Router."""

import importlib.util
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.arena.run_tournament import run_single_match


def load_swept_jaxa(lookahead: int, horizon: int, open_units: int):
    """Dynamically loads Jaxa 2802 with modified parameters in a isolated
    module namespace."""
    path = PROJECT_ROOT / "competitors" / "notebooks" / "jaxa_2802_router" / "main.py"

    with path.open(encoding="utf-8") as f:
        code = f.read()

    # Dynamically inject/replace parameters
    code = code.replace("LOOKAHEAD = 2", f"LOOKAHEAD = {lookahead}")
    code = code.replace("HORIZON = 24", f"HORIZON = {horizon}")
    code = code.replace("OPEN_UNITS = 10", f"OPEN_UNITS = {open_units}")

    # Create isolated module
    spec = importlib.util.spec_from_loader("jaxa_swept", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(code, module.__dict__)

    return module.agent


def evaluate_config(lookahead: int, horizon: int, open_units: int, seeds: list):
    """Evaluates a specific parameter configuration against Heuristic v2."""
    jaxa_fn = load_swept_jaxa(lookahead, horizon, open_units)

    # Register agents under run_tournament's namespace temporarily
    from src.arena import run_tournament

    # We override Jaxa 2802 Elo Router temporarily in get_agent_callable map
    orig_get_agent = run_tournament.get_agent_callable

    def mock_get_agent(name):
        if name == "Jaxa 2802 Elo Router":
            return jaxa_fn
        elif name == "Heuristic v2 (Escalation)":
            return orig_get_agent("Heuristic v2 (Escalation)")
        return orig_get_agent(name)

    run_tournament.get_agent_callable = mock_get_agent

    # Setup H2H
    match_tasks = []
    for seed in seeds:
        match_tasks.append((seed, "Jaxa 2802 Elo Router", "Heuristic v2 (Escalation)"))
        match_tasks.append((seed, "Heuristic v2 (Escalation)", "Jaxa 2802 Elo Router"))

    results = []
    for seed, a0, a1 in match_tasks:
        res = run_single_match(seed, a0, a1)
        if res["success"]:
            results.append(res)

    # Restore original mapping
    run_tournament.get_agent_callable = orig_get_agent

    # Aggregate statistics
    jaxa_gold = 0.0
    for res in results:
        if res["agent_0"] == "Jaxa 2802 Elo Router":
            jaxa_gold += res["gold_0"]
        else:
            jaxa_gold += res["gold_1"]

    avg_gold = jaxa_gold / max(1, len(results))
    return avg_gold


def main():
    print("=" * 70)
    print("           JAXA 2802 PARAMETER SWEEP OPTIMIZER")
    print("=" * 70)

    seeds = [42, 100, 2026]

    # Parameter Search Grid (Round 7)
    grid = [
        (2, 24, 10),  # Baseline
        (1, 1, 10),  # Round 6 Winner
        (1, 1, 8),  # Horizon=1 with open_units=8
        (1, 1, 12),  # Horizon=1 with open_units=12
    ]

    results = []

    for lookahead, horizon, open_units in grid:
        print(
            f"Testing Config: LOOKAHEAD={lookahead:1d} | "
            f"HORIZON={horizon:2d} | OPEN_UNITS={open_units:2d}...",
            end="",
            flush=True,
        )
        start = time.time()
        avg_gold = evaluate_config(lookahead, horizon, open_units, seeds)
        duration = time.time() - start
        results.append((avg_gold, (lookahead, horizon, open_units)))
        print(f" DONE | Avg Gold scored: ${avg_gold:10,.2f} ({duration:.1f}s)")

    print("=" * 70)
    print("                             SUMMARY STANDINGS")
    print("-" * 70)
    for rank, (gold, params) in enumerate(
        sorted(results, reverse=True, key=lambda x: x[0]), 1
    ):
        lookahead, horizon, open_units = params
        baseline_str = " [BASELINE]" if params == (2, 24, 10) else ""
        print(
            f"Rank {rank:2d} | Avg Gold: ${gold:10,.2f} | "
            f"LOOKAHEAD={lookahead:1d}, HORIZON={horizon:2d}, "
            f"OPEN_UNITS={open_units:2d}{baseline_str}"
        )
    print("=" * 70)


if __name__ == "__main__":
    main()
