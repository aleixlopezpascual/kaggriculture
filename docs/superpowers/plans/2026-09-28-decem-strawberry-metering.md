# DECEM Strawberry Lot Metering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement disciplined commodity lot metering for high-elasticity crops (primarily Strawberry) to eliminate price-crash sell dumps, capturing DECEM's +$5,700 premium pricing advantage while strictly preserving room-guard safety and latency limits.

**Architecture:** A lightweight, non-intrusive market filter (`StrawberryLotMeter`) integrated into our verified P2 V2 optimizer pipeline. When sell orders for elastic crops exceed the town's single-cycle absorption capacity, the filter caps the lot size to 2–6 units unless near shed capacity ($\ge 90$) or at terminal liquidation ($\ge 718$), keeping market quotes elevated above $85–$120.

**Tech Stack:** Python 3.10+, `kaggle-environments 1.32.7`, `pytest`, monotonic timing profiling (`time.perf_counter()`).

**Spec:** [`docs/decem_world_2_playbook.md`](../decem_world_2_playbook.md) and [`docs/competitor_notebooks_analysis.md`](../competitor_notebooks_analysis.md).

## Global Constraints

- **Latency Budget:** Monotonic callback latency must remain strictly under 100 ms (`GEMINI.md`).
- **Shed Safety (Room-Guard Invariant):** Never meter sales if total shed stock $\ge 90$ units or on terminal step $\ge 718$, preventing inventory overflow destruction.
- **Order Preservation:** Fixed non-SELL market orders (`HIRE`, `BUY_SEED`, `BUY_ANIMAL`, `BUY_LAND`) must remain strictly untouched and preserved in their relative slots.
- **Immutability:** Game observations and state objects must remain completely immutable (`frozen=True`).
- **No Unprompted Submissions:** No Kaggle upload or live deployment without explicit prior user authorization.

## Review Focus

1. **Terminal Liquidation Exemption:** Step $\ge 718$ must bypass metering and liquidate 100% of shed inventory without capping.
2. **Room-Guard Overflow Protection:** Total shed stock $\ge 90$ must bypass metering to guarantee zero lost harvests due to shed capacity.
3. **Non-Target Crop Invariance:** Sales of Wheat, Carrot, Milk, Wool, and Fertilizer must not be altered by the strawberry metering logic.
4. **Order Quantity Integrity:** Metered order quantity must be a positive integer $\ge 1$; empty or zero-quantity orders must not be emitted.
5. **Slot Ordering Parity:** The P2 V2 market slot optimizer must execute smoothly on top of metered orders without crashing or introducing latency spikes.

---

### Task 1: Core Commodity Lot Metering Logic and Unit Tests

**Files:**
- Create: `src/utils/commodity_lot_meter.py`
- Create: `tests/test_commodity_lot_meter.py`

**Interfaces:**
- Consumes: `observation: dict[str, Any]`, `orders: list[list[Any]]`
- Produces: `meter_sell_orders(observation: dict[str, Any], orders: list[list[Any]], max_strawberry_lot: int = 6) -> list[list[Any]]`

- [ ] **Step 1: Write the failing unit tests for `commodity_lot_meter`**

```python
# tests/test_commodity_lot_meter.py
from typing import Any
import pytest
from src/utils.commodity_lot_meter import meter_sell_orders


def test_metering_caps_strawberry_sales():
    obs: dict[str, Any] = {
        "step": 300,
        "private": {"shed": {"STRAWBERRY": 20, "WHEAT": 10}},
        "town": {"unlocked_shops": ["ICE_CREAM_SHOP"]},
    }
    orders = [["SELL", "STRAWBERRY", 16], ["SELL", "WHEAT", 10]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=6)
    assert metered[0] == ["SELL", "STRAWBERRY", 6]
    assert metered[1] == ["SELL", "WHEAT", 10]


def test_metering_bypassed_at_terminal_step():
    obs: dict[str, Any] = {
        "step": 718,
        "private": {"shed": {"STRAWBERRY": 20}},
        "town": {"unlocked_shops": []},
    }
    orders = [["SELL", "STRAWBERRY", 20]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=6)
    assert metered[0] == ["SELL", "STRAWBERRY", 20]


def test_metering_bypassed_when_shed_nearly_full():
    obs: dict[str, Any] = {
        "step": 400,
        "private": {"shed": {"STRAWBERRY": 50, "WHEAT": 42}},
        "town": {"unlocked_shops": []},
    }
    orders = [["SELL", "STRAWBERRY", 16]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=6)
    assert metered[0] == ["SELL", "STRAWBERRY", 16]


def test_metering_preserves_non_sell_orders():
    obs: dict[str, Any] = {
        "step": 200,
        "private": {"shed": {"STRAWBERRY": 10}},
        "town": {"unlocked_shops": []},
    }
    orders = [["HIRE"], ["BUY_LAND"], ["SELL", "STRAWBERRY", 12]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=4)
    assert metered == [["HIRE"], ["BUY_LAND"], ["SELL", "STRAWBERRY", 4]]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_commodity_lot_meter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.utils.commodity_lot_meter'`

- [ ] **Step 3: Implement minimal code for `commodity_lot_meter.py`**

```python
# src/utils/commodity_lot_meter.py
from __future__ import annotations

from typing import Any

_SHED_CAPACITY_EMERGENCY_THRESHOLD = 90
_TERMINAL_ACT_STEP = 718


def meter_sell_orders(
    observation: dict[str, Any],
    orders: list[list[Any]],
    max_strawberry_lot: int = 6,
) -> list[list[Any]]:
    """Meter high-elasticity crop sales (e.g.

    Strawberry) into absorption-sized lots unless near capacity or at match
    end.
    """
    if not orders:
        return orders

    step = int(observation.get("step", 0))
    if "step" not in observation:
        day = int(observation.get("day", 0))
        hour = int(observation.get("hour", 0))
        step = day * 24 + hour

    # 1. Terminal liquidation guard: always liquidate everything at match end
    if step >= _TERMINAL_ACT_STEP:
        return [list(o) if isinstance(o, (list, tuple)) else o for o in orders]

    # 2. Shed capacity emergency guard: if shed >= 90% full, do not restrict sales
    private = observation.get("private", {})
    shed = private.get("shed", {})
    total_shed = sum(int(v) for v in shed.values())
    if total_shed >= _SHED_CAPACITY_EMERGENCY_THRESHOLD:
        return [list(o) if isinstance(o, (list, tuple)) else o for o in orders]

    # 3. Dynamic lot sizing: count active strawberry-consuming shops
    shops = observation.get("town", {}).get("unlocked_shops", [])
    strawberry_shops = shops.count("ICE_CREAM_SHOP") + shops.count(
        "SMOOTHIE_SHOP"
    )
    effective_cap = (
        max_strawberry_lot if strawberry_shops >= 1 else max(2, max_strawberry_lot - 2)
    )

    out_orders: list[list[Any]] = []
    for order in orders:
        if not isinstance(order, (list, tuple)) or not order:
            out_orders.append(order)
            continue

        op = order[0]
        if op == "SELL" and len(order) >= 3 and order[1] == "STRAWBERRY":
            qty = int(order[2])
            metered_qty = min(qty, effective_cap)
            if metered_qty > 0:
                out_orders.append(["SELL", "STRAWBERRY", metered_qty])
        else:
            out_orders.append(list(order))

    return out_orders
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_commodity_lot_meter.py -v`
Expected: PASS (4/4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/utils/commodity_lot_meter.py tests/test_commodity_lot_meter.py
git commit -m "feat(market): implement commodity lot metering with room-guard safety"
```

---

### Task 2: Integrate Metering Layer with P2 V2 Candidate Wrapper

**Files:**
- Create: `src/agents/p3_metered_challenger.py`
- Create: `tests/test_p3_metered_challenger.py`

**Interfaces:**
- Consumes: `p2_v2_agent`, `meter_sell_orders`
- Produces: `agent(observation: dict[str, Any], configuration: Any = None) -> dict[str, Any]`

- [ ] **Step 1: Write integration test for P3 metered challenger**

```python
# tests/test_p3_metered_challenger.py
from pathlib import Path
import kaggle_environments
import pytest
from src.agents.p3_metered_challenger import agent


def test_p3_metered_challenger_execution_step():
    obs = {
        "step": 360,
        "player": 0,
        "farms": [
            {
                "money": 10000.0,
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
                "tiles": [[None] * 10 for _ in range(10)],
                "farmer": [4, 4],
            },
            {
                "money": 10000.0,
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
                "tiles": [[None] * 10 for _ in range(10)],
                "farmer": [4, 4],
            },
        ],
        "private": {"shed": {"STRAWBERRY": 25, "WHEAT": 5}},
        "market": {"inventory": {}, "prices": {"STRAWBERRY": 110, "WHEAT": 25}},
        "town": {"unlocked_shops": ["ICE_CREAM_SHOP"]},
    }
    act = agent(obs)
    assert "market" in act
    # Strawberry sell orders must not exceed effective cap (6)
    for o in act["market"]:
        if len(o) >= 3 and o[0] == "SELL" and o[1] == "STRAWBERRY":
            assert int(o[2]) <= 6


def test_p3_metered_challenger_full_game_simulation():
    env = kaggle_environments.make(
        "kaggriculture", configuration={"seed": 848617604}
    )
    p3_path = str(Path("src/agents/p3_metered_challenger.py").resolve())
    shep_path = "competitors/notebooks/shepherd_sovereign_main.py"
    steps = env.run([p3_path, shep_path])
    assert len(steps) == 720
    assert steps[-1][0]["status"] == "DONE"
    assert steps[-1][0]["reward"] > 50000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_p3_metered_challenger.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.agents.p3_metered_challenger'`

- [ ] **Step 3: Implement `src/agents/p3_metered_challenger.py`**

```python
# src/agents/p3_metered_challenger.py
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_DIR = Path(__file__).resolve().parent
_PKG_DIR = _DIR.parent.parent / "submission" / "prvsiyan_v2_package"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import main as _p2_v2_module

from src.utils.commodity_lot_meter import meter_sell_orders


def agent(
    observation: dict[str, Any], configuration: Any = None
) -> dict[str, Any]:
    # 1. Run verified P2 V2 optimizer
    raw_action = _p2_v2_module.agent(observation, configuration)

    # 2. Apply disciplined commodity lot metering
    market_orders = raw_action.get("market") or []
    metered_market = meter_sell_orders(
        observation, market_orders, max_strawberry_lot=6
    )

    return dict(raw_action, market=metered_market)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_p3_metered_challenger.py -v`
Expected: PASS (2/2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/agents/p3_metered_challenger.py tests/test_p3_metered_challenger.py
git commit -m "feat(agent): assemble P3 metered challenger integrating P2 V2 and lot metering"
```

---

### Task 3: Monotonic Latency Profiling and Head-to-Head Benchmark on Seed 848617604

**Files:**
- Create: `scripts/profile_p3_metered.py`
- Create: `tests/test_p3_latency_profile.py`

**Interfaces:**
- Consumes: `src/agents/p3_metered_challenger.py`, `kaggle-environments`
- Produces: latency telemetry report with p95, p99, and max callback elapsed monotonic timing

- [ ] **Step 1: Write latency profile test for P3**

```python
# tests/test_p3_latency_profile.py
from pathlib import Path
import time
import kaggle_environments
import pytest
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_p3_latency_profile.py -v`
Expected: PASS

- [ ] **Step 3: Implement evaluation script `scripts/profile_p3_metered.py`**

```python
#!/usr/bin/env python3
"""Monotonic latency and margin evaluator for P3 Metered Challenger vs DECEM seed."""

from pathlib import Path
import time
import kaggle_environments


def evaluate_p3_on_decem_seed():
    seed = 848617604
    p2_path = "submission/prvsiyan_v2_package/main.py"
    p3_path = "src/agents/p3_metered_challenger.py"
    decem_path = (
        "docs/experiments/agent_selection/decem_evaluation/decem_tape_agent.py"
    )

    print(f"=== Benchmarking P3 vs DECEM Tape on Seed {seed} ===")

    # Run P2 V2 baseline
    env_p2 = kaggle_environments.make(
        "kaggriculture", configuration={"seed": seed}
    )
    t0 = time.perf_counter()
    steps_p2 = env_p2.run([p2_path, decem_path])
    p2_time = time.perf_counter() - t0
    r_p2 = steps_p2[-1][0]["reward"]
    d_p2 = steps_p2[-1][1]["reward"]

    # Run P3 Metered
    env_p3 = kaggle_environments.make(
        "kaggriculture", configuration={"seed": seed}
    )
    t0 = time.perf_counter()
    steps_p3 = env_p3.run([p3_path, decem_path])
    p3_time = time.perf_counter() - t0
    r_p3 = steps_p3[-1][0]["reward"]
    d_p3 = steps_p3[-1][1]["reward"]

    print(
        f"P2 V2 Baseline: Reward ${r_p2:,.0f} vs DECEM ${d_p2:,.0f} | Margin: {r_p2 - d_p2:+,.0f} | Time: {p2_time:.2f}s"
    )
    print(
        f"P3 Metered:     Reward ${r_p3:,.0f} vs DECEM ${d_p3:,.0f} | Margin: {r_p3 - d_p3:+,.0f} | Time: {p3_time:.2f}s"
    )
    print(f"P3 vs P2 Delta: {r_p3 - r_p2:+,.0f} gold")


if __name__ == "__main__":
    evaluate_p3_on_decem_seed()
```

- [ ] **Step 4: Execute evaluation script and verify output**

Run: `.venv/bin/python scripts/profile_p3_metered.py`
Expected: Output showing reward, margin, and delta without timeouts or errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/profile_p3_metered.py tests/test_p3_latency_profile.py
git commit -m "test(profile): add monotonic latency and matched seed evaluator for P3"
```

---

### Task 4: Packaging and Verification Suite

**Files:**
- Create: `submission/prvsiyan_v3_package/main.py`
- Modify: `tests/test_submission_v2_standalone.py` (add V3 package test)

**Interfaces:**
- Self-contained portable submission package (`submission/prvsiyan_v3_package/`) compatible with Kaggle submission tar.gz creation.

- [ ] **Step 1: Write standalone packaging test for V3**

```python
# In tests/test_submission_v2_standalone.py
def test_submission_v3_package_standalone():
    v3_main = Path("submission/prvsiyan_v3_package/main.py")
    if not v3_main.is_file():
        pytest.skip("V3 package not created yet")

    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
    steps = env.run(
        [str(v3_main.resolve()), "submission/prvsiyan_v2_package/main.py"]
    )
    assert len(steps) == 720
    assert steps[-1][0]["status"] == "DONE"
```

- [ ] **Step 2: Build the standalone V3 package directory**

Package `main.py`, `meter.py`, `baseline.py`, and `optimizer.py` inside `submission/prvsiyan_v3_package/` with fallback path resolution.

- [ ] **Step 3: Run full pytest suite across workspace**

Run: `.venv/bin/pytest -q`
Expected: All tests pass cleanly (117+ tests).

- [ ] **Step 4: Commit**

```bash
git add submission/prvsiyan_v3_package/ tests/test_submission_v2_standalone.py
git commit -m "feat(package): construct standalone Prvsiyan V3 submission package with lot metering"
```
