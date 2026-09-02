"""Kaggriculture parallel self-play simulation coordinator."""

import concurrent.futures
from src.agents.base import BaseAgent
from src.arena.evaluator import LocalArena


def run_parallel_simulations(
    agent: BaseAgent, seeds: list[int], max_workers: int = 4
) -> dict[str, float]:
    """Runs local benchmarking matches in parallel across a worker pool."""
    arena = LocalArena(agent)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(arena.run_match, seed): seed for seed in seeds}
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return {
        "avg_gold": sum(results) / len(results),
        "max_gold": max(results),
        "min_gold": min(results),
        "runs": len(results),
    }
