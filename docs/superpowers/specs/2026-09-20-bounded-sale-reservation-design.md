# Kaggriculture: Bounded Sale Reservation Design Specification

This document details the architectural and mechanical design for the **Bounded Sale Reservation (Ready Stock, Earlier Sales)** optimization layer. This post-processing engine wraps around any underlying Kaggriculture agent to optimize transaction timing under market price-decay conditions.

---

## 🎯 1. Purpose and Success Criteria

*   **Objective:** Pull planned future sales forward to the current turn if the required commodity stock is already physically available in the farm shed.
*   **The Problem it Solves:** Agents often pre-plan sales for specific future turns. However, if the crop is harvested early or cows/sheep yield earlier due to favorable random walk variables, the stock sits idle in the shed. Opponent sales or town demand decay can depress market quotes during this idle period.
*   **Success Metric:** Under 10 sequential matchups (Seeds `[42, 100, 2026, 1234, 555]`, both seats) against `Jaxa 2802 Elo Router` and `Reyhan Dynamic Route Agent`:
    1.  Zero execution errors or invalid actions.
    2.  An increase in the candidate's average gold margin.
    3.  A win rate $>50\%$ when applied to our baseline controllers.

---

## 🏗️ 2. Architectural Structure

The Bounded Sale Reservation acts as an intermediate **action post-processor** inserted between the raw strategic output of the agent and the Kaggle environment formatting step:

```text
       ┌────────────────────────────────────────────────────────┐
       │                   parse_world_state()                  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │               Underlying Agent (.act() / .agent())     │
       └───────────────────────────┬────────────────────────────┘
                                   │ Raw Dict / JointActions
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │           BoundedSaleReservation Post-Processor        │
       │  (Adjusts sales earlier; records debt logs; enforces)   │
       └───────────────────────────┬────────────────────────────┘
                                   │ Optimized Actions Dict
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                   Kaggle Match Server                  │
       └────────────────────────────────────────────────────────┘
```

---

## ⚙️ 3. Component Details & Mechanics

We implement the engine inside `src/utils/sale_reservation.py` as a stateless or stateful tracker:

```python
class BoundedSaleReservation:
    def __init__(self, parent_agent):
        self.parent_agent = parent_agent
        self.debt_records = {}  # item_name (capitalized) -> quantity (int)
        self.current_shop_block = None

    def process_turn(self, state, raw_actions):
        """
        state: WorldState dataclass representing current turn
        raw_actions: list of market orders from the parent agent: e.g., [("BUY_PRODUCT", "Wheat", 5), ("SELL", "Wheat", 10)]
        """
```

### 3.1 Shop Block Reset
Kaggriculture features 72-turn shop blocks (0–71, 72–144, etc.). Gated pricing curves and lottery structures reset at block transitions.
*   **Rule:** At the start of turn processing, we calculate the current block: `block = state.turn // 72`.
*   **Action:** If `self.current_shop_block != block`, we reset `self.current_shop_block = block` and clear `self.debt_records = {}`. Debt can never carry over across shop blocks.

### 3.2 Debt Settlement Pass
Before considering lookahead sales, the engine must settle any existing debt:
1.  Separate the parent's proposed market orders into `sales` and `buys`.
2.  For each proposed `SELL` action: `("SELL", item, qty)`:
    *   If `self.debt_records.get(item, 0) > 0`:
        *   Retrieve debt: `debt = self.debt_records[item]`.
        *   If `qty > debt`:
            *   Update sale to `adjusted_qty = qty - debt`.
            *   Clear debt: `self.debt_records[item] = 0`.
            *   Keep the adjusted sale action: `("SELL", item, adjusted_qty)`.
        *   If `qty <= debt`:
            *   Reduce debt: `self.debt_records[item] -= qty`.
            *   Omit/discard this sale action completely (pre-sold).

### 3.3 Sliding Window Lookahead Pass
During step range `288 <= state.turn <= 695` (where cash flows and premium cycles are dense):
1.  Calculate current available stock in the shed: `avail_stock = dict(state.farm.inventory)`.
2.  Subtract currently scheduled sales of the current turn from `avail_stock` to establish the safe surplus:
    $$\text{Surplus}(item) = \text{ShedStock}(item) - \text{CurrentTurnScheduledSales}(item)$$
3.  Simulate a lookahead up to **5 actions** (or **4 steps** ahead) using the parent agent's pre-computed actions or a tape-querying mock function.
4.  For each future scheduled sale of `(future_item, future_qty)` encountered:
    *   If `Surplus(future_item) >= future_qty`:
        *   Pull the sale to the current turn: prepend `("SELL", future_item, future_qty)` to our market actions.
        *   Record the debt: `self.debt_records[future_item] = self.debt_records.get(future_item, 0) + future_qty`.
        *   Deduct from surplus: `Surplus(future_item) -= future_qty`.

### 3.4 Bounded Safety Guards (Fail-safes)
*   **Feeding/Purchase Exclusions:** If the player has a scheduled purchase of an animal (e.g., `BUY_ANIMAL`) or worker feeds that require the commodity, lookahead immediately terminates for that item to prevent cash/feed starvation.
*   **Day 28 Liquidation Gating:** When `state.turn >= 672` (Day 28), lookahead is permanently disabled, and the default full terminal liquidation runs natively.

---

## 🧪 4. Testing & Verification Strategy

### 4.1 Unit Tests (`tests/test_sale_reservation.py`)
We will write comprehensive mock-based unit tests to cover:
1.  **Debt Deduction:** Verify that pulling 10 Wheat early successfully registers a debt of 10 and eats a future 10 Wheat sale.
2.  **Shop Block Reset:** Verify that crossing turn 72 clears `debt_records` and restarts reservation.
3.  **Surplus Bounds:** Verify that we never sell premium items early if the shed inventory is empty.

### 4.2 Local Tournament Runs
We will register `Escalation with Bounded Sale Reservation` under `src/arena/run_tournament.py` and run a Head-to-Head matchup against the base `Heuristic v2 (Escalation)`.
