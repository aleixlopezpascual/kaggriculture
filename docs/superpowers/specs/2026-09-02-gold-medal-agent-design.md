# Design Specification: Gold-Medal Hybrid Agent (Decoupled MCTS + Heuristic)

Date: 2026-09-02
Status: Approved & Validated

## 1. Executive Summary

To achieve a top-tier "Gold Medal" standing on the Kaggriculture leaderboard, our agent must solve two contradictory requirements:
1. **Long-Term Economic Strategy:** Deciding when to scale labor, invest in animal husbandry, buy quadrants, or transition crops based on multi-day cash flow analysis.
2. **Zero-Loss Hourly Execution:** Ensuring workers route perfectly, water plants before they wither, feed livestock before they starve, and front-run the market sequential price evaluation—all within a strict **100ms per-turn execution limit**.

This specification details the **Decoupled Hybrid Agent**. It splits decision-making into a high-level **Strategic MCTS Brain** that runs once per day to set high-level resource goals, and a **Tactical Heuristic Execution Core** that runs hourly to handle worker routing and emergency overrides dynamically.

---

## 2. Architecture & Data Flow

The system consists of the following components:

```text
       ┌────────────────────────────────────────────────────────┐
       │                   Kaggle Match Server                  │
       └───────────────────────────┬────────────────────────────┘
                                   │ Raw Observation JSON
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                    src/env/parser.py                   │
       │       (parse_world_state: JSON -> WorldState)          │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                  src/agents/mcts.py                    │
       │  MCTSAgent: Run macro rollouts daily to select goals   │
       │  Outputs: StrategicTarget                              │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                src/agents/heuristic.py                 │
       │  HeuristicAgent: Hourly greedy executor of targets     │
       │  Outputs: worker_actions, farm_actions                 │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 src/utils/market.py /                  │
       │                 src/utils/routing.py                   │
       │  (Pathfinding and premium order sorting optimization)   │
       └───────────────────────────┬────────────────────────────┘
                                   │ Output Action JSON
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                   Kaggle Match Server                  │
       └────────────────────────────────────────────────────────┘
```

---

## 3. Component Deep-Dives

### 3.1 The Strategic Contract: `StrategicTarget`
Located in `src/env/state.py`, this immutable data model defines the macro targets selected by the Strategic Brain:

```python
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True, slots=True)
class StrategicTarget:
    target_workers: int              # Desired active worker count (farmer + hired hands)
    target_cows: int                 # Target Cow count
    target_sheep: int                # Target Sheep count
    target_geese: int                # Target Goose count
    crop_priorities: Dict[str, int]  # Ratio/target counts of crops (e.g., {'Wheat': 10, 'Strawberries': 15})
    budget_reserved_for_seeds: float # Keep this cash reserve back to avoid seed starvation
    is_liquidating: bool             # When True (Turn 680+), triggers pure market dump
```

---

### 3.2 The Strategic Brain: `MCTSAgent` (`src/agents/mcts.py`)

#### A. Trigger Frequency
To stay well within the **100ms time limit**, the MCTS brain does NOT run every turn. It is triggered only:
1. At the **start of each day** (when `state.hour == 0`).
2. If the current `StrategicTarget` is **fully achieved** (e.g. we wanted 3 cows and 3 are bought, or 10 strawberries are planted).
3. If an **emergency state** occurs (e.g. cash drops below a minimum threshold).

#### B. Macro Search Tree
Rather than branching on micro worker movements (e.g., `MOVE_UP`, `TILE`), MCTS branches on **Strategic Targets** (Macro Options).
Available Macro Options for branching:
- **`FocusCrops(crop_type)`**: Sets target workers to 3, target seeds to maximum, and crop priorities to 100% of selected type.
- **`FocusLivestock(animal_type)`**: Sets target crops to grow Wheat (pasture feed) and targets buying the selected livestock type.
- **`ScaleLabor(target_hands)`**: Sets target hands to 3-5 while keeping crop targets balanced.
- **`BuyLand`**: Saves cash to buy the next land quadrant.
- **`Liquidate`**: Prepares turn 680+ final salvage.

#### C. Fast Simulator Rollouts
During MCTS search, node expansion and transitions are rolled out using the stateless, ultra-fast `step_world` function in `src/env/transitions.py`.
- Rollouts run a depth of **2 to 3 days** (48 to 72 turns).
- Rollouts utilize `HeuristicAgent` initialized with the candidate `StrategicTarget` to simulate greedy hourly actions, ensuring extremely realistic lookahead trajectories.
- Value evaluation aggregates total gold plus terminal asset valuation (shed inventory and animals discounted to 50% value).

---

### 3.3 The Tactical Execution Core: `HeuristicAgent` (`src/agents/heuristic.py`)

The Heuristic Core executes hourly. It evaluates the current `WorldState` and drives the farm toward the active `StrategicTarget` while handling dynamic micro-preservations.

#### A. Real-Time Emergency Overrides
Before executing target-driven tasks, workers check for emergency states:
- **Crop Moisture < 30%**: Water immediately.
- **Animal Hunger > 50%**: Feed Wheat immediately from inventory (or fetch Wheat from the shed).
- **Weeds present**: Dig and till immediately to reclaim land.

#### B. Target-Driven Actions
If no emergencies exist, workers are assigned tasks to fulfill targets:
- **Hiring Hands**: If current worker count < `target_workers`, queue a `HIRE_WORKER` farm action.
- **Animal Purchase**: If current animal count < `target_animal`, and cash > animal cost + `budget_reserved_for_seeds`, buy the animal.
- **Crop Planting**: If crop count < `crop_priorities` targets:
  - Check seed inventory. If seeds are missing, purchase seeds.
  - Route to tilled tiles and `PLANT`.

#### C. Logistics and Shed Interactivity
To prevent worker AP waste:
- Workers check their bag. If carrying mature crops or harvested livestock products, they path to the **central farm shed** to `DROP` items.
- If an animal needs feeding and the worker has no Wheat, they path to the shed to `PICKUP` Wheat before moving to the animal.

#### D. Sequential Order Precedence (Front-Running)
To capture peak pricing:
- Market sell orders are compiled and sorted in memory before submission:
  `["SELL", "MILK", qty]`, `["SELL", "WOOL", qty]`, `["SELL", "STRAWBERRIES", qty]`, `["SELL", "MELONS", qty]`, `["SELL", "CARROTS", qty]`, `["SELL", "WHEAT", qty]`
- Placed at the very top of the actions command array.

---

## 4. Testing & Validation Plan

To ensure our new Hybrid Agent achieves the high performance required for gold-medal standing, we run a rigorous 3-step validation pipeline:

### 4.1 Unit Verification (`tests/`)
- Verify `StrategicTarget` matches parser and compiler layouts.
- Verify MCTS brain completes 50 simulations in under **30 milliseconds** on local states.
- Verify `HeuristicAgent` handles emergency overrides perfectly under rainy vs. sunny weather conditions.

### 4.2 Multi-Seed Both-Seat Arena Benchmarking (`src/arena/`)
- Run a head-to-head tournament: `HeuristicAgent` (baseline) vs. `DecoupledHybridAgent` (MCTS + Heuristic).
- Run across **50 random seeds** (100 total matches: each agent plays Seat 0 and Seat 1 once per seed).
- Criteria to claim victory:
  - **Win Rate > 75%** against the baseline.
  - **Zero timeouts** (ensure average hourly processing time is `< 10ms`, with strategic decision peaks `< 50ms`).
  - **Average ending gold increase of > 30%** over pure greedy.

### 4.3 Standalone Compilation Verification
- Run `python submission/compile_submission.py` and ensure the single-file bundle builds without warnings.
- Verify the generated `submission.py` passes syntax, format, and static type checks.
