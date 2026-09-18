# Kaggriculture Research Update: Final-Week Public Meta Decapsulation & Benchmarks
**Date:** September 18, 2026  
**Status:** Comprehensive Extraction, Parsing, and Local Matchup Verification

---

## 📋 Executive Summary

This report documents the parsing, decoding, extraction, and local head-to-head tournament evaluation of the latest Kaggle public agent release, **`Kaggriculture V48 — Clear the Queue`** (score `~2790` on public boards, derived from the file `40-40-early-floor-39-46-top-10-v48-fast-routes.ipynb`). 

Using our high-fidelity, sequential paired-seed tournament platform, we benchmarked V48 against our peak portfolio climber **`Jaxa 2802 Elo Router`** (v20) and **`EXP-173 v45 Fusion Router`** (v18). The results empirically demonstrate that the aggressively optimized sales sequencing of V48 decays heavily under rigorous, long-term multi-seed evaluation.

---

## ⚡ Deconstruction of the V48 "Clear the Queue" Mechanics

V48 attempts to optimize three distinct strategic levers:
1.  **The Two-Turn Sale Advance:** Proactively submits product sell orders exactly **two turns earlier** than standard public models to front-run opponents and liquidate assets before town multipliers deplete.
2.  **The 24-Turn Optimal Horizon:** Restricts the tape-preservation / pre-selling horizon to exactly **24 turns** ahead. Testing of smaller (8, 16) or larger (36, 48) ranges resulted in steep pricing drops.
3.  **The 10-Unit Step-0 Wheat Round Trip:** Employs a 10-unit early-wheat buy-sell cycle to distort the rival's index-1 funding buffer.

---

## ⚔️ Paired-Seed Local Tournament Results

### Matchup 1: `Jaxa V48 Clear-Queue` vs. `Jaxa 2802 Elo Router` (v20)
*   **Matches:** 10 sequential matches (Seeds `[42, 100, 2026, 1234, 555]`, playing both seats).

| Agent | Wins | Losses | Ties | Win % | Avg Gold |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Jaxa 2802 Elo Router** (v20) | 10 | 0 | 0 | **100.0%** | **$98,638** |
| **Jaxa V48 Clear-Queue** | 0 | 10 | 0 | 0.0% | **$76,436** |

*   **Average Margin Difference:** **+$22,202 gold** in favor of `Jaxa 2802`.
*   **Post-Mortem:** `Jaxa 2802` completely swept V48 10-0.

---

### Matchup 2: `Jaxa V48 Clear-Queue` vs. `EXP-173 v45 Fusion Router` (v18)
*   **Matches:** 6 sequential matches (Seeds `[42, 100, 2026]`, playing both seats).

| Agent | Wins | Losses | Ties | Win % | Avg Gold |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **EXP-173 v45 Fusion Router** | 6 | 0 | 0 | **100.0%** | **$97,456** |
| **Jaxa V48 Clear-Queue** | 0 | 6 | 0 | 0.0% | **$75,608** |

*   **Average Margin Difference:** **+$21,848 gold** in favor of `v45`.
*   **Post-Mortem:** `v45` swept V48 6-0.

---

## 🔍 Structural Deficiency: Why V48 Underperformed Locally

Our simulator logs identified a critical **market decay flaw** in the V48 action tapes:
*   While the **Two-Turn Sale Advance** works well when solo-evaluated on the public ladder, against an elite opponent executing optimal defensive actions, selling cash products too early **collapses local market quotes**.
*   This pricing crash during critical Day 2 and Day 3 animal/livestock cycles chokes compounding cash flow. V48 ends up with a significantly smaller seed budget on Day 3, forcing workers into idle loops and resulting in a **-$22,000 average gold deficit** by Turn 720.

---

## 🏁 Submission Status & Tactical Recommendation

*   **No New Submission Necessary:** Our active climbing agent **`Jaxa 2802 Elo Router`** remains our absolute peak model. It easily absorbs the market front-running of V48 and maintains an average winning margin of **+$22,202 gold** over it.
*   **Matchmaking Safety:** Submitting the V48 binary or compiling a fallback would overwrite one of our two active leaderboard slots (**`Reyhan`** at **2502.1 Elo** or **`Jaxa 2802`**).
*   **Decision:** Maintain our current dual-climber configuration on the Kaggle ladder. 
