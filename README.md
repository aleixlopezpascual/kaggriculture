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

## 🏆 Historical Live Submissions & Standings Snapshot (Dated 2026-09-25 15:55 CEST (+0200))

*(Historical dated snapshot as of 2026-09-25 15:55 CEST (+0200); not a live-current standing. No submission was made during this documentation update.)*

Under Kaggle's active tracking policy (where only the latest two submissions remain active in live simulation and evaluation)[1], our latest-two tracked competition slots on the live ladder are:
1. **`Prvsiyan Moon Counts Melons`** (Ref ID: `56531885`): File `prvsiyan_kaggriculture_submission.tar.gz`. Submitted 2026-09-24T21:25:39.747000. Status: COMPLETE. Public Score: **2093.9** (Private: blank). Latest episode query: 125 completed public episodes and 1 completed validation episode.[36]
2. **`Shepherd Sovereign`** (Ref ID: `56490949`): File `shepherd_sovereign_main.py`. Submitted 2026-09-23T10:46:41.287000. Status: COMPLETE. Public Score: **2034.7** (Private: blank). Latest episode query: 284 completed public episodes and 1 completed validation episode.[36] Historical context: achieved a 73.3% win rate in the earlier 90-match local SOTA tournament.

Third / Older (Outside latest-two tracked pair):
* **`Jaxa 2802 Variant B`** (Ref ID: `56467787`): Status: COMPLETE. Public Score: **1680.8** (Private: blank). Retired to third/older and freezes its Elo rating.[36]

*(Note: Prvsiyan's displayed public score is 59.2 points higher than Shepherd's (2093.9 vs 2034.7), but they are dynamic cumulative ratings across different public match histories (125 vs 284 episodes)[36], not a matched head-to-head. The live public leaderboard places team Aleix López at rank 1351 out of 10004 teams (score gap 153.8 and rank gap 351 to rank 1000).[25] The episodes endpoint does not establish opponent identities or outcomes. No submission was made during this documentation refresh.)*

For comprehensive architectural breakdowns, game-engine physics, and empirical A/B test findings, see:
* **P0 Public Replay Parity Report:** [`docs/experiments/public_replay_parity_2026-09-25.md`](docs/experiments/public_replay_parity_2026-09-25.md)
* **P1 Refresh Selection Report:** [`docs/experiments/agent_selection/p1_refresh_2026-09-25/report.md`](docs/experiments/agent_selection/p1_refresh_2026-09-25/report.md)
* **P2 Market Slot Ordering Report:** [`docs/experiments/agent_selection/p2_market_slot_ordering/report.md`](docs/experiments/agent_selection/p2_market_slot_ordering/report.md)
* **Public Research & Medal Backlog:** [`docs/plans/kaggriculture-public-research-backlog-2026-09-25.md`](docs/plans/kaggriculture-public-research-backlog-2026-09-25.md)
* **Continuation Win-Path Handoff (2026-09-27):** [`docs/plans/kaggriculture-win-path-handoff-2026-09-27.md`](docs/plans/kaggriculture-win-path-handoff-2026-09-27.md)
* **Master Retrospective:** [`docs/kaggriculture_master_retrospective_2026_09_23.md`](docs/kaggriculture_master_retrospective_2026_09_23.md)
* **SOTA Tournament Report:** [`docs/competitor_tournament_results_2026_09_23.md`](docs/competitor_tournament_results_2026_09_23.md)
* **Empirical A/B Test Findings:** [`docs/research_update_2026_09_23.md`](docs/research_update_2026_09_23.md)
* **Experiment Version Ledger:** [`docs/experiments.md`](docs/experiments.md)

## Sources

[1] https://www.kaggle.com/competitions/kaggriculture/overview/evaluation
[25] https://www.kaggle.com/competitions/kaggriculture/leaderboard
[36] https://www.kaggle.com/competitions/kaggriculture/submissions
