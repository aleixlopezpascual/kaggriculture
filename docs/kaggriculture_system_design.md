# Kaggriculture Workspace: System Design & Architecture Specification

This specification document outlines the production-ready system architecture for our autonomous farming and trading agent in the Kaggle Kaggriculture competition. The design is structured to prioritize execution speed (within the 100ms per-turn limit), clean functional separation, and multi-seed local validation.

---

## 🏗️ 1. System Topology Overview

We decouple the system into four independent modules communicating through immutable data models:

```text
       ┌────────────────────────────────────────────────────────┐
       │                 Kaggle Match Server                    │
       └───────────────────────────┬────────────────────────────┘
                                   │ Raw Observation JSON
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                    src/env/parser.py                   │
       │     (Parses observation JSON -> WorldState dataclass)  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                   src/agents/base.py                   │
       │           (Active Agent Strategy Selector)             │
       └─────┬────────────────────────────────────────────┬─────┘
             │                                            │
             │ Deterministic Branch                       │ Lookahead Branch
             ▼                                            ▼
┌────────────────────────┐                  ┌────────────────────────┐
│ src/agents/heuristic.py│                  │   src/agents/mcts.py   │
│  (Greedy Queue-Based)  │                  │  (Macro Decision Tree) │
└────────────┬───────────┘                  └────────────┬───────────┘
             │                                            │
             └─────────────────────┬──────────────────────┘
                                   │ Task Action Specifications
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                   src/utils/routing.py                 │
       │     (Resolves Task AP Allocations -> Farmer/Hand MOVES)│
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                  src/utils/market.py                   │
       │       (Sorts and prioritizes premium sell orders)      │
       └───────────────────────────┬────────────────────────────┘
                                   │ Output Action JSON
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 Kaggle Match Server                    │
       └────────────────────────────────────────────────────────┘
```

---

## 🗃️ 2. Core Modules & Component Specifications

### 2.1 State Representation (`src/env/state.py`)
State is stored in frozen, slatted Python dataclasses to eliminate the memory overhead of `__dict__` and guarantee reference safety during tree expansion.

```python
from dataclasses import dataclass
from typing import Tuple, Dict, NamedTuple, Optional

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
    tiles: Tuple[Optional[dict], ...]  # 100 tiles representing grid
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

### 2.2 Job Priorities & Router (`src/utils/routing.py`)
To manage spatial movement efficiently, we use a prioritized greedy task matcher.
- **Priority Queue Definition:**
  ```python
  JOB_PRIORITIES = [
      "HARVEST_LIVESTOCK", # Yields Milk, Wool (High Value)
      "FEED_LIVESTOCK",    # Starvation prevention (Critical)
      "HARVEST_CROPS",     # Melons, Strawberries (High Value)
      "WATER_PLANTS",      # Wither prevention (Daily)
      "DIG_WEEDS",         # Clear ground
      "APPLY_CARE",        # Happiness bonus
      "PLANT_SEEDS",       # Space utilization
      "TILL_TILES"         # Expansion prep
  ]
  ```
- **The Task Dispatcher:**
  Each worker is assigned tasks based on its current position and the job matrix. The router pathfinds to the tile, emits matching `["MOVE", direction]` vectors until the distance is 0, and then executes the interaction command (e.g., `["WATER"]`).

### 2.3 Order Prioritization Filter (`src/utils/market.py`)
To combat price elasticity and capture peak town multipliers, all transaction outputs are re-sorted before serialization:
```python
def compile_market_actions(pending_sales: list[dict]) -> list[list]:
    # Sort order: Milk/Wool/Eggs/Strawberry -> Melon -> Carrot -> Wheat
    # Ensures highest-margin transactions settle first in sequential town evaluation
    ...
```

---

## 🧪 3. Local Arena Evaluator Specification (`src/arena/`)

To validate changes locally across hundreds of games without Kaggle ladder matchmaking latency:

- **Match Simulator (`src/arena/evaluator.py`):** Holds a pure Python port of Kaggriculture’s transitions (`step_world`).
- **Seed-Swiped Tests:** Runs head-to-head evaluation matches.
  ```python
  def run_benchmarks(agent_a, agent_b, num_seeds: int = 50):
      # Evaluates agent_a vs agent_b on both Player 0 and Player 1 seats across num_seeds.
      # Returns: Win Rate, Average Cash Margin, Draw Rate.
  ```

---

## 🚀 4. Compilation & Submission Pipeline (`submission/`)

Since Kaggle requires a single self-contained Python file (`submission.py`) for upload:
- **`compile_submission.py`** scans our modular code directories (`src/`), flattens classes, strips local imports, bundles dependency stubs, and outputs a clean, unified `submission.py` ready for upload.
