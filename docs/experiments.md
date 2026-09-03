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
| **v6** | `55970505` | `submission.tar.gz` | **C95** Public Baseline (Weed-Slip, Front-Run) | **$154,927** | **1196.0** | **Active / Climbing** |

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
*   **Live Performance:** **`1196.0`** Elo (Active / Climbing).
*   **Why it succeeded:** True physical drop coordination, automated end-of-day backups, and dynamic, error-free path recovery under random seeds.
