#!/usr/bin/env python3
"""Monotonic latency and margin evaluator for P3 Metered Challenger vs DECEM seed."""

import json
import subprocess
import sys
from pathlib import Path


def _run_isolated_match(agent0: str, agent1: str, seed: int) -> dict:
    code = f"""
import json, time, kaggle_environments

env = kaggle_environments.make("kaggriculture", configuration={{"seed": {seed}}})
t0 = time.perf_counter()
steps = env.run(["{agent0}", "{agent1}"])
elapsed = time.perf_counter() - t0

r0 = steps[-1][0]["reward"]
r1 = steps[-1][1]["reward"]
s0 = steps[-1][0]["status"]
s1 = steps[-1][1]["status"]

out = {{"reward0": r0, "reward1": r1, "status0": s0, "status1": s1, "elapsed": elapsed}}
print(json.dumps(out))
"""
    raw = subprocess.check_output([sys.executable, "-c", code]).decode().strip()
    return json.loads(raw)


def evaluate_p3_on_decem_seed():
    seed = 848617604
    p2_path = str(Path("submission/prvsiyan_v2_package/main.py").resolve())
    p3_path = str(Path("src/agents/p3_metered_challenger.py").resolve())
    decem_path = str(
        Path(
            "docs/experiments/agent_selection/decem_evaluation/decem_tape_agent.py"
        ).resolve()
    )

    print(f"=== Benchmarking P3 vs DECEM Tape on Seed {seed} ===")

    # Run P2 V2 baseline
    res_p2 = _run_isolated_match(p2_path, decem_path, seed)
    r_p2 = res_p2["reward0"]
    d_p2 = res_p2["reward1"]
    time_p2 = res_p2["elapsed"]

    # Run P3 Metered
    res_p3 = _run_isolated_match(p3_path, decem_path, seed)
    r_p3 = res_p3["reward0"]
    d_p3 = res_p3["reward1"]
    time_p3 = res_p3["elapsed"]

    m_p2 = r_p2 - d_p2
    m_p3 = r_p3 - d_p3
    print(
        f"P2 V2 Baseline: Reward ${r_p2:,.0f} vs DECEM ${d_p2:,.0f} | "
        f"Margin: {m_p2:+,.0f} | Time: {time_p2:.2f}s"
    )
    print(
        f"P3 Metered:     Reward ${r_p3:,.0f} vs DECEM ${d_p3:,.0f} | "
        f"Margin: {m_p3:+,.0f} | Time: {time_p3:.2f}s"
    )
    print(f"P3 vs P2 Delta: {r_p3 - r_p2:+,.0f} gold")


if __name__ == "__main__":
    evaluate_p3_on_decem_seed()
