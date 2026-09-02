# Kaggle-Simulator Parity Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align our local simulator's rules, physics, and transitions 100% with the official Kaggle game engine, ensuring our offline evaluations perfectly mirror live ladder evaluations.

**Architecture:** We will modify `src/env/state.py` and `src/env/transitions.py` to support physical worker cargo carrying lists, adjacent drop/pickup operations at coordinate `(4, 4)`, hour 23 auto-drops with 100-item capacity limit enforcements, and strict animal feed consumption.

**Tech Stack:** Python 3.10+, numpy, pytest, kaggle-environments

**Spec:** `docs/superpowers/specs/2026-09-02-simulator-parity-design.md`

## Global Constraints
- **Python Version Floor:** 3.10+
- **Code Style:** Black formatting, Ruff linting (strict check before committing)
- **Engine Parity:** Transition output states must match `kaggle-environments` byte-for-byte.

---

## File Structure & Dependencies

We will modify and expand these files:
1. `src/env/state.py`: Update `WorkerState` to support `carrying` as a tuple of strings.
2. `src/env/transitions.py`: Implement physical `HARVEST`, `DROP`, `PICKUP`, and `FEED` logic, plus hour-23 auto-drops and capacity-overflow discards.
3. `tests/test_simulator_parity.py`: Build a strict, multi-turn cross-validation suite comparing our local transition states against `kaggle-environments`.

---

## Tasks

### Task 1: Update WorkerState Carrying Model

**Files:**
- Modify: `src/env/state.py`
- Modify: `tests/test_strategic_target.py`

**Interfaces:**
- Consumes: None (Core state models)
- Produces: Updated `WorkerState` with slatted, frozen representation.

- [ ] **Step 1: Write the failing unit test**
Modify `tests/test_strategic_target.py` (or add a test) to verify `WorkerState` supports carried item sequences:
```python
from src.env.state import WorkerState

def test_worker_state_carrying_sequence():
    worker = WorkerState(
        worker_id=1,
        x=2,
        y=3,
        carrying=("Wheat", "Strawberries"),
        is_busy=False
    )
    assert worker.carrying == ("Wheat", "Strawberries")
    assert len(worker.carrying) == 2
```

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_strategic_target.py -k "test_worker_state_carrying_sequence" -v`
Expected: FAIL (due to signature mismatch or typing mismatch if `carrying` expects `str | None` currently)

- [ ] **Step 3: Modify `WorkerState` in `src/env/state.py`**
Update `WorkerState` to:
```python
@dataclass(frozen=True, slots=True)
class WorkerState:
    """State of an individual farming unit on the grid."""

    worker_id: int
    x: int
    y: int
    carrying: tuple[str, ...]  # Tuple of carried item names (e.g. ("WHEAT",))
    is_busy: bool
```

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_strategic_target.py -v`
Expected: PASS

- [ ] **Step 5: Format and lint**
Run: `.venv/bin/black src/ tests/ && .venv/bin/ruff check src/ tests/`
Expected: No errors

- [ ] **Step 6: Commit**
```bash
git add src/env/state.py tests/test_strategic_target.py
git commit -m "feat: upgrade WorkerState carrying representation to support multi-item cargo"
```

---

### Task 2: Implement Physical Harvest, Drop, and Pickup in transitions.py

**Files:**
- Modify: `src/env/transitions.py`
- Modify: `tests/test_env_transitions.py`

**Interfaces:**
- Consumes: `WorkerState.carrying`, `FarmState.inventory`
- Produces: Upgraded `step_world` processing `DROP`, `PICKUP` and harvest-to-bag transitions.

- [ ] **Step 1: Write the failing unit test**
Append to `tests/test_env_transitions.py`:
```python
from src.env.state import WorkerState, FarmState, WorldState
from src.env.transitions import step_world

def test_physical_drop_command():
    # Worker at (4, 3) (adjacent to shed at 4,4) carrying 1 Wheat
    worker = WorkerState(worker_id=1, x=4, y=3, carrying=("Wheat",), is_busy=False)
    farm = FarmState(gold=1000, inventory={}, seed_inventory={}, workers=(worker,), expansion_quadrants=1)
    state = WorldState(turn=1, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(), farm=farm, tilled_tiles=())
    
    # Issue physical DROP command
    actions = {
        "worker_actions": {1: ("DROP", "Wheat", 1)},
        "farm_actions": []
    }
    next_state = step_world(state, actions)
    # The worker's bag should be empty, and the item should reside inside the farm shed inventory
    assert next_state.farm.workers[0].carrying == ()
    assert next_state.farm.inventory.get("Wheat", 0) == 1
```

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_env_transitions.py -k "test_physical_drop_command" -v`
Expected: FAIL (DROP command unrecognized or incorrect bag state)

- [ ] **Step 3: Update `step_world` in `src/env/transitions.py`**
1. **Redirect Harvest to Bag**:
   Modify `HARVEST` transition:
   ```python
   # Inside transitions.py under HARVEST command:
   if crop.growth_stage == 3:
       # Append to worker's carrying list, do NOT directly add to farm inventory
       updated_carrying = list(w.carrying) + [crop.crop_type]
       w = replace(w, carrying=tuple(updated_carrying))
       del crops_map[(tx, ty)]
       tilled.add((tx, ty))
   ```
2. **Implement `DROP` command**:
   ```python
   elif act_type == "DROP":
       item_type, qty = act[1], act[2]
       # Verify adjacent to central shed (4, 4)
       if abs(w.x - 4) + abs(w.y - 4) <= 1:
           carried_list = list(w.carrying)
           to_drop = [i for i in carried_list if i == item_type][:qty]
           # Only drop if it fits in 100-item shed capacity limit
           current_shed_load = sum(inventory.values())
           space_available = max(0, 100 - current_shed_load)
           droppable_qty = min(len(to_drop), space_available)
           
           for i in range(droppable_qty):
               carried_list.remove(item_type)
               inventory[item_type] = inventory.get(item_type, 0) + 1
           w = replace(w, carrying=tuple(carried_list))
   ```
3. **Implement `PICKUP` command**:
   ```python
   elif act_type == "PICKUP":
       item_type, qty = act[1], act[2]
       if abs(w.x - 4) + abs(w.y - 4) <= 1:
           available = inventory.get(item_type, 0)
           pickup_qty = min(qty, available)
           if pickup_qty > 0:
               inventory[item_type] -= pickup_qty
               updated_carrying = list(w.carrying) + [item_type] * pickup_qty
               w = replace(w, carrying=tuple(updated_carrying))
   ```

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_env_transitions.py -v`
Expected: PASS

- [ ] **Step 5: Format and lint**
Run: `.venv/bin/black src/ tests/ && .venv/bin/ruff check src/ tests/`
Expected: No errors

- [ ] **Step 6: Commit**
```bash
git add src/env/transitions.py tests/test_env_transitions.py
git commit -m "feat: implement physical DROP, PICKUP, and bag-bound HARVEST transition mechanics"
```

---

### Task 3: Implement Hour-23 Auto-Drop, Capacity Limits, and Feed Consumption

**Files:**
- Modify: `src/env/transitions.py`
- Modify: `tests/test_env_transitions.py`

**Interfaces:**
- Consumes: All updated transition mechanics
- Produces: Auto-drop dumps, 100-item capacity enforcements, and strict animal feed consumption.

- [ ] **Step 1: Write the failing unit test**
Append to `tests/test_env_transitions.py`:
```python
def test_hour_23_auto_drop_and_overflow_discard():
    # Setup state on hour 23 with worker carrying 5 Strawberries, and shed already having 98 Wheats
    worker = WorkerState(worker_id=1, x=4, y=4, carrying=("Strawberries",)*5, is_busy=False)
    farm = FarmState(gold=1000, inventory={"Wheat": 98}, seed_inventory={}, workers=(worker,), expansion_quadrants=1)
    state = WorldState(turn=23, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(), farm=farm, tilled_tiles=())
    
    next_state = step_world(state, {"worker_actions": {}, "farm_actions": []})
    # Since turn % 24 == 23, the worker's cargo must auto-drop.
    # Total units added: 5 Strawberries to 98 Wheats = 103 items.
    # The excess 3 items must be discarded, enforcing the strict 100-item shed capacity!
    assert next_state.farm.workers[0].carrying == ()
    total_shed = sum(next_state.farm.inventory.values())
    assert total_shed == 100
```

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_env_transitions.py -k "test_hour_23_auto_drop_and_overflow_discard" -v`
Expected: FAIL (either no auto-drop occurs or total items exceeds 100)

- [ ] **Step 3: Update `step_world` in `src/env/transitions.py`**
1. **Implement Hour 23 Auto-Drop**:
   At the end of `step_world` (turn compilation phase):
   ```python
   # If it is hour 23 of the day
   if state.turn % 24 == 23:
       final_workers = []
       for w in updated_workers:
           for item in w.carrying:
               inventory[item] = inventory.get(item, 0) + 1
           final_workers.append(replace(w, carrying=()))
       updated_workers = final_workers
       
       # Enforce strict 100-item shed limit (discarding oldest overflow)
       total_shed = sum(inventory.values())
       if total_shed > 100:
           excess = total_shed - 100
           # Deduct excess items proportionally or FIFO from inventory
           for item in list(inventory.keys()):
               if excess <= 0:
                   break
               count = inventory[item]
               to_remove = min(excess, count)
               inventory[item] -= to_remove
               excess -= to_remove
               if inventory[item] == 0:
                   del inventory[item]
   ```
2. **Implement Strict Animal Feed Consumption**:
   Modify `FEED` transition block:
   ```python
   elif act_type == "FEED":
       ax, ay = act[1], act[2]
       if abs(w.x - ax) + abs(w.y - ay) <= 1 and (ax, ay) in animals_map:
           # Worker MUST carry 1 "Wheat" to feed
           if "Wheat" in w.carrying:
               carried_list = list(w.carrying)
               carried_list.remove("Wheat")
               w = replace(w, carrying=tuple(carried_list))
               anim = animals_map[(ax, ay)]
               animals_map[(ax, ay)] = AnimalState(
                   animal_type=anim.animal_type,
                   hunger=max(0, anim.hunger - 40),
                   is_fed=True,
                   x=anim.x,
                   y=anim.y,
               )
   ```

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_env_transitions.py -v`
Expected: PASS

- [ ] **Step 5: Format and lint**
Run: `.venv/bin/black src/ tests/ && .venv/bin/ruff check src/ tests/`
Expected: No errors

- [ ] **Step 6: Commit**
```bash
git add src/env/transitions.py tests/test_env_transitions.py
git commit -m "feat: enforce hour-23 auto-drops, strict 100-item shed limit, and wheat-dependent animal feeding"
```

---

### Task 4: Complete High-Fidelity Cross-Validation Test

**Files:**
- Create: `tests/test_simulator_parity.py`

**Interfaces:**
- Consumes: All updated local state and transition files, `kaggle-environments` package.
- Produces: Complete validation of simulation parity on complex action sequences.

- [ ] **Step 1: Create the failing parity test file**
Create `tests/test_simulator_parity.py` to compare transition equivalence:
```python
from kaggle_environments import make
from src.env.state import WorkerState, FarmState, WorldState
from src.env.transitions import step_world

def test_kaggle_environments_byte_parity():
    # Initialize kaggle-environment instance
    env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 42})
    env.reset()
    
    # Mirror state in our local simulator
    # Execute identical actions on both and assert perfect state hash equivalence
    assert True # placeholder for the real parity comparisons
```

- [ ] **Step 2: Expand with rich step comparisons and assert perfect match equivalence**
Ensure the parity test loops through 24 mock turns, executing `TILE`, `PLANT`, `WATER`, `HARVEST`, `DROP`, `BUY_SEED`, and `SELL`, and asserting that both `env.state` (or parsed equivalent) and `next_state` are completely equal in gold, tilled coordinates, animal hunger, and inventories.

- [ ] **Step 3: Run the cross-validation test**
Run: `.venv/bin/pytest tests/test_simulator_parity.py -v`
Expected: PASS with 100% equivalence match.

- [ ] **Step 4: Commit**
```bash
git add tests/test_simulator_parity.py
git commit -m "test: add high-fidelity kaggle-environments cross-validation parity test"
```
