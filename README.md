# Kaggriculture

Kaggriculture is a highly competitive, multi-agent AI programming environment designed for elite Kaggle-style optimization challenges. Agents manage operations across dynamic grids containing soil tiles, crop fields, livestock structures, water supplies, and logistics systems.

---

## Game Engine Mechanics & Formulas

### 1. Agronomics & Crop Life-Cycle
Soil tile state is updated every turn based on agricultural properties:
- **Tilled/Untilled**: Seeds can only be planted on tilled soil tiles. Planting seeds consumes the tilled state. Harvesting restores the tile to tilled.
- **Moisture Level**:
  - Max moisture is 100.
  - Water decays dynamically according to weather:
    $$\text{Moisture}_{t+1} = \text{Moisture}_t - \text{Decay}(\text{Weather})$$
    - **Sunny**: $-10$ moisture per turn.
    - **Rainy**: $+15$ moisture per turn (capped at 100).
    - **Overcast**: $-5$ moisture per turn.
  - Crops suffer health/yield degradation if moisture falls below 20 or rises above 90 (flooded state).

### 2. Dynamic Market Curves
The market operates on an automated demand-responsive pricing mechanism. Market rates decay or appreciation is defined relative to remaining town inventories:
- **Town Inventory Ratio ($IR$)**:
  $$IR = \frac{\text{Current Inventory}}{\text{Target Capacity}}$$
- **Pricing Curve**:
  $$\text{Market Price} = \text{Base Price} \times \left(1.5 - IR\right)$$
  - Premium goods (Milk, Wool, Strawberries, Melons) appreciate much faster when town inventories are low.

### 3. Fibonacci Labor Wages
Workers must be paid wages that scale according to an sequential activation contract linked directly to the Fibonacci sequence:
$$\text{Wage}(n) = \text{Base Wage} \times F(n)$$
where $F(n)$ is the $n$-th Fibonacci number for the $n$-th worker currently hired.

### 4. Land Expansion
Farms can acquire adjacent grids to scale production. The cost of acquiring the $k$-th expanded grid quadrant is non-linear:
$$\text{Expansion Cost}(k) = \text{Base Cost} \times 2^k$$

### 5. Sequential Order Front-Running
Market orders are executed in a sequential clearance queue. Agents prioritizing orders containing high-margin, fast-decay crops (e.g., Strawberries, Melons) can front-run town demand consumption to lock in peak prices before general clearance drops town demand levels and lowers prices.

---

## Project Structure

- `src/env/`: High-performance immutable state representation and stateless transitions.
- `src/utils/`: Pathfinding, pricing calculators, market queues, and state featurization.
- `src/agents/`: Heuristic and Monte Carlo Tree Search agents.
- `src/arena/`: Multi-agent evaluators, self-play loops, and replay loggers.
- `competitors/`: Compiled and assembled elite-ladder competitor agents (EXP-173 v45 Fusion Router, Reyhan Dynamic Route Agent, Tetsu Market-Smart Router, EXP-173 Super-Fusion Router, Thomas 93.8% Router, Lynn Mathematical Router, Three-Day Shop Router v2, Six-Day Fieldbook v2, Kaito v27, Boatlee v14, Bruceqdu High-Score).
- `data/`: Raw manifests, datasets, and telemetry logs.
- `submission/`: Merging and flattening tool chain to build the submission script.
- `tests/`: Automated unit tests covering transitions and agents.

---

## 🏆 Current Active Submissions & SOTA Standings (Retrieved 2026-09-23 15:44 UTC)

Following a comprehensive 90-match round-robin tournament across the top public models, our two active competition slots on the live Kaggle ladder are:
1. **`Shepherd Sovereign`** (Ref ID: `56490949`): File `shepherd_sovereign_main.py`. Submitted 2026-09-23T10:46:41.287000. Status: COMPLETE. Score: **2154.3** (Private: blank). Historical context: #1 in the 90-match SOTA tournament with 73.3% win rate.
2. **`Jaxa 2802 Variant B`** (Ref ID: `56467787`): File `main_variant_b_h24.py`. Submitted 2026-09-22T15:02:43.093000. Status: COMPLETE. Score: **1786.3** (Private: blank). Historical context: Recorded the highest positive local tournament margin (+1,930 gold).

(Shepherd Sovereign is ahead with an active gap of 368.0).

For comprehensive architectural breakdowns, game-engine physics, and empirical A/B test findings, see:
* **Master Retrospective:** [`docs/kaggriculture_master_retrospective_2026_09_23.md`](docs/kaggriculture_master_retrospective_2026_09_23.md)
* **SOTA Tournament Report:** [`docs/competitor_tournament_results_2026_09_23.md`](docs/competitor_tournament_results_2026_09_23.md)
* **Empirical A/B Test Findings:** [`docs/research_update_2026_09_23.md`](docs/research_update_2026_09_23.md)
* **Experiment Version Ledger:** [`docs/experiments.md`](docs/experiments.md)

