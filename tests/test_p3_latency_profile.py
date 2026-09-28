import time

import kaggle_environments

from src.agents.p3_metered_challenger import agent


def test_p3_latency_stays_under_100ms():
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
    env.reset()
    latencies: list[float] = []

    for _ in range(100):
        obs = env.state[0]["observation"]
        t0 = time.perf_counter()
        act = agent(obs)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed)
        env.step([act, {"farmer": ["PASS"], "market": []}])
        if env.done:
            break

    max_latency = max(latencies)
    mean_latency = sum(latencies) / len(latencies)
    assert max_latency < 100.0, f"Max latency exceeded guideline: {max_latency:.2f}ms"
    assert mean_latency < 10.0, f"Mean latency unexpectedly high: {mean_latency:.2f}ms"
