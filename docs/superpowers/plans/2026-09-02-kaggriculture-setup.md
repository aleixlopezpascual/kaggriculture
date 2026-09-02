# Kaggriculture Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize a production-ready, highly optimized, tested Python repository for the Kaggle Kaggriculture simulation competition, establishing core environment stubs, rule-based job prioritizers, pathfinding routing layers, an arena evaluator, and specialized AI instructions.

**Architecture:** Hybrid Dataclass State Model coupled with a decoupled deterministic Execution Router. Pure functional transition steps enable fast simulation, local rollouts, and exact state replay logs.

**Tech Stack:** Python 3.10+, NumPy, pytest, ruff, black

**Spec:** `docs/kaggriculture_system_design.md`

## Global Constraints
- **Python Version Floor:** 3.10+
- **Code Style:** Black formatting, Ruff linting (strict check before committing)
- **Time Limits:** All agent per-turn processing MUST execute in < 100 milliseconds
- **State Properties:** Use `frozen=True` and `slots=True` for all environment state dataclasses to guarantee immutability and speed.

---

### Task 1: Environment & Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `README.md`

**Interfaces:**
- Consumes: None (Root initialization)
- Produces: Base virtual environment configuration, linter configs, and game rules document.

- [ ] **Step 1: Write requirements.txt**
Create `/Users/aleix.lopez/kaggriculture/requirements.txt`:
```text
numpy>=1.22.0
pytest>=7.0.0
ruff>=0.0.250
black>=22.0.0
```

- [ ] **Step 2: Write pyproject.toml**
Create `/Users/aleix.lopez/kaggriculture/pyproject.toml`:
```toml
[tool.ruff]
line-length = 88
target-version = "py310"
select = ["E", "F", "W", "I"]

[tool.black]
line-length = 88
target-version = ['py310']
```

- [ ] **Step 3: Write README.md**
Create `/Users/aleix.lopez/kaggriculture/README.md` containing a complete overview of the rules, price elasticity mechanics, farming constraints, and worker labor scaling.

- [ ] **Step 4: Commit**
```bash
git add requirements.txt pyproject.toml README.md
git commit -m "chore: scaffold project requirements and configurations"
```

---

### Task 2: Core State Models & Dataclasses

**Files:**
- Create: `src/env/__init__.py`
- Create: `src/env/state.py`

**Interfaces:**
- Consumes: None
- Produces: Immutable state schemas representing crops, animals, workers, markets, and the farm grid.

- [ ] **Step 1: Create state stubs**
Write the state dataclasses into `src/env/state.py` with `slots=True` and `frozen=True`:
```python
from dataclasses import dataclass
from typing import Tuple, Dict, Optional

@dataclass(frozen=True, slots=True)
class CropState:
    id: int
    crop_type: str
    growth_stage: int
    water_level: int
    consecutive_unwatered: int
    fertilized_until: int

@dataclass(frozen=True, slots=True)
class AnimalState:
    id: int
    animal_type: str
    hunger_level: int
    consecutive_unfed: int
    yield_units: int
    care_score: int

@dataclass(frozen=True, slots=True)
class WorkerState:
    id: int
    is_hand: bool
    position: Tuple[int, int]
    carrying: Tuple[str, ...]

@dataclass(frozen=True, slots=True)
class FarmState:
    money: float
    workers: Tuple[WorkerState, ...]
    tiles: Tuple[Optional[dict], ...]
    shed_inventory: Dict[str, int]
    seed_inventory: Dict[str, int]

@dataclass(frozen=True, slots=True)
class WorldState:
    step: int
    day: int
    hour: int
    my_farm: FarmState
    opp_farm: FarmState
    market_prices: Dict[str, float]
    market_inventories: Dict[str, int]
```

- [ ] **Step 2: Commit**
```bash
git add src/env/__init__.py src/env/state.py
git commit -m "feat: add immutable dataclass structures for game state representation"
```

---

### Task 3: State Transition Simulator Engine

**Files:**
- Create: `src/env/transitions.py`

**Interfaces:**
- Consumes: `WorldState`, `FarmState`, `CropState`, `AnimalState`
- Produces: Pure-functional transition mapping `step_world(state, actions) -> next_state`.

- [ ] **Step 1: Implement step_world transitions**
Write pure transition rules for plant water decay, animal feeding, weather shifts, and step incrementation inside `src/env/transitions.py`.
```python
from src.env.state import WorldState, CropState, AnimalState
from dataclasses import replace

def step_crop(crop: CropState, watered: bool, weather: str) -> CropState:
    decay = 10 if weather == "SUNNY" else 5
    next_water = min(100, max(0, crop.water_level - decay + (30 if watered else 0)))
    consec = 0 if watered else crop.consecutive_unwatered + (1 if next_water == 0 else 0)
    
    next_stage = crop.growth_stage
    if 30 <= next_water <= 80:
        next_stage = min(4, crop.growth_stage + 1)
        
    return replace(crop, water_level=next_water, consecutive_unwatered=consec, growth_stage=next_stage)
```

- [ ] **Step 2: Commit**
```bash
git add src/env/transitions.py
git commit -m "feat: implement state transition function engine stubs"
```

---

### Task 4: Observation Parser

**Files:**
- Create: `src/env/parser.py`

**Interfaces:**
- Consumes: Raw observation JSON dictionary from Kaggle environment
- Produces: `WorldState` instance

- [ ] **Step 1: Write parse_observation**
In `src/env/parser.py`, map raw nested JSON arrays and dictionaries to typed dataclasses.
```python
from src.env.state import WorldState, FarmState, WorkerState, CropState, AnimalState

def parse_observation(obs_json: dict) -> WorldState:
    # Parsing logic
    ...
```

- [ ] **Step 2: Commit**
```bash
git add src/env/parser.py
git commit -m "feat: implement JSON observation parser"
```

---

### Task 5: Routing & Utility Calculators

**Files:**
- Create: `src/utils/__init__.py`
- Create: `src/utils/routing.py`
- Create: `src/utils/market.py`
- Create: `src/utils/calculators.py`
- Create: `src/utils/state_featurizer.py`

**Interfaces:**
- Consumes: `WorldState`, target actions
- Produces: Lowest-level AP movement instructions, ordered market transactions, yield projections, and feature matrices.

- [ ] **Step 1: Write routing and A* stubs**
Write Manhattan pathfinding heuristics into `src/utils/routing.py` to route workers toward prioritized tile targets.
- [ ] **Step 2: Write market prioritizing queue**
Implement sorted sell transactions (high sensitivity first) in `src/utils/market.py`.
- [ ] **Step 3: Commit**
```bash
git add src/utils/
git commit -m "feat: add routing pathfinders, calculators, and market sort layers"
```

---

### Task 6: Agents Implementation

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/base.py`
- Create: `src/agents/heuristic.py`
- Create: `src/agents/mcts.py`

**Interfaces:**
- Consumes: `WorldState`
- Produces: Action dictionary containing farmer instructions, hands, and sorted market orders.

- [ ] **Step 1: Write Agent Base class**
```python
from abc import ABC, abstractmethod
from src.env.state import WorldState

class BaseAgent(ABC):
    @abstractmethod
    def act(self, state: WorldState) -> dict:
        pass
```
- [ ] **Step 2: Write Heuristic Priority Agent**
Implement a deterministic priority agent assigning workers nearest high-priority agricultural tasks (`Harvest -> Feed -> Water -> Weeds -> Care -> Plant`).
- [ ] **Step 3: Commit**
```bash
git add src/agents/
git commit -m "feat: create agent abstractions and deterministic priority baseline"
```

---

### Task 7: Arena Evaluator & Self-Play

**Files:**
- Create: `src/arena/__init__.py`
- Create: `src/arena/evaluator.py`
- Create: `src/arena/self_play.py`
- Create: `src/arena/logger.py`

**Interfaces:**
- Consumes: `BaseAgent` versions, random seeds
- Produces: Simulated 720-turn matches and match metrics (Win rate, final ELO).

- [ ] **Step 1: Implement LocalArena runner**
In `src/arena/evaluator.py`, orchestrate dual-seat, multi-seed matching profiles.
- [ ] **Step 2: Commit**
```bash
git add src/arena/
git commit -m "feat: add local arena simulator and seed benchmarking pipeline"
```

---

### Task 8: Compilation Submission Script

**Files:**
- Create: `submission/compile_submission.py`

**Interfaces:**
- Consumes: All modular `src/` modules
- Produces: Single standalone `/submission/submission.py` script.

- [ ] **Step 1: Implement flattening compilation script**
Create a python script in `submission/compile_submission.py` that crawls `src/` imports, merges codes sequentially, filters local relative directories, and writes a self-contained submission file.
- [ ] **Step 2: Commit**
```bash
git add submission/compile_submission.py
git commit -m "feat: add submission compilation pipeline"
```

---

### Task 9: Unit Tests Setup

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_env_transitions.py`
- Create: `tests/test_agent_actions.py`

**Interfaces:**
- Consumes: Core `src/` transition and agent actions
- Produces: Exit 0 on passing test suites.

- [ ] **Step 1: Write test suites**
Create assertions in `tests/test_env_transitions.py` verifying state isolation, plant decay calculations, and water limits.
- [ ] **Step 2: Commit**
```bash
git add tests/
git commit -m "test: implement environment transition unit tests"
```

---

### Task 10: AI Instructions Setup

**Files:**
- Create: `GEMINI.md`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`

**Interfaces:**
- Consumes: None
- Produces: Developer instructions and terminal cheat-sheet files.

- [ ] **Step 1: Write specialized AI files**
Generate inside the repository root the three requested specialized guide docs matching our workspace patterns.
- [ ] **Step 2: Commit**
```bash
git add GEMINI.md AGENTS.md CLAUDE.md
git commit -m "docs: finalize developer and AI assistant instructions"
```
