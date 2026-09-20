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
| **v12** | `56079009` | `competitors/notebooks/thomas_router.py` | **Thomas 93.8% Router** (Replay Portfolio, 44k Game Sweeps) | **$162,733** | **1791.4** | Complete (Retired) |
| **v13** | `56079889` | `competitors/notebooks/lynn_router.py` | **Lynn Mathematical Router** (Mathematical Farming-Score, One-Slot Reserve) | **$157,561** | **1696.2** | Complete (Retired) |
| **v14** | N/A | `competitors/notebooks/kaito_v21_router.py` | **Kaito v21.1 Router** (Conditional Memory Router, 30 matches) | **$56,178** | N/A | **Decayed (Inefficient)** |
| **v15** | `56194677` | `competitors/notebooks/fusion_router.py` | **EXP-173 Super-Fusion Router** (Fuses Thomas + Yusuke + Dmitrii + Aurax7) | **$172,897** | **2166.4** | Complete (Retired) |
| **v16** | `56194679` | `competitors/notebooks/tetsu_smart_router/main.py` | **Tetsu Market-Smart Router** (4-Action Sale Reservation Router) | **$166,996** | **1885.2** | Complete (Retired) |
| **v17** | `56229360` | `competitors/notebooks/v36_fusion_router.py` | **EXP-173 v36 Fusion Router** (Guarded Four-Turn Sales Router) | **$172,897** | **1969.3** | Complete (Retired) |
| **v18** | `56276799` | `competitors/notebooks/v45_fusion_router.py` | **EXP-173 v45 Fusion Router** (First-Turn Wheat Round Trip) | **$172,897** | **1942.8** | Complete (Retired) |
| **v19** | `56276801` | `competitors/notebooks/reyhan_dynamic_router.py` | **Reyhan Dynamic Route Agent** (Dynamic 6-Day Decision Forest) | $172,897 | **2071.6** | **Active (Peak Elite / Climbing)** |
| **v20** | `56301961` | `competitors/notebooks/jaxa_2802_router/main.py` | **Jaxa 2802 Elo Router** (128/128 Worlds Multi-World Router) | $161,858 | **2212.6** | **Active (Peak Elite / Climbing)** |
| **v21** | N/A | `competitors/notebooks/v48_main.py` | **Jaxa V48 Clear-Queue** (2-Turn Advance, Horizon 24) | $76,436 | N/A | **Decayed (Inefficient)** |

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
*   **Local Performance:** **$162,733** average gold in solo-runs against Random (our highest ever recorded!). In our head-to-head elite-bracket tournament matchups, it scored **$113,095** average gold, achieving absolute **#1 Standings with a perfect 100.0% win rate (42 wins, 0 losses) and 0 losses!**
*   **Live Performance:** **`1791.4`** Elo (Active - Peak Climbing).
*   **Why it succeeded:** Extremely deep parametric decision trees coupled with a comprehensive, robustly simulated, and weed-slip protected opening route portfolio that completely preempts market prices and sweeps the entire elite competitor pool.

---

### Version 13: Lynn Mathematical Router
*   **Ref ID:** `56079889`
*   **Approach:** Downloaded and extracted from `/competitors/notebooks/farming-score-a-mathematical-approach.ipynb`. Integrates long-route tapes with a highly advanced value-aware one-slot inventory capacity reserve. Prefers protecting the shed at day close and dynamically front-loading sales without changing overall quantities.
*   **Local Performance:** **$157,561** average gold in solo-runs against Random. In our head-to-head elite-bracket tournament matchups, it scored **$80,050** average gold, securing the **#2 Standing in the entire tournament with an outstanding 81.5% win rate (44 wins, 10 losses)!**
*   **Live Performance:** **`1696.2`** Elo (Active - Peak Climbing).
*   **Why it succeeded:** Exceptional competitive defense! Swept both our optimized `Six-Day Fieldbook v2` and original `Six-Day Fieldbook` **3W-0L-0T (100% win rate) head-to-head**! It prevents resource starvations by keeping exact mathematical capacities reserved.

---

### Version 14: Kaito v21.1 Router
*   **Ref ID:** N/A (Local Benchmark Only)
*   **Approach:** Downloaded and extracted from `/competitors/notebooks/177-180-fresh-top-30-v21-1-conditional-memory.ipynb`. Integrates 30 public route memories using nearest public-farm matches at current steps.
*   **Local Performance:** **$56,178** average gold in our head-to-head tournament matches. Ended near the bottom of the standings with an **11.1% win rate (6 wins, 48 losses)**.
*   **Why it failed:** Severe route decay! Its embedded opening public-state trajectories have completely decayed and lost their edge as the global elite bracket meta moved.

---

### Version 15: EXP-173 Super-Fusion Router
*   **Ref ID:** `56194677`
*   **Approach:** Downloaded and extracted from `/competitors/notebooks/kaggriculture-most-powerfull-route.ipynb`. Fuses Thomas's public-state decision trees, Yusuke's shop-router-0909 action tapes, Dmitrii's physical terminal rescue, and Aurax7's day-end storage guard.
*   **Local Performance:** **$172,897** average gold in solo-runs against Random (our new absolute repository record!). In our head-to-head tournament matchups, it scored **$85,338** average gold, claiming the **#2 Spot with a magnificent 93.9% win rate (62 wins, 4 losses)!**
*   **Live Performance:** **`2166.4`** Elo (Retired).
*   **Why it succeeded:** Incredible synergy! By combining all public meta advances into a single agent, it completely dominated other individual public agents head-to-head.

---

### Version 16: Tetsu Market-Smart Router
*   **Ref ID:** `56194679`
*   **Approach:** Reconstructed and unpacked from `/competitors/notebooks/market-smart-farming-kaggriculture.ipynb`. Implements a highly robust 4-action sale reservation system that precisely guards market drop timings.
*   **Local Performance:** **$166,996** average gold in solo-runs against Random. In our head-to-head tournament matchups, it scored **$85,263** average gold, claiming the **#1 Absolute Standings Position with an unmatched 97.0% win rate (64 wins, 2 losses)!**
*   **Live Performance:** **`2162.4`** Elo (Retired).
*   **Why it succeeded:** Perfect economic defense! It completely prevents market pricing collapses and swept Thomas's Router **3W-0L-0T (100%) head-to-head**!

---

### Version 17: EXP-173 v36 Fusion Router
*   **Ref ID:** `56229360`
*   **Approach:** Downloaded and extracted from `/competitors/notebooks/kaggriculture-v36-guarded-four-turn-sales.ipynb`. Integrates Ahmed's brand-new, optimized v36 Guarded Four-Turn Sales sequence.
*   **Local Performance:** **$172,897** average gold in solo-runs against Random. In our head-to-head elite-bracket tournament matchups, it scored **$84,588** average gold, achieving the **uncontested #1 standing with a perfect 100.0% win rate (72 wins, 0 losses) and 0 losses!**
*   **Live Performance:** **`1969.3`** Elo (Retired).
*   **Why it succeeded:** Strictly superior guarded sale timings. Completely swept Tetsu's Market-Smart Router **3W-0L-0T (100% win rate) head-to-head**!

---

### Version 18: EXP-173 v45 Fusion Router
*   **Ref ID:** `56276799`
*   **Approach:** Downloaded and extracted from `/competitors/notebooks/kaggriculture-v45-first-turn-wheat-round-trip.ipynb`. Fuses atomic openings (Rayk opening assignment) with earlier reservation activation adapted from aurax7 Reactive V5.
*   **Local Performance:** **$172,897** average gold in solo-runs against Random. In our head-to-head elite-bracket tournament matchups, it scored **$87,344** average gold, achieving **Joint #1 Undefeated Standings with an 87.5% win rate (42 wins, 0 losses, 6 ties) and 0 losses!**
*   **Live Performance:** **`1942.8`** Elo (Retired).
*   **Why it succeeded:** Phenomenal opening-move trade optimization. Completely swept the previous v36 fusion router **3W-0L-0T (100%) head-to-head**!

---

### Version 19: Reyhan Dynamic Route Agent
*   **Ref ID:** `56276801`
*   **Approach:** Downloaded and extracted from `/competitors/notebooks/kaggriculture-dynamic-route-agent.ipynb`. Implements a slightly shifted, highly robust 6-day public-state decision forest.
*   **Local Performance:** **$172,897** average gold in solo-runs against Random. In our head-to-head elite-bracket tournament matchups, it scored **$87,344** average gold, achieving **Joint #1 Undefeated Standings with an 87.5% win rate (42 wins, 0 losses, 6 ties) and 0 losses!**
*   **Live Performance:** **`2071.6`** Elo (Active - Peak Climbing).
*   **Why it succeeded:** Highly synergistic other-branch decision structures. Identical undefeated performance, completely tying with the v45 agent (0W-0L-3T head-to-head self-play ties).

---

### Version 20: Jaxa 2802 Elo Router
*   **Ref ID:** `56301961`
*   **Approach:** Downloaded and unpacked from `/competitors/notebooks/2802-two-identical-agents-90-points-apart.ipynb`. Implements a highly advanced 128/128 world multi-world predictive routing forest.
*   **Local Performance:** **$161,858** average gold in solo-runs against Random. In our head-to-head elite-bracket tournament matchups, it scored **$82,185** average gold, achieving the **uncontested #1 standing with a perfect 100.0% win rate (54 wins, 0 losses) and 0 losses!**
*   **Live Performance:** **`2212.6`** Elo (Active - Peak Climbing).
*   **Why it succeeded:** Superior decision forest accuracy. Completely swept both of our previously undefeated joint champions (**v45** and **Reyhan**) **3W-0L-0T (100% win rate) head-to-head!**

---

### Version 21: Jaxa V48 Clear-Queue
*   **Ref ID:** N/A (Local Benchmark Only)
*   **Approach:** Unpacked and decoded from `40-40-early-floor-39-46-top-10-v48-fast-routes.ipynb`. Implements a two-turn sale advance of pure cash products, a strict 24-turn optimal reservation horizon, and a 10-unit Step-0 Wheat Round Trip.
*   **Local Performance:** **$76,436** average gold in head-to-head matchups against `Jaxa 2802 Elo Router` (securing a **0% win rate (0 wins, 10 losses)**), and **$75,608** average gold against `EXP-173 v45 Fusion Router` (securing a **0% win rate (0 wins, 6 losses)**).
*   **Why it failed:** Severe market decay! Proactively advancing cash product sales by two turns chokes compound animal resource scaling and starves the Day 3 seed budget under our high-fidelity tournament engine. `Jaxa 2802` remains our undisputed peak climbing agent.

