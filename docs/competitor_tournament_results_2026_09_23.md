# Kaggriculture Systematic Local Tournament: Benchmark & Leaderboard Correlation
**Date:** September 23, 2026  
**Format:** 90 Head-to-Head Matches (6 Candidates × 5 Opponents × 2 Seat Orientations × 3 Diverse Seeds `[42, 100, 2026]`)

---

## 🏆 Final Tournament Standings & Kaggle Elo Correlation

| Rank | Candidate Agent | Matches | Wins | Losses | Ties | Win Rate | Local Avg Gold | Avg Margin | Kaggle Leaderboard Elo | Key Architectural Features |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#1** | **Jaxa 2802 Variant B** | 30 | **26** | 4 | 0 | **`86.7%`** | $78,909 | **`+$4,901`** | **`1816.5`** *(Peak: `2008.2`)* | **Original World Champion:** `HORIZON = 24`, `LOOKAHEAD = 2`, `OPEN_UNITS = 10`. Swept 4 out of 5 opponents 6–0. |
| **#2** | **Herd-Safe Race Router** | 30 | **22** | 8 | 0 | **`73.3%`** | **`$83,385`** | **`+$3,410`** | **`Unsubmitted`** *(New Sept 23)* | **New Frontier:** `COURIER` same-day shed deliveries + `HERD2` dynamic sheep/cow swaps + `RACEPX` price-floor guards. Winning record vs **all** agents. |
| **#3** | **Jaxa 2802 Variant A** | 30 | **18** | 12 | 0 | **`60.0%`** | $82,793 | **`+$3,365`** | **`1673.3`** | **Overfit Sweep:** `HORIZON = 1`, `LOOKAHEAD = 1`, `OPEN_UNITS = 8`. Lost 0–6 vs Variant B; lower win rate despite higher theoretical solo gold. |
| **#4** | **V57 Invariant** | 30 | **14** | 16 | 0 | **`46.7%`** | $79,915 | **`+$6,216`** | **`Unsubmitted`** *(New Sept 22)* | **Order-Book Invariant:** Slot-by-slot lockstep auction reordering with causal funding-order safety. |
| **#5** | **Reyhan Dynamic** | 30 | **10** | 20 | 0 | **`33.3%`** | $78,509 | **`+1,011`** | **`1735.7`** *(Peak: `1933.7`)* | **Dynamic 6-Day Decision Forest:** High-speed cash rotation with weed-slip recovery. |
| **#6** | **Thomas 93.8%** | 30 | **0** | 30 | 0 | **`0.0%`** | $72,238 | **`-18,903`** | **`1744.0`** *(Retired)* | **Classical Baseline:** Completely swept 0–6 by every modern September 2026 router. |

---

## 🥊 Head-to-Head Matchup Matrix (W - L - T)

| Opponent $\rightarrow$<br>Agent $\downarrow$ | Jaxa 2802 B | Herd-Safe Race | Jaxa 2802 A | V57 Invariant | Reyhan Dynamic | Thomas 93.8% | Total Record |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Jaxa 2802 Variant B** | — | 2 – 4 | **6 – 0** | **6 – 0** | **6 – 0** | **6 – 0** | **26 – 4 (86.7%)** |
| **Herd-Safe Race** | **4 – 2** | — | **4 – 2** | **4 – 2** | **4 – 2** | **6 – 0** | **22 – 8 (73.3%)** |
| **Jaxa 2802 Variant A** | 0 – 6 | 2 – 4 | — | **6 – 0** | **4 – 2** | **6 – 0** | **18 – 12 (60.0%)** |
| **V57 Invariant** | 0 – 6 | 2 – 4 | 0 – 6 | — | **6 – 0** | **6 – 0** | **14 – 16 (46.7%)** |
| **Reyhan Dynamic** | 0 – 6 | 2 – 4 | 2 – 4 | 0 – 6 | — | **6 – 0** | **10 – 20 (33.3%)** |
| **Thomas 93.8%** | 0 – 6 | 0 – 6 | 0 – 6 | 0 – 6 | 0 – 6 | — | **0 – 30 (0.0%)** |

---

## 💡 Key Analytical Insights

### 1. Proof of the Overfitting Trap: Higher Solo Gold $\neq$ Higher Win Rate
*   **Variant A vs Variant B:** In the tournament, Variant A averaged **$82,793** solo gold compared to Variant B's **$78,909** (+3,884 gold higher!).
*   **Yet Variant B crushed Variant A 6–0 head-to-head**, achieved an **86.7% win rate** compared to Variant A's **60.0%**, and holds a **+143.2 Elo lead** on the live Kaggle ladder.
*   **The Cause:** Variant A hoards goods to maximize its theoretical cash yield, but Variant B front-runs town pricing by selling 24 turns early. In a shared-market head-to-head, Variant B's early sales crash the market price, forcing Variant A to sell into depressed quotes.

### 2. The Power of "Herd-Safe Race" (The Unsubmitted Giant)
*   **`Herd-Safe Race`** achieved the highest overall average gold (**$83,385**) and holds a **winning head-to-head record against every single agent in the competition** (including 4–2 over Jaxa Variant B and 4–2 over Jaxa Variant A).
*   Its secret weapon is the **`COURIER` layer** (delivering harvested goods to the shed at Hour 20–22 to sell on the evening market at morning peak quotes 24 hours early) combined with **dynamic species selection (`HERD2`)**, swapping geese for cows/sheep based on town shop types.
