# Design Specification: Kaggle-Simulator Parity Alignment

Date: 2026-09-02
Status: Draft & Spec Review

## 1. Executive Summary

Our current local simulator (`src/env/transitions.py`) contains major gaps in physics and rules alignment compared to the live `kaggle-environments` server. These gaps cause a severe local-live evaluation discrepancy: an agent that scores $10,800+ locally scores only $142 on Kaggle because it fails to perform physical crop transportation (bag to shed) and correct animal feeding loops.

This specification details the structural and behavioral modifications required to achieve **100% execution parity** with the Kaggle game engine. By implementing worker bags, physical drop/pickup commands, end-of-day auto-dumps with overflow discards, and strict animal feed consumption, we will ensure our local offline evaluations predict live ladder scores with absolute accuracy.

---

## 2. Key Parity Gaps & Solutions

| Mechanic | Local Simulator (`transitions.py`) | Kaggle Engine (`kaggle-environments`) | Parity Solution |
| :--- | :--- | :--- | :--- |
| **Harvest Delivery** | Instantly teleported to `FarmState.inventory`. | Placed in worker's private bag (`carrying`). | Append harvested items to `WorkerState.carrying` array. |
| **Market/Sells** | `SELL` command sells from generic inventory. | `SELL` command can ONLY deduct from the `shed` inventory. | Enforce that `SELL` only spends from `FarmState.inventory` (shed). |
| **Shed Interaction** | Non-existent (no `DROP`/`PICKUP` actions). | Workers adjacent to `(4,4)` must issue `DROP`/`PICKUP` commands. | Implement `DROP` and `PICKUP` action checks for adjacent coordinates. |
| **Shed Capacity** | Infinite capacity. | Hard limit of 100 non-seed items. Excess is discarded. | Implement a strict 100-item cap check on `FarmState.inventory`. |
| **End-of-Day Dump** | Non-existent. | At Hour 23, auto-drop all carried goods. Overflow is destroyed. | Loop through workers at hour 23, dump carrying arrays, discard if total > 100. |
| **Livestock Feeding** | Free of cost (hunger simply drops). | Consumes 1 `WHEAT` from shed daily. No feed = animal escapes. | Check and deduct 1 `WHEAT` from the shed for each animal feed cycle. |

---

## 3. Detailed Component Designs

### 3.1 State Representation Upgrades (`src/env/state.py`)
To hold carried goods, `WorkerState` must support an explicit sequence/tuple representing the bag inventory.

```python
@dataclass(frozen=True, slots=True)
class WorkerState:
    """State of an individual farming unit on the grid."""
    worker_id: int
    x: int
    y: int
    carrying: tuple[str, ...] # Sequence of item types currently carried (e.g. ("WHEAT", "MILK"))
    is_busy: bool
```

---

### 3.2 Transition Logic Modifications (`src/env/transitions.py`)

#### A. physical `HARVEST` and `COLLECT`
When `HARVEST` occurs on a mature crop at `(tx, ty)`:
- Instead of adding to `FarmState.inventory` directly, the harvested item name (e.g., `"Strawberries"`) is appended to the worker's `carrying` tuple.
- The same rule applies to livestock collections: milk, wool, and eggs are appended to the worker's `carrying` bag.

#### B. physical `DROP` and `PICKUP`
Workers can execute physical transactions when adjacent to the central farm shed. While only the Northwest quadrant is unlocked, the **only valid shed access coordinate is `(4, 4)`**.
- **`["DROP", item_type, qty]`**:
  - Valid if `manhattan_distance(worker.x, worker.y, 4, 4) <= 1`.
  - Moves up to `qty` of `item_type` from the worker's `carrying` list into `FarmState.inventory` (the shed), up to the 100-item maximum capacity limit.
- **`["PICKUP", item_type, qty]`**:
  - Valid if `manhattan_distance(worker.x, worker.y, 4, 4) <= 1`.
  - Moves up to `qty` of `item_type` (e.g. `"Wheat"`) from `FarmState.inventory` into the worker's `carrying` bag.

#### C. End-of-Day Auto-Drop & Discard (Hour 23)
At the end of each day (when `state.turn % 24 == 23`):
- Loop through all workers in `state.farm.workers`.
- For each worker, append all items from their `carrying` list into the shed `FarmState.inventory`.
- Empty their `carrying` list to `()`.
- Check shed capacity:
  ```python
  total_shed_units = sum(FarmState.inventory.values())
  if total_shed_units > 100:
      # Silently discard excess items over 100 (FIFO or proportional reduction)
      # Simulating Kaggle engine overflow destruction
  ```

#### D. Livestock Feed Consumption
When `FEED` is executed on an animal:
- The worker must be adjacent to the animal, and the worker **must carry 1 `"Wheat"` in their bag**.
- On success, the animal's hunger decreases, and 1 `"Wheat"` is removed from the worker's `carrying` list.
- If the worker does not carry `"Wheat"`, the action fails (`no-op`).

---

## 4. Verification and Parity Testing

To guarantee 100% accuracy, we will build a cross-validation script (`tests/test_simulator_parity.py`):
1. **Initialize identical states** in both our upgraded `transitions.py` and the official `kaggle-environments` package.
2. **Execute a sequence of complex actions** (watering, tilling, physical drops, buys, feeds) on both engines.
3. **Assert absolute state equivalence** (gold, worker bags, crop stages, and animal hunger values must be byte-for-byte identical after each turn transition).
