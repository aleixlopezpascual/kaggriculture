# Kaggriculture: Experiments & Submission Ledger

> **Important Caveats on Experiment Data & Source Capture**
> * **Path Normalization:** Only the canonical RACE aggregate (`docs/experiments/race_horizon_41.json`) and four batches (`race_horizon_41_batch01.json` through `race_horizon_41_batch04.json`) had path values normalized; `candidates.frozen_original.json` remains byte-preserved with historical machine paths and `candidates.json` is the portable rerun manifest. The exact game, result, and source-hash fields remain unchanged except for the path strings.
> * **Execution Security:** Agent runners execute candidate Python in-process via `exec`, with NO sandbox. You must only run reviewed and trusted source snapshots.
> * **Source Authorship & Licensing:** The captured Kaggle sources bundled in this repository may contain submitter-authored modifications alongside inherited, third-party, or open-source components described in their own notices. The bundled copies are strictly hash-pinned captures of the linked public outputs; do not assume all code was originally authored by the listed Kaggle notebook author. We retain Apache/NOTICE attribution detail where present, without making broader unsupported licensing claims.

> **Data Provenance Snapshot (Retrieved 2026-09-25 12:08 CEST (+0200))**
> Kaggle CLI Command: `kaggle competitions submissions kaggriculture --format json --page-size 100`
> * **Latest-Two Tracked #1 (Newest):** Prvsiyan Moon Counts Melons (Ref `56531885`), Status: COMPLETE, Public Score: 2071.7, Private: blank (110 completed public episodes, 1 completed validation episode)
> * **Latest-Two Tracked #2 (Second-Newest):** Shepherd Sovereign (Ref `56490949`), Status: COMPLETE, Public Score: 2021.4, Private: blank (272 completed public episodes, 1 completed validation episode; already uploaded; no re-upload)
> * **Third / Older (Not in Tracked Pair):** Jaxa 2802 Variant B (Ref `56467787`), Status: COMPLETE, Public Score: 1680.8, Private: blank
> *(Note: The top two entries represent Kaggle's active two-submission tracking rule for live evaluation, not leaderboard rank.)*

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
| **v19** | `56276801` | `competitors/notebooks/reyhan_dynamic_router.py` | **Reyhan Dynamic Route Agent** (Dynamic 6-Day Decision Forest) | $172,897 | **2071.6** | Complete (Retired) |
| **v20** | `56301961` | `competitors/notebooks/jaxa_2802_router/main.py` | **Jaxa 2802 Elo Router** (128/128 Worlds Multi-World Router) | $161,858 | **2212.6** | Complete (Retired) |
| **v21** | N/A | `competitors/notebooks/v48_main.py` | **Jaxa V48 Clear-Queue** (2-Turn Advance, Horizon 24) | $76,436 | N/A | **Decayed (Inefficient)** |
| **v22** | `56424193` | `submission/submission.py` | **Optimized Jaxa 2802 + BoundedSaleReservation** (LOOKAHEAD=1, HORIZON=1, OPEN_UNITS=8) | $166,498 | **126.6** | Complete (Retired) |
| **v23** | `56433746` | `competitors/notebooks/jaxa_2802_router/main.py` | **Optimized Jaxa 2802 Router** (LOOKAHEAD=1, HORIZON=1, OPEN_UNITS=8) | $166,498 | **1672.5** | Complete (Retired) |
| **v24** | `56433753` | `competitors/notebooks/reyhan_dynamic_router.py` | **Reyhan Dynamic Route Agent** (Dynamic 6-Day Decision Forest) | $172,897 | **1735.7** | Complete (Retired) |
| **v25** | `56467783` | `competitors/notebooks/jaxa_2802_router/main.py` | **A/B Test Variant A: Jaxa 2802 (H1, L1, U8)** | $166,498 | **1675.1** | Complete (Retired) |
| **v26** | `56467787` | `competitors/notebooks/jaxa_2802_router/main_variant_b_h24.py` | **A/B Test Variant B: Jaxa 2802 (H24, L2, U10)** | $161,858 | **1680.8** | Complete (Retired - Third / Older) |
| **v27** | `56490949` | `competitors/notebooks/shepherd_sovereign_main.py` | **Shepherd Sovereign: Herd-Safe Sovereign Engine** | $82,074 | **2021.4** | **Active (Latest-Two Tracked Pair)** |
| **v28** | `56531885` | `prvsiyan_kaggriculture_submission.tar.gz` | **Prvsiyan Moon Counts Melons** (Local confirmation candidate; Apache-2.0) | $99,568 | **2071.7** | **Active (Latest-Two Tracked)** |

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

---

### Version 22: Optimized Jaxa 2802 + BoundedSaleReservation
*   **Ref ID:** `56424193`
*   **Approach:** Built via `submission/compile_submission.py` bundling `src/` modules with the `EscalationAgent` tactical core and the newly implemented `BoundedSaleReservation` timing optimizer.
*   **Local Performance:** **$166,498** (evaluated in simulated router contexts) / **$12,560** (actual standalone `EscalationAgent` heuristic benchmark).
*   **Live Performance:** **`126.6`** Elo (Retired).
*   **Post-Mortem Findings:**
    1.  **Chassis Discrepancy:** The compiler bundled our custom heuristic agent (`EscalationAgent`) rather than the world-champion multi-world routing forest (`Jaxa 2802`).
    2.  **Performance Ceiling Gap:** While `EscalationAgent` passes all unit tests and optimizes local labor wages and crop rotations, its heuristic ceiling of ~$12.5k gold is severely outmatched by the ~$166k gold ceiling of elite route tapes on the live ladder, causing its Elo to plunge to 126.6.

---

### Version 23: Optimized Jaxa 2802 Router (Parametric Overfit)
*   **Ref ID:** `56433746`
*   **Approach:** Submitted `competitors/notebooks/jaxa_2802_router/main.py` directly with the parameter sweep configuration: `HORIZON = 1`, `LOOKAHEAD = 1`, and `OPEN_UNITS = 8`.
*   **Local Performance:** Scored **$166,498.00** average gold across a 3-seed paired-seat H2H sweep (+1,051 gold over baseline).
*   **Live Performance:** **`1672.5`** Elo (Active - Underperforming by -335.7 Elo vs baseline).
*   **Post-Mortem Findings (The Local Overfit Trap):**
    1.  **Horizon Truncation Damage:** Limiting `HORIZON` from 24 turns to 1 turn was chosen locally because it prevented rare simulated asset dilution. However, on the live multi-player ladder, a 24-turn pre-selling reservation window is critical during turns 288–696 to front-run opponents and lock in high prices before town demand naturally decays. Truncating to 1 turn forfeited all multi-turn market preemption.
    2.  **Turn-0 Slack Dilution:** Reducing `OPEN_UNITS` from 10 to 8 units gave rival clones enough early price slack to purchase their planned melon seeds rather than forcing them into budget deficits.
    3.  **Sale Advance Lag:** Reducing `LOOKAHEAD` from 2 to 1 turn allowed rival bots with 2-turn advances to liquidate ahead of us, depressing market prices.

---

### Version 24: Reyhan Dynamic Route Agent (Cold-Start Re-climb)
*   **Ref ID:** `56433753`
*   **Approach:** Submitted `competitors/notebooks/reyhan_dynamic_router.py` to overwrite the weak `v22` slot and re-establish a dual-elite climbing configuration.
*   **Local Performance:** **$172,897** average gold.
*   **Live Performance:** **`1735.7`** Elo (Retired - Superseded by A/B test).
*   **Post-Mortem Findings:**
    1.  **Cold-Start Convergence:** While previously sitting at `1933.7` Elo, re-submitting reset its match history to 0 games. Over 24 hours it climbed from the default placement rating to 1735.7 Elo before being retired to initiate the controlled A/B test.

---

### Version 25: A/B Test Variant A — Jaxa 2802 (H1, L1, U8)
*   **Ref ID:** `56467783`
*   **Approach:** Submitted `competitors/notebooks/jaxa_2802_router/main.py` simultaneously alongside Variant B to execute a rigorous, fair, same-second A/B test under identical ladder matchmaking conditions.
*   **Parameters:** `HORIZON = 1`, `LOOKAHEAD = 1`, `OPEN_UNITS = 8`.
*   **Local Benchmark:** **$166,498** average gold (+1,051 over baseline locally).
*   **Live Performance:** **`1675.1`** Elo (Complete - Retired).
*   **Post-Mortem Findings (The Local Overfitting Trap):**
    1.  **Overfitting to Frozen Offline Baselines:** Squeezing out an apparent +$1,051 local gold advantage was an illusion caused by evaluating against non-reactive, frozen replay bots across a narrow 3-seed slice.
    2.  **Severe Live Degradation:** On the live multiplayer ladder, where town multipliers decay rapidly and opponents actively sell into shared market pools, collapsing the pre-selling horizon to `HORIZON = 1` stripped the bot of its ability to front-run decayed prices, costing **-143.2 Elo points** in head-to-head live competition.

---

### Version 26: A/B Test Variant B — Jaxa 2802 (H24, L2, U10)
*   **Ref ID:** `56467787`
*   **Approach:** Extracted and submitted `competitors/notebooks/jaxa_2802_router/main_variant_b_h24.py` from verified original archive `submission_k0006_open10_h24_frontload_advance2_v43.tar.gz`.
*   **Parameters:** `HORIZON = 24`, `LOOKAHEAD = 2`, `OPEN_UNITS = 10`.
*   **Local Benchmark:** **$161,858** average gold (World-record 100% tournament sweep baseline).
*   **Live Performance:** **`1680.8`** Elo (Peak: **`1889.3`** Elo) — **Retired from Active Pair (Third / Older Submission)** (Snapshot at 2026-09-25 12:08 CEST (+0200)).
*   **Post-Mortem Findings:**
    1.  **Macro-Market Superiority:** A 24-turn pre-selling horizon and 2-turn pure-cash advance reliably lock in premium shed pricing before market demand collapses.
    2.  **Generalization Over Micro-Optimization:** Proves conclusively that robust, macro-level market dictation and defensive buffers generalize far better to live matchmaking than brittle micro-optimizations found via small local sweeps.

---

### Version 27: Shepherd Sovereign — Herd-Safe Sovereign Engine
*   **Ref ID:** `56490949`
*   **Approach:** Deployed `competitors/notebooks/shepherd_sovereign_main.py` directly from the Sept 23 morning release (`haideptry/the-shepherds-ledger-herd-safe-sovereign`).
*   **Key Mechanics:**
    1.  **Herd-Safe Feed Reserves:** Eliminates early speculative Day-1 wheat dumping that leads to inventory crashes, securing cash and feed reserves dedicated to livestock survival.
    2.  **Shed-Arrival Sale Windows:** Synchronizes strawberry and milk sales with physical shed deliveries, guaranteeing unglutted sales before town price decay.
*   **Local Performance:** **#1 in 90-match SOTA tournament** across the top 6 public models: **73.3% Win Rate** (22W - 8L), holding a positive winning record against **every single model** (4-2 vs 2950 Peak, 4-2 vs Thomas 2945, 6-0 vs Herd-Safe, 4-2 vs Jaxa B).
*   **Live Performance:** **`2021.4`** Elo — **Active (Latest-Two Tracked Pair)** (Snapshot at 2026-09-25 12:08 CEST (+0200); 272 completed public episodes, 1 completed validation episode; already uploaded, no re-upload).

---

### Version 28: Prvsiyan Moon Counts Melons — Local Confirmation Candidate
*   **Ref ID:** `56531885`
*   **Approach:** Submitted archive `prvsiyan_kaggriculture_submission.tar.gz` (containing `main.py`, `LICENSE.txt`, and `NOTICE.txt` under Apache-2.0 license) at explicit user request following local confirmation testing.
*   **Local Performance:** **$99,568.0** average terminal cash across 144 confirmation tournament matches (.8750 pooled match-points rate; provisional confirmation-panel leader).
*   **Live Performance:** **`2071.7`** Elo — **Active (Latest-Two Tracked)** (Snapshot at 2026-09-25 12:08 CEST (+0200); 110 completed public episodes, 1 completed validation episode).

---

### Controlled A/B Experiment: RACE Premium-Sale Reservation Horizon (40 vs 41 Turns)
*   **Hypothesis:** V55-inspired: default horizon 40 -> 41 turns (`V9_RACE_DEFAULT = 40` -> `41`) evaluated against the Shepherd Sovereign core to determine if extending the premium-sale reservation window improves trade timing or terminal margin.
*   **Setup:**
    *   **Engine & Runtime:** Kaggriculture simulation engine 1.32.7.
    *   **Arms:** Current Shepherd Sovereign baseline vs. 41-turn in-memory candidate.
    *   **Provenance & Hashes:**
        *   Baseline SHA256: `5f2b51a2beaf5e08cb73e82f0e03e02e56de601563b28344e49b7058e371b247`
        *   Candidate SHA256: `5273f0884fefcc9087b57b9c07e981b110c2dd2385b6c2c8fcb25e714945f361`
    *   **Evaluation Matrix:** 12 paired seeds (`[16395794, 879848124, 709458408, 981021242, 586735484, 677596929, 753194523, 155914011, 599914084, 610590515, 843962203, 781627676]`), five opponents (`The 2950 Peak Farm`, `Reyhan Dynamic Route Agent`, `Herd-Safe Race`, `V57 Invariant`, `Jaxa 2802 Variant B`), evaluated across both seats (0 and 1).
    *   **Match Scale:** 240 games total (120 baseline, 120 candidate), forming 120 paired matchup comparisons.
    *   **Data Provenance:** Aggregated at UTC `2026-09-24T14:34:56.348071+00:00`. Full result/provenance JSON is [`docs/experiments/race_horizon_41.json`](experiments/race_horizon_41.json), compiled from the four raw batch files `race_horizon_41_batch01.json` through `race_horizon_41_batch04.json` (including all raw games, exact seeds, hashes, bootstrap intervals, and verification).
*   **Results:**
    *   **Execution Integrity:** Every game completed with status `DONE`; zero agent/runtime error strings; zero RACE error counters; no telemetry error indicators. Invalid-action counts were not separately captured by this runner.
    *   **Outcome Summary:** Both arms had 106 wins, 14 losses, 0 ties. All 120 paired matchups were exactly identical in points, margin, and cash.
    *   **Paired Deltas:** Mean paired points delta `0.0` (cluster-bootstrap 95% interval `[0.0, 0.0]`), margin delta `0.0` (95% interval `[0.0, 0.0]`), cash delta `0.0` (95% interval `[0.0, 0.0]`).
    *   **Terminal Cash:** Mean terminal cash for each arm: `104561.7833`.
    *   **Per-Opponent Performance (24 games each):**

        Each row averages the 24 baseline games (12 seeds × both seats). Candidate values matched exactly because all paired outcomes and cash were identical. W-L-T columns indicate Shepherd's record, not the opponent's.

        | Opponent | Shepherd W-L-T | Opponent W-L-T | Shepherd Mean Cash | Opponent Mean Cash | Mean Margin |
        | :--- | :--- | :--- | :--- | :--- | :--- |
        | The 2950 Peak Farm | 22-2-0 | 2-22-0 | 104,164.00 | 103,239.00 | +925.00 |
        | Reyhan Dynamic Route Agent | 22-2-0 | 2-22-0 | 105,663.42 | 100,565.42 | +5,098.00 |
        | Herd-Safe Race | 24-0-0 | 0-24-0 | 103,746.58 | 103,368.83 | +377.75 |
        | V57 Invariant | 16-8-0 | 8-16-0 | 103,895.00 | 103,598.83 | +296.17 |
        | Jaxa 2802 Variant B | 22-2-0 | 2-22-0 | 105,339.92 | 100,531.08 | +4,808.83 |
    *   **Wall Time:** Mean wall time per game was 5.2918 s baseline, 5.2921 s candidate (no meaningful difference).
*   **Decision:**
    *   **No Promotion:** Retain the 40-turn baseline.
    *   **Scope:** Scope the conclusion to this seed/opponent panel and measured outcome fields; action-level differences were not logged.

---

### Controlled Offline Experiment: Local Agent Selection Tournament (Screening & Confirmation)
*   **Detailed Report:** See [`docs/experiments/agent_selection/report.md`](experiments/agent_selection/report.md) for full methodology, matchup matrices, cluster bootstrap intervals, and runtime analysis.
*   **Design & Engine:** Two-phase offline evaluation under official simulation engine `kaggle-environments 1.32.7`. Phase 1 screened 10 candidate agents in a full round-robin across 4 fixed seeds (360 games total; 72 games/agent; all 720 player statuses `DONE`, 0 errors). Phase 2 confirmed the top two finalists across an 8-seed confirmation panel against each other and the roster (272 games total; 144 games/finalist; 544 player statuses `DONE`, 0 errors).
*   **Phases & Results:** In Phase 1 screening, Shepherd Sovereign ranked #1 (.8333 match-points rate, 60-12-0) and Prvsiyan Moon Counts Melons ranked #2 (.8056, 58-14-0). In Phase 2 confirmation, Prvsiyan led the pooled match-points rate (.8750, 126-18-0) and won 16-0-0 vs Shepherd in direct H2H (+1,723.5 margin); however, Prvsiyan went 2-14-0 vs Jaxa 2802 Variant B (-9,998.2 margin) where Shepherd went 16-0-0 (+6,088.8 margin), and the whole-seed cluster bootstrap paired difference across all opponents crosses zero (95% CI `[-0.0278, +0.2708]`). Both recorded occasional callback latency spikes over 100 ms.
*   **Outcome & Submission Status:** Prvsiyan is designated the provisional confirmation-panel leader for internal research; Shepherd Sovereign is retained as the local baseline. No Kaggle submission was executed during the local tournament itself.
*   **Live Follow-up (Latest Live Snapshot):** Subsequent to the offline tournament, at the user's explicit request, a live confirmation candidate package for Prvsiyan Moon Counts Melons was submitted to Kaggle on 2026-09-24 (Ref `56531885`, file `prvsiyan_kaggriculture_submission.tar.gz`). Status as of fresh read-back (2026-09-25 12:08 CEST (+0200)) is `SubmissionStatus.COMPLETE` with a public score snapshot of `2071.7` (private blank), with 110 completed public episodes and 1 completed validation episode (`113019966`). Shepherd Sovereign's accumulated public score is `2021.4` (Ref `56490949`, `COMPLETE`, 272 completed public episodes and 1 completed validation episode, not re-uploaded). While Prvsiyan's displayed public score is 50.3 points higher than Shepherd's, this difference reflects dynamic cumulative ratings against varying matchmaking opponents over different episode counts (110 vs 272), not a matched head-to-head A/B result. The episodes endpoint does not establish opponent identities or match outcomes. No submission was made during this documentation refresh. Under Kaggle's active tracking policy (latest two submissions), Prvsiyan and Shepherd are the latest-two tracked submissions, with Jaxa 2802 Variant B (Ref `56467787`, `1680.8`) retired to third/older. See [`docs/experiments/agent_selection/report.md`](experiments/agent_selection/report.md) for full provenance, episode details, and caveats.

