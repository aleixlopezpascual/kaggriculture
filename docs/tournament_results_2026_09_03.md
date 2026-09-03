# Kaggriculture Head-to-Head Tournament & Bug Diagnostics Report

Date: 2026-09-03  
Status: Complete & Verified  

---

## 📊 1. Tournament Overview & Final Standings

We executed a systematic head-to-head tournament between our key agent baselines across **30 matched seat-swapped matches** on five diverse seeds (`42`, `100`, `2026`, `999`, and `12345`).

### Final Standings

| Agent | Matches | Wins | Losses | Ties | Win % | Avg Gold | Avg Margin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Six-Day Fieldbook (v8)** | 20 | 20 | 0 | 0 | 100.0% | **$140,562** | +$140,515 |
| **Heuristic Agent** | 20 | 10 | 10 | 0 | 50.0% | **$9,528** | -$63,518 |
| **MCTS Agent** | 20 | 0 | 20 | 0 | 0.0% | **$2,978** | -$76,997 |

### Head-to-Head Matchup Matrix
*(Row vs Column)*

| Agent (Row) vs Opp (Col) | Heuristic | MCTS | Six-Day Fieldbook |
| :--- | :--- | :--- | :--- |
| **Heuristic** | — | 5W - 0L - 0T (100%) | 0W - 5L - 0T (0%) |
| **MCTS** | 0W - 5L - 0T (0%) | — | 0W - 5L - 0T (0%) |
| **Six-Day Fieldbook** | 5W - 0L - 0T (100%) | 5W - 0L - 0T (100%) | — |

---

## 🔍 2. Deep-Dive Diagnostics & Root Cause Analyses

Initially, Heuristic and MCTS produced zero meaningful play, collapsing to exact scores of `$3,000` (original starting cash) or failing to make any money after purchasing items. Through step-by-step trace debugging and action inspections, we identified and resolved **three major execution-blocking alignment bugs**:

### Bug A: The Crop-Watering Blindspot (Watering Deficit)
*   **Symptom:** Planted crops were never watered, causing them to dry up and die before reaching maturity.
*   **Root Cause:** In our local transition model, crop watering is determined by `moisture <= 30`. However, the official Kaggle environments observation has no numeric moisture field; instead, it uses a boolean `watered_today` flag. Our state parser hardcoded crop moisture to `50`, meaning the `HeuristicAgent` saw `moisture=50` (which is $> 30$) and believed crops were perfectly fine, never watering them.
*   **Fix:** We upgraded `thirsty_crops` in `src/agents/heuristic.py` to support `is_watered` checking:
    ```python
    thirsty_crops = [c for c in state.crops if c.moisture <= 30 or not c.is_watered]
    ```

### Bug B: The Plural Key Discrepancy (Infinite Seed Buying)
*   **Symptom:** The agent continuously purchased strawberry seeds until it ran completely out of money.
*   **Root Cause:** The heuristic target defaults to `"Strawberries"` (plural). However, the state parser capitalizes the official item `"STRAWBERRY"` into `"Strawberry"` (singular). As a result, checks like `state.farm.seed_inventory.get("Strawberries")` returned `0` at all times, blinding the agent to its active inventory and forcing it into an endless seed purchase loop.
*   **Fix:** We updated all default crop priority keys in both `heuristic.py` and `mcts.py` to singular (`"Strawberry"` and `"Melon"`), and added singular support inside our calculators and market utility modules.

### Bug C: The Tilling & "DIG" Misconception (Infinite Dig Loop)
*   **Symptom:** Workers stood on empty tiles executing `["DIG"]` on every single turn, never planting seeds or moving.
*   **Root Cause:** In our local simulator, empty soil tiles must be explicitly "tilled" via `"TILE"` before they can be planted. But under the official Kaggle engine, empty tiles are already empty soil and do not need to be tilled. Executing `"DIG"` on an empty tile is a `no-op`. Because our parser didn't populate `state.tilled_tiles` under the official format, the agent believed the entire board was untilled and spent the match trying to till its current tile over and over.
*   **Fix:** We upgraded `parse_world_state` in `src/env/parser.py` to automatically populate `tilled_tiles` with all unlocked, unoccupied tiles on the board, immediately unlocking them for direct planting:
    ```python
    tilled_tiles = [coord for coord in unlocked_coords if coord not in occupied]
    ```

---

## 🚀 3. Key Takeaways & Future Directions

1.  **Baseline Activation Succeeded:** The `Heuristic` baseline average gold skyrocketed from **$89 to $9,528** across all seeds once these fixes were applied. It now correctly plants, waters, harvests, and sells crops automatically.
2.  **Strategic Target Slices:** Currently, the heuristic uses a single crop target focus. To reach the Six-Day Fieldbook's peak performance (~$140k+), we need to transition our local agents to support:
    *   Hiring hands and expanding quadrants sequentially.
    *   Implementing Livestock (Cows and Sheep) and physical feed/wheat cargo transportation.
    *   Leveraging **RouterNet** (or nearest-route trajectory cloning) to select macro plans based on public town shops.

---

*Report compiled by Gemini CLI on 2026-09-03.*
