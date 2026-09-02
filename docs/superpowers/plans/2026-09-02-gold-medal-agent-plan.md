# Gold-Medal Hybrid Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a production-ready, top-tier decoupled agent that uses MCTS for daily strategic macro target selection and a prioritized heuristic queue for hourly tactical worker routing, securing a Gold Medal ranking.

**Architecture:** A decoupled hybrid design. `MCTSAgent` runs daily at hour 0 to search and select a `StrategicTarget` dataclass representing target workers, animal counts, crop distributions, and reserves. `HeuristicAgent` runs hourly, consuming the current target to drive tilling, planting, feeding, watering, shed drop-offs, and sequential premium market order front-running.

**Tech Stack:** Python 3.10+, NumPy, pytest, ruff, black

**Spec:** `docs/superpowers/specs/2026-09-02-gold-medal-agent-design.md`

## Global Constraints
- **Python Version Floor:** 3.10+
- **Code Style:** Black formatting, Ruff linting (strict check before committing)
- **Time Limits:** All agent per-turn processing MUST execute in < 100 milliseconds
- **State Properties:** Use `frozen=True` and `slots=True` for all environment state dataclasses to guarantee immutability and speed.

---

## File Structure & Dependencies

We will modify and expand these key files:
1. `src/env/state.py`: Append `StrategicTarget` dataclass.
2. `src/agents/heuristic.py`: Upgrade `HeuristicAgent` to accept and drive towards a `StrategicTarget` with emergency overrides, logistics, and front-running.
3. `src/agents/mcts.py`: Refactor `MCTSAgent` to cache targets and branch on macro targets using target-guided rollouts.
4. `tests/test_agent_actions.py`: Add robust unit tests verifying target satisfaction, logistics, and MCTS selection.

---

## Tasks

### Task 1: Strategic Target Dataclass Definition

**Files:**
- Modify: `src/env/state.py`
- Create: `tests/test_strategic_target.py`

**Interfaces:**
- Consumes: None (Core data structure)
- Produces: `StrategicTarget` dataclass with slots and frozen representation.

- [ ] **Step 1: Write the failing unit test**
Create `/Users/aleix.lopez/kaggriculture/tests/test_strategic_target.py`:
```python
from src.env.state import StrategicTarget

def test_strategic_target_instantiation():
    target = StrategicTarget(
        target_workers=4,
        target_cows=3,
        target_sheep=2,
        target_geese=1,
        crop_priorities={"Wheat": 8, "Strawberries": 12},
        budget_reserved_for_seeds=200.0,
        is_liquidating=False
    )
    assert target.target_workers == 4
    assert target.target_cows == 3
    assert target.crop_priorities["Wheat"] == 8
    assert target.is_liquidating is False
```

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_strategic_target.py -v`
Expected: FAIL with `ImportError: cannot import name 'StrategicTarget'`

- [ ] **Step 3: Implement `StrategicTarget` in `src/env/state.py`**
Append to the end of `/Users/aleix.lopez/kaggriculture/src/env/state.py`:
```python
@dataclass(frozen=True, slots=True)
class StrategicTarget:
    target_workers: int
    target_cows: int
    target_sheep: int
    target_geese: int
    crop_priorities: dict[str, int]
    budget_reserved_for_seeds: float
    is_liquidating: bool
```

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_strategic_target.py -v`
Expected: PASS

- [ ] **Step 5: Format and lint**
Run: `.venv/bin/black . && .venv/bin/ruff check .`
Expected: No errors

- [ ] **Step 6: Commit**
```bash
git add src/env/state.py tests/test_strategic_target.py
git commit -m "feat: define StrategicTarget data model for strategic coordination"
```

---

### Task 2: Refactor Heuristic Agent for Target-Driven Execution

**Files:**
- Modify: `src/agents/heuristic.py`
- Modify: `tests/test_agent_actions.py`

**Interfaces:**
- Consumes: `WorldState`, `StrategicTarget`
- Produces: Updated `HeuristicAgent` taking `StrategicTarget` in `act(state, target=None)`. If target is `None`, instantiates a default starting target representing baseline behavior.

- [ ] **Step 1: Write the failing unit test**
Append to `/Users/aleix.lopez/kaggriculture/tests/test_agent_actions.py`:
```python
from src.agents.heuristic import HeuristicAgent
from src.env.state import StrategicTarget, WorldState, FarmState, WorkerState

def test_heuristic_drives_cow_target():
    # Setup state with enough gold but no cows, and a target of 1 cow
    farmer = WorkerState(worker_id=1, is_hand=False, position=(0,0), carrying=())
    farm = FarmState(gold=1000.0, workers=(farmer,), tiles=Tuple[Optional[dict], ...]((None,)*100), shed_inventory={}, seed_inventory={})
    # Empty world
    # (Assuming a mockup state instance is created)
```
Wait! Let's look at `tests/test_agent_actions.py` first to see how mock states are currently set up.
(We'll write a mock state initializer that mirrors the existing test setups). Let's see the step 1 code details:

```python
from src.agents.heuristic import HeuristicAgent
from src.env.state import StrategicTarget, WorldState, FarmState, WorkerState

def test_heuristic_drives_cow_target():
    farmer = WorkerState(worker_id=1, x=0, y=0, carrying=None)
    farm = FarmState(gold=1000.0, workers=(farmer,), tiles=(), expansion_quadrants=(), inventory={})
    state = WorldState(
        turn=1,
        weather="Sunny",
        grid_width=10,
        grid_height=10,
        crops=(),
        animals=(),
        farm=farm,
        tilled_tiles=(),
    )
    target = StrategicTarget(
        target_workers=1,
        target_cows=1,
        target_sheep=0,
        target_geese=0,
        crop_priorities={},
        budget_reserved_for_seeds=50.0,
        is_liquidating=False
    )
    agent = HeuristicAgent()
    actions = agent.act(state, target=target)
    # The agent should purchase a COW as a farm action since it is below target
    assert "BUY_COW" in actions.get("farm_actions", [])
```

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_agent_actions.py -k "test_heuristic_drives_cow_target" -v`
Expected: FAIL (either `BUY_COW` not in actions or target parameter unhandled)

- [ ] **Step 3: Update `HeuristicAgent` in `src/agents/heuristic.py`**
Modify `HeuristicAgent.act` to accept an optional `target: StrategicTarget = None` argument. If `target` is `None`, use a default:
```python
        if target is None:
            target = StrategicTarget(
                target_workers=3,
                target_cows=0,
                target_sheep=0,
                target_geese=0,
                crop_priorities={"Strawberries": 10},
                budget_reserved_for_seeds=100.0,
                is_liquidating=False
            )
```
Implement emergency overrides first:
1. **Watering Emergency:** Any crop with moisture <= 30 is queued for watering.
2. **Starvation Emergency:** Any animal with hunger >= 50 is queued for feeding.
3. **Weed Emergency:** Any weed tile is cleared.

Implement target satisfaction actions:
1. **Hiring Hands:** If `len(state.farm.workers) < target.target_workers` and gold > wage, queue `HIRE_WORKER`.
2. **Animal Purchasing:** If cow count < `target.target_cows` and cash > `500 + target.budget_reserved_for_seeds`, buy cow. Same for sheep (cost 300) and geese (cost 150).
3. **Planted Crop Satisfaction:** Maintain crop counts according to `target.crop_priorities`.
4. **Market front-running order sorting:** Collect all sell orders and sort with high-value premium items (Milk, Wool, Strawberries, Melons) first.

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_agent_actions.py -v`
Expected: PASS

- [ ] **Step 5: Format and lint**
Run: `.venv/bin/black . && .venv/bin/ruff check .`
Expected: No errors

- [ ] **Step 6: Commit**
```bash
git add src/agents/heuristic.py tests/test_agent_actions.py
git commit -m "feat: upgrade HeuristicAgent to execute dynamic StrategicTargets"
```

---

### Task 3: Refactor MCTSAgent for Daily Macro Strategy Selection

**Files:**
- Modify: `src/agents/mcts.py`
- Modify: `tests/test_agent_actions.py`

**Interfaces:**
- Consumes: `WorldState`, updated `HeuristicAgent`, `StrategicTarget`
- Produces: `MCTSAgent` caching target and executing selection daily at hour 0 or upon completion of previous targets.

- [ ] **Step 1: Write the failing unit test**
Append to `/Users/aleix.lopez/kaggriculture/tests/test_agent_actions.py`:
```python
from src.agents.mcts import MCTSAgent

def test_mcts_caches_and_selects_target():
    # Setup standard state
    farmer = WorkerState(worker_id=1, x=0, y=0, carrying=None)
    farm = FarmState(gold=1000.0, workers=(farmer,), tiles=(), expansion_quadrants=(), inventory={})
    state_day_0_hour_0 = WorldState(
        turn=0,
        weather="Sunny",
        grid_width=10,
        grid_height=10,
        crops=(),
        animals=(),
        farm=farm,
        tilled_tiles=(),
    )
    agent = MCTSAgent(num_simulations=5)
    # Turn 0 (Hour 0 of Day 0) should trigger strategic selection
    actions = agent.act(state_day_0_hour_0)
    assert agent.active_target is not None
```

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_agent_actions.py -k "test_mcts_caches_and_selects_target" -v`
Expected: FAIL with `AttributeError` or target selection missing

- [ ] **Step 3: Update `MCTSAgent` in `src/agents/mcts.py`**
1. Add `self.active_target: StrategicTarget | None = None` to `__init__`.
2. Update `act` method:
   - Check if `self.active_target` is `None`, or `state.turn % 24 == 0` (start of day), or target has been fully satisfied.
   - If true, run MCTS search over 4 candidate macro `StrategicTarget` targets:
     - `CropFocus(Strawberries)`
     - `LivestockFocus(Cows)`
     - `LaborScale(5)`
     - `LiquidateFocus` (if turn >= 680)
   - Perform MCTS node selections and expansions using the macro candidate target values.
   - Run daily-scale rollouts using the local fast simulator (`step_world`) guided by `HeuristicAgent(target)`.
   - Update `self.active_target` with the best evaluated macro target.
   - Retrieve and return actions from `self.heuristic_fallback.act(state, target=self.active_target)`.

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_agent_actions.py -v`
Expected: PASS

- [ ] **Step 5: Format and lint**
Run: `.venv/bin/black . && .venv/bin/ruff check .`
Expected: No errors

- [ ] **Step 6: Commit**
```bash
git add src/agents/mcts.py tests/test_agent_actions.py
git commit -m "feat: implement MCTS macro-target Daily Strategic Brain selector"
```

---

### Task 4: Local Arena Benchmark and Standalone Compilation

**Files:**
- Modify: None (pure validation & build execution)

**Interfaces:**
- Consumes: All updated files
- Produces: `submission/submission.py` running successfully in local benchmarks

- [ ] **Step 1: Compile the final submission**
Run: `python3 submission/compile_submission.py`
Expected: Standalone file generated successfully at `submission/submission.py` without warnings

- [ ] **Step 2: Run Pytest suite**
Run: `.venv/bin/pytest`
Expected: 100% tests passed (including both our new tests and all old tests)

- [ ] **Step 3: Validate Standalone Code Syntax**
Run: `python3 -m py_compile submission/submission.py`
Expected: Compiles with 0 syntax or parsing errors

- [ ] **Step 4: Execute Multi-Seed Tournament**
Run a local multi-seed simulation benchmarking `HeuristicAgent` vs `MCTSAgent`:
```bash
.venv/bin/python -c "
from src.agents.mcts import MCTSAgent
from src.arena.evaluator import LocalArena
agent = MCTSAgent(num_simulations=10)
arena = LocalArena(agent)
results = arena.benchmark(seeds=[42, 100, 2026])
print('Hybrid MCTS Benchmark:', results)
assert results['avg_gold'] > 2700.0, 'Hybrid MCTS must outperform basic greedy!'
"
```
Expected: Average gold > 2700.0, fast runs (< 100ms total), 0 timeouts.

- [ ] **Step 5: Final Git Status Check**
Run: `git status`
Expected: Workspace fully clean and all files properly tracked.
