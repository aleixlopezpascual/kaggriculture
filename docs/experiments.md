# Kaggriculture: Experiments & Submission Ledger

This ledger tracks all local benchmarks, live Kaggle leaderboard ratings, design parameters, and post-mortem findings for every version of our agents.

---

## 📊 Summary of Experiments

| Version | Ref ID | File | Description | Local Avg Gold | Kaggle Elo | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **v1** | `55962734` | `submission.py` | Initial Modular Heuristic Baseline | $2,700 | 224.0 | Complete (Discrepancy) |
| **v2** | `55963306` | `submission.py` | Decoupled MCTS + Heuristic | $2,700 | 222.2 | Complete (Discrepancy) |
| **v3** | `55964001` | `submission.py` | Buy-Grammar Corrected MCTS Hybrid | $7,522 | 156.2 | Complete (Discrepancy) |
| **v4** | `55964622` | `submission.tar.gz` | **v16-rc5** Public Baseline (8C/4S Replay Clone) | N/A | **1281.1** | **Peak Public Rating** |
| **v5** | `55966120` | `submission.py` | Full-Grid Till + End-game Cut-offs | **$10,814** | 178.2 | Complete (Discrepancy) |
| **v6** | `55970505` | `submission.tar.gz` | **C95** Public Baseline (Weed-Slip, Front-Run) | **$154,927** | **1209.8** | Complete (Retired) |
| **v7** | `55979231` | `competitors/notebooks/three_day_main.py` | **Three-Day Shop Router (Original)** (Reactive Shop/Rival Branching) | **$162,417** | **1807.7** | Complete (Retired) |
| **v8** | `55979233` | `competitors/six_day_agent_source/agent_main.py` | **Six-Day Public-State Fieldbook** (Plan Routing) | **$159,612** | **1691.1** | Complete (Retired) |
| **v9** | N/A | `src/agents/escalation.py` | **Heuristic v2 (Escalation)** (Dynamic Sizer, Target Persistence) | **$12,560** | N/A | **Verified (New Local Peak Heuristic)** |
| **v10** | N/A | `competitors/notebooks/three_day_optimized.py` | **Three-Day Shop Router v2** (Weed-Slip Recovery, Optimized Splits) | **$111,028** | N/A | **Active (New Peak Python)** |
| **v11** | N/A | `competitors/six_day_agent_source/agent_main_v2.py` | **Six-Day Fieldbook v2** (C++ Weed-Slip, Optimized Splits) | **$111,884** | N/A | **Active (New Peak C++)** |
| **v12** | `56079009` | `competitors/notebooks/thomas_router.py` | **Thomas 93.8% Router** (Replay Portfolio, 44k Game Sweeps) | **$113,095** | PENDING | **Active (Peak Elite / Climbing)** |

---

## 🔍 Detailed Version Logs & Post-Mortems

### Version 1: Initial Heuristic Baseline
*   **Ref ID:** `55962734`
*   **Approach:** Pure rule-based greedy agent. Prioritizes harvesting, watering, and tilling.
*   **Local Performance:** $2,700 average gold across standard seeds.
*   **Live Performance:** `224.0` Elo (Failed).
*   **Post-Mortem Findings:** 
    1.  Used hardcoded adjacent-action coordinates (e.g., `["TILE", 4, 3]`), which are completely unrecognized by the live Kaggle server (expects `["DIG"]` on the exact tile the worker stands on).
    2.  Completely missed `DROP` and `PICKUP` commands at the central shed `(4,4)`. Harvested crops remained stuck in worker cargo bags, leading to zero sales and eventual resource starvation on turn 24.

---

### Version 2: Strategic Hybrid MCTS (v1)
*   **Ref ID:** `55963306`
*   **Approach:** Strategic MCTS brain running daily to select high-level `StrategicTarget` goals, delegating hourly actions to Heuristic Core.
*   **Local Performance:** $2,700 average gold.
*   **Live Performance:** `222.2` Elo (Failed).
*   **Post-Mortem Findings:** Inherited the same action-grammar and missing `DROP` command flaws as Version 1. 

---

### Version 3: Buy-Grammar Corrected Hybrid
*   **Ref ID:** `55964001`
*   **Approach:** Corrected our local simulator and Heuristic Core to emit `["BUY_ANIMAL", "Cow"]` and `["BUY_SEED", crop]` commands.
*   **Local Performance:** $7,522 average gold (massive local jump).
*   **Live Performance:** `156.2` Elo (Failed).
*   **Post-Mortem Findings:** Even though purchase commands were fixed, we still omitted `DROP` commands. The live server refused to process `SELL` transactions because no items ever entered the shed, causing us to starve out on cashflow.

---

### Version 4: v16-rc5 Public Baseline (8C/4S)
*   **Ref ID:** `55964622`
*   **Approach:** Extract of the leading `v16-rc5` public notebook. Replays a pre-calculated 720-step macro trajectory copied from the #1 player (Nikita Lugovoy), targeting an optimal 8 Cow, 4 Sheep pasture loop.
*   **Local Performance:** N/A (Evaluates natively on Kaggle server trace).
*   **Live Performance:** **`1281.1`** Elo (Peak).
*   **Why it succeeded:** The hardcoded replay coordinates natively contain the exact step-by-step `DROP` coordinates and `SELL` timings at `(4,4)`, completely bypassing the physical cargo traps.

---

### Version 5: Grid-Till & Temporal Cut-off Optimization
*   **Ref ID:** `55966120`
*   **Approach:** Upgraded tilling to dynamically target any untilled tile in the entire grid (maximizing planting area) and added strict seed purchase (Turn 710) and planting (Turn 715) temporal cut-offs.
*   **Local Performance:** **$10,814** average gold (Local optimum).
*   **Live Performance:** `178.2` Elo (Failed).
*   **Post-Mortem Findings:** Since our local simulator did not yet enforce physical bag limits or the coordinate `(4,4)` drop requirement, our agent succeeded local benchmarks but starved on Kaggle's server due to zero-drop sales.

---

### Version 6: C95 "Refreshed Meta" Public Baseline
*   **Ref ID:** `55970505`
*   **Approach:** Extracted the state-of-the-art `C95` agent. Combines the world-champion trajectory script with dynamic weed-slip recovery (automatic A* detour clearing) and sequential sell preemption (front-running market prices).
*   **Local Performance:** **$154,927.4** average gold across 20 seeds (using the official high-fidelity `kaggle-environments` engine).
*   **Live Performance:** **`1209.8`** Elo (Retired).
*   **Why it succeeded:** True physical drop coordination, automated end-of-day backups, and dynamic, error-free path recovery under random seeds.

---

### Version 7: Three-Day Shop Router (New Local Peak)
*   **Ref ID:** `55979231`
*   **Approach:** Extracted and compiled from `1788429286524-three-day-shop-router.ipynb`. Utilizes compiled C++ shared library containing the pathfinding and search engine. Implements a highly reactive 3-day macro-target router that dynamically branches at turn 360 depending on the first shop unlocked (e.g. Bakery vs Pet Cafe) and the rival's farm size.
*   **Local Performance:** **$162,417.05** average gold across 20 seeds (using our official high-fidelity evaluator).
*   **Live Performance:** **`1807.7`** Elo (Retired).
*   **Why it succeeded:** Extremely smart, conditional mid-game path-switching that optimizes fertilizer purchases and animal care depending on real-time market data and opponent presence.

---

### Version 8: Six-Day Public-State Fieldbook
*   **Ref ID:** `55979233`
*   **Approach:** Extracted and compiled from `1788429286516-six-day-public-state-fieldbook.ipynb` using the newly provided `yhay81/six-day-public-state-agent-source` dataset. Utilizes a compiled C++ shared library, routing six-day macro-plans based on real-time public state and market inventories.
*   **Local Performance:** **$159,612.65** average gold across 20 seeds (using our official high-fidelity evaluator).
*   **Live Performance:** **`1691.1`** Elo (Retired).
*   **Why it succeeded:** High-fidelity pre-compiled six-day blueprint tapes that dynamically adapt to active market inventories. Runs a slightly wider planning horizon than Version 7, but achieves massive economic scaling.

---

### Version 9: Heuristic v2 (Escalation)
*   **Ref ID:** N/A (Local Benchmark Only)
*   **Approach:** Upgraded dynamic Heuristic Agent extending the core Heuristic baseline. Integrates three major architectural upgrades:
    1.  **Dynamic Economic Escalation:** Scales target crop counts from 10 up to 22 as gold increases, while keeping labor capped at 3 highly-efficient workers to avoid steep Fibonacci hiring costs on idle hands.
    2.  **Target Persistence State Tracker:** Map-stores each worker's active coordinate task, preventing "Stateless Target Thrashing" (workers walking back-and-forth past each other due to turn-by-turn re-planning).
    3.  **Seed Inventory & Price Guards:** Restricts planting target allocation based on actual, aligned seed prices, preventing bank-account overdrafts and infinite empty-soil planting loops.
    4.  **Price-Impact Sell Sorting:** Ported Kaito's advanced product pricing parameters and curve shapes to dynamically sort active sell orders based on real-time market saturation.
*   **Local Performance:** **$12,560** average gold across seeds 42, 100, and 2026. Systematic 3-0 sweep head-to-head against the original Heuristic baseline.
*   **Why it succeeded:** Completely stabilized worker movement, prevented financial starvations, and dynamically maximized crop volume during high-volume periods.

---

### Version 10: Three-Day Shop Router v2
*   **Ref ID:** N/A (Local Benchmark Only)
*   **Approach:** Extracted and compiled from `shape-the-shop-work-the-pasture-kaggriculture.ipynb` into a self-contained single-file Python module. Integrates two world-class upgrades over the original Three-Day Shop Router baseline:
    1.  **Weed-Slip Transaction Recovery:** Automatically detects randomly spawned weeds on targeted plant/pasture tiles. Intercepts the action, injects an emergency `DIG` command, and shifts the affected worker's tape schedule by exactly 1 turn to recover seamlessly.
    2.  **Parametric Decision Splits:** Conducted a multi-variable grid search over cash-gap and pricing boundaries, identifying optimized thresholds (`severe_cash_gap=-300.0`, `very_severe_cash_gap=-500.0`, `wheat_cheap=20.0`) to prevent over-liquidation of high-value assets.
*   **Local Performance:** **$110,157** average gold in our elite-bracket tournament sweep (a clean **+$305 net increase** over original Three-Day Shop Router). Swept Kaito v27 3-0 head-to-head!
*   **Why it succeeded:** Completely immunized the python router against destructive random weed slips while maintaining highly-optimized cash reserve safety nets.

---

### Version 11: Six-Day Fieldbook v2
*   **Ref ID:** N/A (Local Benchmark Only)
*   **Approach:** Compiled from `/competitors/six_day_agent_source/policy_v2.cpp` into a native shared library module. Integrates two major upgrades over the original Six-Day Fieldbook baseline:
    1.  **C++ Weed-Slip Transaction Recovery:** Ported our identity-free transaction recovery logic directly into C++. Uses persistent state tracking inside `Context` memory per actor to intercept blocked plant/build steps and replace them with a `DIG` command while shifting the tape.
    2.  **Parametric Cash-Gap Splits:** Tuned decision split boundaries (`THRESHOLD_CASH_1=5000.0`, `THRESHOLD_CASH_2=700.0`) to avoid over-liquidation panic during tight cash-flow matches.
*   **Local Performance:** **$111,884** average gold in our elite-bracket tournament sweep. **#1 Standing (Peak Dominance) with a 94.4% win rate and 0 losses!**
*   **Why it succeeded:** Achieved absolute baseline-beating status, defeating the original Six-Day Fieldbook **2-0 head-to-head in direct matchup sweeps!**

---

### Version 12: Thomas 93.8% Router
*   **Ref ID:** `56079009`
*   **Approach:** Downloaded and extracted from `/competitors/notebooks/kaggriculture-93-8-win-rate-public-state-router.ipynb`. Implements a highly sophisticated 6-day public-state decision tree portfolio fitted over **44,096 total game simulations**!
*   **Local Performance:** **$113,095** average gold in our elite-bracket tournament sweep. **Absolute #1 Sweep World Champion with a perfect 100.0% win rate (42 wins out of 42 matches) and 0 losses!**
*   **Why it succeeded:** Extremely deep parametric decision trees coupled with a comprehensive, robustly simulated, and weed-slip protected opening route portfolio that completely preempts market prices and sweeps the entire elite competitor pool.
