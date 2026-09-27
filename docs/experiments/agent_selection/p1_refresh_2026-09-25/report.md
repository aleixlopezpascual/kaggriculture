# Local Agent Selection Experiment Report: P1 Refresh (Screening & Confirmation 2026-09-25)

## Executive Summary

This report documents the local, offline Phase 1 (P1) refresh tournament evaluating competitive agent architectures for the Kaggle Kaggriculture 720-turn simulation environment. The experiment evaluated eight byte-pinned candidate policies across two rigorous stages under the official simulation engine (`kaggle-environments 1.32.7`):

1. **Phase 1 (Screening):** A full round-robin tournament across all eight candidates over four fixed seeds (224 matches total; 56 matches per candidate; 28 unordered pairs $\times$ 2 seat orientations).
2. **Phase 2 (Confirmation):** An untouched holdout benchmarking tournament between the top two screening finalists—**Arsgorynich Herd-Safe V3** (`arsgorynich_herd_safe_v3`) and **Prvsiyan Moon Counts Melons** (`prvsiyan_moon_counts_melons`)—competing against each other and all six non-finalists across eight fresh held-out seeds (208 matches total; 112 matches per finalist).

### Key Findings
* **Objective Separation:** Official competition standings and evaluation rely on discrete match win points (win = 1.0, tie = 0.5, loss = 0.0) [1], not coin margins or solo farm bank totals. Terminal coins and margins are tracked as secondary diagnostics.
* **Screening Leader vs Confirmation Point-Estimate Leader:**
  * In Phase 1 screening, **Arsgorynich Herd-Safe V3** finished as the **round-robin screening leader** with a match-points rate of **0.892857 [0.785714, 1.000000]** (50-6-0, mean margin +2528.96 coins), while **Prvsiyan Moon Counts Melons** placed second with **0.714286 [0.607143, 0.821429]** (40-16-0, mean margin -1670.07 coins). Because their 95% seed-cluster bootstrap intervals overlap, Arsgorynich is the round-robin screening leader, not an unconditional global champion.
  * In Phase 2 confirmation across 112 matches per finalist, **Prvsiyan Moon Counts Melons** emerged as the **observed confirmation-panel point-estimate leader** with a match-points rate of **0.803571 [0.732143, 0.857143]** (90-22-0) versus Arsgorynich's **0.678571 [0.562500, 0.803571]** (76-36-0).
* **Whole-Roster Paired Uncertainty (Inconclusive Global Winner):** In a paired whole-seed cluster bootstrap analysis across the eight confirmation seeds (10,000 resamples), the paired whole-roster difference ($\Delta = \text{Prvsiyan} - \text{Arsgorynich}$) is **+0.125000 (+12.5 percentage points)**, but the 95% bootstrap confidence interval is **`[-0.044643, +0.276786]`**. Because this interval crosses zero, there is **no statistically decisive overall panel winner** across all opponents.
* **Direct Head-to-Head Decisiveness:** In direct head-to-head play across 16 confirmation matches (8 seeds $\times$ both seats), Prvsiyan defeated Arsgorynich **14-2-0** (0.875000 match-points rate, mean margin +927.9 coins). This result was stable across seats: Prvsiyan went 7-1 in each seat orientation, and Arsgorynich went 1-7 in each seat orientation. The paired head-to-head difference is **+0.750000** (95% seed-cluster CI `[+0.250000, +1.000000]`), with 7 of 8 seeds favoring Prvsiyan. Direct head-to-head outcomes must be reported separately from the uncertain whole-roster aggregate.
* **The Jaxa 2802 Anomaly & Severe Matchup Risk:** Prvsiyan displays a critical blind spot against **Jaxa 2802 Variant B**, losing all 16 sampled matches (**0-16-0**, losing 0-8 in each seat orientation, mean margin -14,300.2 coins). Conversely, Arsgorynich swept Jaxa **16-0-0** (+4,428.9 coins margin). This forms a severe intransitive triangle (Prvsiyan beats Arsgorynich, Arsgorynich beats Jaxa, Jaxa sweeps Prvsiyan). Collapsing performance to mean points alone obscures this catastrophic matchup liability.
* **Strict Runtime & Latency Warning:** Both finalists failed the workspace strict `<100 ms` per-callback guideline (`GEMINI.md`). Across 80,528 callbacks each, both Arsgorynich and Prvsiyan recorded **14 callbacks exceeding 100 ms**, with maximum callback latencies reaching **160.04 ms** (Arsgorynich) and **200.99 ms** (Prvsiyan). While all callback exception counters were zero, the latency gate was not strictly satisfied. Because four seed jobs executed concurrently per batch, host contention may have inflated tail timings; serialized profiling is required before judging intrinsic runtime. The worst individual per-match p95 was 3.36 ms for Arsgorynich and 4.17 ms for Prvsiyan (not overall p95s).
* **Policy Telemetry Signals:** Telemetry was non-empty in all 112 finalist appearances. Arsgorynich recorded no non-zero error-like counters. Prvsiyan recorded one `cattle_failed_purchase_units` in each of 8 unique Jaxa matches (both seat orientations across 4 seeds); associated `errors` and `sale_errors` remained zero. This is a policy telemetry signal to investigate, not a runtime exception or forfeit. Jaxa exported no policy telemetry.
* **Operational Scope & Decision:** **No strategy source was changed, no Kaggle upload or submission was performed, and no medal outcome is established.** Prvsiyan is treated as the provisional confirmation-panel point-estimate leader, while Arsgorynich provides critical defense against Jaxa-type policies. The existing user active ladder pair (Prvsiyan ref `56531885` and Shepherd Sovereign ref `56490949`)[36] remains untouched.

---

## 1. Experimental Design, Provenance & Verification

### 1.1 Simulation Engine & Scoring Standards
* **Engine:** `kaggle-environments` version `1.32.7` (verified via `importlib.metadata`).
* **Game Horizon:** 720 discrete simulation steps per match.
* **Primary Objective:** Match win points (win = 1.0, tie = 0.5, loss = 0.0) [1]. Official ladder Elo and post-deadline tournament ranking evaluate game outcomes, not coin margins.
* **Secondary Metrics:** Mean candidate terminal coins, mean opponent terminal coins, and mean margin ($\text{Coins}_{\text{candidate}} - \text{Coins}_{\text{opponent}}$).
* **Execution Safety:** All candidate scripts were executed locally in-process without sandbox isolation. Manifest and source integrity were validated before and after execution.

### 1.2 Candidate Roster & Byte-Pinned Provenance
The eight evaluated candidates represent active user baselines, prior internal benchmarks, and curated public lineages. Candidates were registered in frozen manifest `candidates.json` (SHA-256: `d0e1dc3208df1f3dd67b17a317c48118320ed5b55de5d07483f13992068df2c8`):

| Candidate ID | Name | Lineage & Group | Source File Path | SHA-256 Digest | License |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `shepherd_sovereign` | Shepherd Sovereign | User active baseline (Submission Ref 56490949)[36] | `competitors/notebooks/shepherd_sovereign_main.py` | `5f2b51a2beaf5e08cb73e82f0e03e02e56de601563b28344e49b7058e371b247` | Repo-local user baseline |
| `prvsiyan_moon_counts_melons` | The Moon Counts Melons | User active challenger (Submission Ref 56531885)[36][37] | `sources/prvsiyan_moon_counts_melons/main.py` | `178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a` | Apache-2.0 |
| `jaxa_2802_variant_b` | Jaxa 2802 Variant B | User prior submission (Submission Ref 56467787; matchup stress)[36] | `competitors/notebooks/jaxa_2802_router/main_variant_b_h24.py` | `944aa64c5ae1296a9a17eb7961ed8d5a96d0b80183d41e954389983d73420a56` | Repo-local user baseline |
| `peak_2950` | The 2950 Peak Farm | Repository-local prior benchmark (Peak Farm) | `competitors/notebooks/peak_2950_main.py` | `613245d98c5066f9c393de866b0e19998c0f7ba636be08b2990a3e5e79d18ca7` | Repo-local benchmark |
| `v57_invariant` | V57 Invariant | Repo-local benchmark (Ahmed lineage representative) [33] | `competitors/notebooks/v57_main.py` | `2ee689fdc58f38b7bf6b80b8d3f48129d19b47201dbee51fdcbd977498a5106f` | Apache-2.0 |
| `thomas_2945_farm` | Thomas 2945 Farm | Repository-local prior benchmark (Thomas 2945) | `competitors/notebooks/thomas_2945_main.py` | `4f3ca95dd12d9a94b03339999d8803c155f450a8d3956636f050643301fcc5dd` | Repo-local benchmark |
| `cha22_multi_route` | Cha22 R5 Multi-Route | Public candidate (`flexonafft` / Guruprasaathas Master Engine V3) | `sources/cha22_multi_route/main.py` | `127ed3e62988c0474d386db6527ae8ca9de9bb1fe7004128557ddef67126c652` | Apache-2.0 |
| `arsgorynich_herd_safe_v3` | Herd-Safe V3 Risk-Aware | Public candidate (`arsgorynich`, composite lineage) [26] | `sources/arsgorynich-herd-safe-v3/main.py` | `4f8637a3e33348b98f531de246d353f5d2955b2f85480e3fd02bf4a7874f0d01` | Apache-2.0 (with LICENSE/NOTICE) |

*Excluded Candidates:* Ahmed V39 and V55 were excluded as near-duplicates of the Ahmed lineage (represented by V57 Invariant); Herd-Safe Race was replaced by the newer Arsgorynich composite; Tetsutani Demand-Preserving was excluded as byte-identical to Cha22; Nusrati/2715-6 was excluded due to an unresolvable native `.so` binary; Shiiin9 was excluded as an ancestor of the composite.

*Verification & Hash Integrity:* All 8 source files were re-hashed against `candidates.json` before execution, and re-hashed again after execution; all 8 source files still match the manifest. The same hashes matched before execution, after execution, and in every raw game record. Zero source-hash mismatches occurred. Public page scores (e.g., displayed scores for V57 [33] or Arsgorynich [26]) are recorded strictly for discovery metadata and were not used in evaluation.

### 1.3 Execution Integrity: Phase 1 Screening
* **Screening Seeds:** Exactly 4 fixed seeds: `[972925858, 256507559, 522388730, 336278987]`.
* **Match Schedule:** Full round-robin across all 8 candidates. 28 unordered pairs $\times$ 2 seat orientations (Seat 0 and Seat 1) $\times$ 4 seeds = **224 matches total** (56 matches per candidate; 8 matches per opponent pair).
* **Integrity Audit:** 224/224 matches completed successfully; 448/448 player terminal statuses were `DONE`; scoring basis `coins`; 0 runner/agent error strings; 0 callback exceptions; 0 source-hash mismatches. Each candidate executed 40,264 callbacks (719 per match).
* **Recorded Match Durations (`duration_sec`):** 224 matches; sum 1254.61 s; mean 5.601 s; median 5.600 s; empirical p95 6.11 s; max 7.43 s. (Note: These are statistics of per-match `duration_sec`, not wall-clock elapsed time, as seed workers ran in parallel).

### 1.4 Predeclared Finalist Selection Rule
To eliminate post-hoc selection bias, the finalist advancement rule was fixed in the manifest prior to screening execution:
$$\text{Rank By:} \quad \text{Match-Points Rate (Descending)} \implies \text{Mean Margin (Descending)} \implies \text{Candidate ID (Ascending)}$$
Under this rule, the top two candidates advance as finalists to Phase 2 confirmation.

### 1.5 Execution Integrity: Phase 2 Confirmation
* **Confirmation Seeds:** Exactly 8 fresh held-out seeds: `[738084249, 590003991, 966857091, 300914001, 739524397, 846313352, 811995954, 896328793]`.
* **Disjointness Guarantee:** These seeds were verified disjoint from the 4 screening seeds, the prior frozen 12-seed panel (manifest `dfa516424369d4fa30e35cd06da95bff1ffe09a73919a549dc1ca78c6b078a46`), the three P0 replay seeds (`[1714719438, 493147447, 2126140119]`), and the screening smoke seed.
* **Untouched Holdout Protocol:** Raw confirmation results were not inspected until all eight seed jobs completed execution.
* **Schedule & Accounting Correction:** Each seed consists of 26 matches: 2 direct head-to-head matches between finalists (both seats) + 12 matches for Arsgorynich (vs 6 non-finalists in both seats) + 12 matches for Prvsiyan (vs 6 non-finalists in both seats) = 26 matches/seed $\times$ 8 seeds = **208 matches total**.
  * Each finalist appeared in 14 matches per seed, yielding **112 matches per finalist** (8 seeds $\times$ 14 matches = 112 matches).
  * *Transparent Accounting Note:* An earlier rough planning estimate of 104 matches per finalist was an arithmetic planning error. The runner executed the exact schedule of 26 matches per seed (208 total; 112 per finalist; 32 per non-finalist). No frozen totals or raw game records were modified.
* **Integrity Audit:** 208/208 matches completed successfully; 416/416 player terminal statuses were `DONE`; 0 invalid matches; 0 callback exceptions; 0 runner errors; 0 source-hash mismatches. Each finalist executed 80,528 callbacks.
* **Recorded Match Durations (`duration_sec`):** 208 matches; sum 1194.52 s; mean 5.743 s; median 5.780 s; empirical p95 6.25 s; max 6.57 s. (Note: These are statistics of per-match `duration_sec`, not wall-clock elapsed time, as seed workers ran in parallel).

---

## 2. Phase 1: Screening Tournament Results

In Phase 1, all eight candidates completed 56 matches in a full round robin. The primary metric is match-points rate ($\text{Points} / 56$). Seed-cluster 95% confidence intervals are computed via 10,000 resamples over the 4 seed clusters (not treating seat swaps as independent). All screening matches concluded without ties.

### 2.1 Screening Leaderboard (56 Matches / Candidate)

| Rank | Candidate ID | Record (W-L-T) | Points Rate | 95% Seed-Cluster CI | Mean Margin | Mean Coins | Callbacks / Errors | >100ms Calls | Max Latency | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `arsgorynich_herd_safe_v3` | **50-6-0** | **0.892857** | **[0.785714, 1.000000]** | **+2528.96** | $105,196.54 | 40,264 / 0 | 9 | 172.91 ms | **Advanced (Screening Leader)** |
| **2** | `prvsiyan_moon_counts_melons` | **40-16-0** | **0.714286** | **[0.607143, 0.821429]** | **-1670.07** | $104,797.29 | 40,264 / 0 | 3 | 161.00 ms | **Advanced to Finals** |
| 3 | `shepherd_sovereign` | 38-18-0 | 0.678571 | [0.428571, 0.928571] | +2022.50 | $105,079.29 | 40,264 / 0 | 1 | 102.67 ms | Eliminated |
| 4 | `jaxa_2802_variant_b` | 24-32-0 | 0.428571 | [0.428571, 0.428571] | +4420.89 | $109,877.73 | 40,264 / 0 | 2 | 130.14 ms | Eliminated (Tiebreak: Margin +4420.89) |
| 5 | `v57_invariant` | 24-32-0 | 0.428571 | [0.321429, 0.535714] | -2524.70 | $104,400.32 | 40,264 / 0 | 7 | 158.60 ms | Eliminated (Tiebreak: Margin -2524.70) |
| 6 | `cha22_multi_route` | 20-36-0 | 0.357143 | [0.285714, 0.500000] | -571.39 | $103,252.36 | 40,264 / 0 | 7 | 130.44 ms | Eliminated |
| 7 | `thomas_2945_farm` | 14-42-0 | 0.250000 | [0.142857, 0.464286] | -1092.00 | $102,774.86 | 40,264 / 0 | 3 | 376.13 ms | Eliminated (Tiebreak: Margin -1092.00) |
| 8 | `peak_2950` | 14-42-0 | 0.250000 | [0.178571, 0.285714] | -3114.20 | $102,498.88 | 40,264 / 0 | 2 | 119.52 ms | Eliminated (Tiebreak: Margin -3114.20) |

### 2.2 Screening Analysis & Matchup Structure
* **Round-Robin Screening Leader:** Arsgorynich Herd-Safe V3 placed #1 with 50 wins in 56 games (0.892857). However, its 95% bootstrap CI `[0.785714, 1.000000]` overlaps with Prvsiyan's `[0.607143, 0.821429]`. Therefore, Arsgorynich is designated the **round-robin screening leader**, not an unconditional global champion.
* **Top Candidate Screening Matchups:**
  * Arsgorynich vs Prvsiyan: **6-2-0** (0.750 points rate)
  * Arsgorynich vs Shepherd: **4-4-0** (0.500 points rate)
  * Arsgorynich vs Jaxa: **8-0-0** (1.000 points rate)
  * Prvsiyan vs Arsgorynich: **2-6-0** (0.250 points rate)
  * Prvsiyan vs Shepherd: **6-2-0** (0.750 points rate)
  * Prvsiyan vs Jaxa: **0-8-0** (0.000 points rate; swept in both seats)
* **The Coin vs Points Decoupling:** Jaxa 2802 Variant B achieved the highest average coin total ($109,877.73) and highest mean margin (+4420.89 coins) in screening, yet tied for 4th place in points rate (0.428571, 24 wins). This reinforces that raw cash accumulation is not a proxy for tournament victory.
* **Screening Policy Telemetry:** Telemetry was non-empty for all candidates except Jaxa 2802 Variant B (which exported no custom policy telemetry). Zero callback or terminal errors occurred. The only non-zero error-like counter was `cattle_failed_purchase_units`: Prvsiyan and V57 each logged 1 failed cattle purchase unit in two mirrored games against Jaxa on seed `972925858`. (The counter was duplicated across 11 versioned telemetry report dictionaries, representing 2 unique game records). Associated runner error fields were zero.

---

## 3. Phase 2: Confirmation Tournament Results

Phase 2 evaluated finalists **Arsgorynich Herd-Safe V3** and **Prvsiyan Moon Counts Melons** across eight fresh held-out seeds. Each finalist completed 112 matches: 16 direct head-to-head matches and 96 matches across the six non-finalists (16 matches per non-finalist; both seats). No matches ended in ties.

### 3.1 Pooled Confirmation Performance (112 Matches / Finalist)

| Finalist | Record (W-L-T) | Points Rate | 95% Seed-Cluster CI | Mean Margin | Mean Candidate Coins | Mean Opponent Coins | Callbacks / Errors | >100ms Calls | Max Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`prvsiyan_moon_counts_melons`** | **90-22-0** | **0.803571** | **[0.732143, 0.857143]** | **-466.56** | **$88,514.63** | $88,981.20 | 80,528 / 0 | 14 | 200.99 ms |
| **`arsgorynich_herd_safe_v3`** | 76-36-0 | 0.678571 | [0.562500, 0.803571] | +1099.87 | $86,558.23 | $85,458.37 | 80,528 / 0 | 14 | 160.04 ms |

### 3.2 Paired Whole-Roster Analysis Across Seed Clusters
To evaluate whether Prvsiyan's higher pooled point rate represents an unconditional advantage across all opponents, we evaluate the paired difference per seed cluster ($N = 8$ seeds, 14 matches per finalist per seed):
$$\Delta_s = \text{Rate}_{\text{Prvsiyan}, s} - \text{Rate}_{\text{Arsgorynich}, s}$$

| Confirmation Seed | Arsgorynich Wins (14 g) | Prvsiyan Wins (14 g) | Paired Difference ($\Delta_s$) | Seed Character / Notes |
| :---: | :---: | :---: | :---: | :--- |
| `300914001` | 13 / 14 (0.928571) | 8 / 14 (0.571429) | **-0.357143** | Arsgorynich favored |
| `590003991` | 12 / 14 (0.857143) | 12 / 14 (0.857143) | **0.000000** | Equal points |
| `738084249` | 8 / 14 (0.571429) | 12 / 14 (0.857143) | **+0.285714** | Prvsiyan favored |
| `739524397` | 10 / 14 (0.714286) | 12 / 14 (0.857143) | **+0.142857** | Prvsiyan favored |
| `811995954` | 12 / 14 (0.857143) | 12 / 14 (0.857143) | **0.000000** | Equal points |
| `846313352` | 7 / 14 (0.500000) | 12 / 14 (0.857143) | **+0.357143** | Prvsiyan favored |
| `896328793` | 8 / 14 (0.571429) | 10 / 14 (0.714286) | **+0.142857** | Prvsiyan favored |
| `966857091` | 6 / 14 (0.428571) | 12 / 14 (0.857143) | **+0.428571** | Prvsiyan favored |
| **Mean Paired Difference** | — | — | **+0.125000 (+12.5 pp)** | 5 seeds positive for Prvsiyan, 2 tied, 1 negative |

#### Whole-Seed Cluster Bootstrap Analysis (10,000 Resamples)
* **Mean Paired Difference:** **+0.125000** (+12.5 percentage points for Prvsiyan).
* **95% Bootstrap Confidence Interval:** **`[-0.044643, +0.276786]`**.
* **Statistical Conclusion:** **The 95% confidence interval crosses zero.** Prvsiyan had more points on 5/8 seeds, the finalists tied on 2, and Arsgorynich led on 1 (300914001); the 95% CI `[-0.044643, +0.276786]` still crosses zero, so no decisive overall panel winner.

### 3.3 Direct Head-to-Head Benchmark
Across the 16 direct head-to-head encounters between the two finalists (8 seeds $\times$ both seat positions):
* **Direct Match Record:** Prvsiyan defeated Arsgorynich **14-2-0** (0.875000 match-points rate vs 0.125000).
* **Direct Margin & Cash:** Prvsiyan achieved a mean margin of **+927.9 coins** ($86,417.9 vs $85,489.9).
* **Seat Stability:** The result was symmetrical and stable across seat orientations:
  * Seat 0: Prvsiyan **7-1**; Arsgorynich **1-7**.
  * Seat 1: Prvsiyan **7-1**; Arsgorynich **1-7**.
* **Paired H2H Difference:** $\Delta_{\text{H2H}} = +0.750000$; 10,000 whole-seed-cluster bootstrap 95% CI is **`[+0.250000, +1.000000]`**. Seven of the eight confirmation seeds favored Prvsiyan in direct play; one favored Arsgorynich. Direct head-to-head results must be reported separately from whole-roster aggregate comparisons.

---

## 4. Per-Opponent Matchup Breakdown & The Jaxa Contrast

Each finalist played 16 matches against each roster opponent (8 seeds $\times$ 2 seat orientations).

### 4.1 Detailed Per-Opponent Matchup Table

| Finalist Candidate | Opponent Candidate | Finalist Record (W-L-T) | Finalist Points Rate | Finalist Mean Coins | Opponent Mean Coins | Mean Margin |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`arsgorynich_herd_safe_v3`** | vs `cha22_multi_route` | 14-2-0 | 0.8750 | $86,572.4 | $85,628.8 | +943.7 |
| **`arsgorynich_herd_safe_v3`** | vs `jaxa_2802_variant_b` | 16-0-0 | 1.0000 | $87,716.2 | $83,287.3 | +4,428.9 |
| **`arsgorynich_herd_safe_v3`** | vs `peak_2950` | 13-3-0 | 0.8125 | $86,490.5 | $85,901.0 | +589.5 |
| **`arsgorynich_herd_safe_v3`** | vs `shepherd_sovereign` | 7-9-0 | 0.4375 | $86,288.0 | $85,918.8 | +369.2 |
| **`arsgorynich_herd_safe_v3`** | vs `thomas_2945_farm` | 16-0-0 | 1.0000 | $87,005.5 | $84,864.5 | +2,141.0 |
| **`arsgorynich_herd_safe_v3`** | vs `v57_invariant` | 8-8-0 | 0.5000 | $86,345.0 | $86,190.3 | +154.7 |
| **`prvsiyan_moon_counts_melons`** | vs `arsgorynich_herd_safe_v3` (H2H) | 14-2-0 | 0.8750 | $86,417.9 | $85,489.9 | +927.9 |
| **`prvsiyan_moon_counts_melons`** | vs `cha22_multi_route` | 16-0-0 | 1.0000 | $87,613.1 | $84,873.9 | +2,739.2 |
| **`prvsiyan_moon_counts_melons`** | vs `jaxa_2802_variant_b` | **0-16-0** | **0.0000** | **$97,387.4** | **$111,687.7** | **-14,300.2** |
| **`prvsiyan_moon_counts_melons`** | vs `peak_2950` | 16-0-0 | 1.0000 | $86,939.0 | $85,304.7 | +1,634.3 |
| **`prvsiyan_moon_counts_melons`** | vs `shepherd_sovereign` | 12-4-0 | 0.7500 | $86,789.4 | $85,478.8 | +1,310.6 |
| **`prvsiyan_moon_counts_melons`** | vs `thomas_2945_farm` | 16-0-0 | 1.0000 | $87,588.8 | $84,521.8 | +3,067.1 |
| **`prvsiyan_moon_counts_melons`** | vs `v57_invariant` | 16-0-0 | 1.0000 | $86,866.8 | $85,511.7 | +1,355.1 |

### 4.2 The Severe Jaxa 2802 Matchup Risk
* **0-16 Sweep:** Prvsiyan failed to win a single match against Jaxa 2802 Variant B (**0-16-0**, losing all 8 matches in Seat 0 and all 8 matches in Seat 1). Its mean deficit was -14,300.2 coins ($97,387.4 vs $111,687.7).
* **Arsgorynich 16-0 Sweep:** In contrast, Arsgorynich went 16-0 in this 16-game panel matchup against Jaxa's strategy (**16-0-0**, mean margin +4,428.9 coins).
* **Intransitivity Cycle:** This creates a cyclic dynamic:
  $$\text{Prvsiyan} \xrightarrow{\text{beats (14-2)}} \text{Arsgorynich} \xrightarrow{\text{beats (16-0)}} \text{Jaxa 2802} \xrightarrow{\text{beats (16-0)}} \text{Prvsiyan}$$
* **Panel vs Global Population:** While the 8-candidate panel is diverse across major public lineages, it is not the live global Kaggle matchmaking pool. The prevalence of Jaxa-like high-volume predictive routers on the live ladder is unknown, and this result is conditional on encountering them; the panel does not quantify prevalence or any resulting live-rating impact.

---

## 5. Runtime, Latency & Policy Telemetry

### 5.1 Callback Latency & System Limits
* **Workspace Guideline:** `GEMINI.md` mandates that `agent.act()` return in **under 100 ms** to ensure headroom against Kaggle's live timeout limit.
* **Observed Latency Exceedances:**
  * **Arsgorynich:** 14 callbacks exceeded 100 ms across 80,528 total calls; maximum callback latency was **160.04 ms**.
  * **Prvsiyan:** 14 callbacks exceeded 100 ms across 80,528 total calls; maximum callback latency was **200.99 ms**.
* **Zero Exception Counters:** All callback error counters (`callback_errors = 0`) and technical match errors (`technical_errors = 0`) were zero. However, zero exceptions do **not** mean the strict 100 ms latency gate was passed.
* **Host Contention Context:** Confirmation runs executed four seed jobs concurrently per batch. Multi-core execution contention on the local host likely inflated tail latencies. The worst individual per-match p95 latency was **3.36 ms** for Arsgorynich and **4.17 ms** for Prvsiyan (these are worst-match p95 values, not overall aggregate p95s). Serialized profiling under single-process execution is recommended to assess intrinsic latency.
* **Recorded Match Durations (`duration_sec`):** Clearly distinguished as sums and statistics of per-match `duration_sec`, not wall-clock elapsed time (seed workers ran in parallel):
  * **Screening (224 matches):** sum 1254.61 s; mean 5.601 s; median 5.600 s; empirical p95 6.11 s; max 7.43 s.
  * **Confirmation (208 matches):** sum 1194.52 s; mean 5.743 s; median 5.780 s; empirical p95 6.25 s; max 6.57 s.

### 5.2 Policy Telemetry & Error Indicators
* **Telemetry Presence:** Non-empty policy telemetry was exported in all 112 appearances for both finalists.
* **Arsgorynich:** Exported zero non-zero error-like policy counters across all matches.
* **Prvsiyan:** Exported exactly one `cattle_failed_purchase_units` in each of 8 unique matches against Jaxa 2802 Variant B (both seat orientations across seeds `738084249`, `300914001`, `846313352`, and `896328793`). In each case, Prvsiyan's associated `errors` and `sale_errors` fields remained zero. This is a policy telemetry signal to investigate, not a fatal crash or forfeit; the counter's cause has not been established. Note: Each event was repeated under 11 versioned telemetry report keys per game record; counting unique game records yields exactly 8 affected matches.
* **Jaxa 2802 Variant B:** Exported no policy telemetry dictionaries.
* **Invalid Actions:** The runner did not record an engine-level invalid-action counter; therefore, no assertion regarding total invalid actions can be made.

---

## 6. Limitations

1. **Finite Seed Sampling:** Confirmation utilized eight seeds ($N = 8$). Although each seed was evaluated across 26 matches with matched pairs and seat swaps, seed-cluster bootstrap analysis reveals broad uncertainty.
2. **Curated Panel vs Live Population:** The panel includes prominent community lineages (Ahmed, Thomas, Flexonafft, Jaxa, Arsgorynich) but does not mirror the live distribution of thousands of active competitors.
3. **Severe Non-Transitivity:** The presence of cyclic dominance (Prvsiyan $\to$ Arsgorynich $\to$ Jaxa $\to$ Prvsiyan) demonstrates that no single scalar rating captures all head-to-head dynamics.
4. **Concurrent Timing Telemetry:** Latency tails reflect shared host execution under parallel batches, not a dedicated single-threaded benchmark.
5. **No Guarantee of Live Ladder Movement:** Offline tournament points do not guarantee live rating gains, medal progression, or specific ladder outcomes.

---

## 7. Interpretation & Operational Decision

1. **Role Designations:**
   * **Arsgorynich Herd-Safe V3** is designated the **round-robin screening leader** (0.892857 points rate in Phase 1).
   * **Prvsiyan Moon Counts Melons** is designated the **observed confirmation-panel point-estimate leader** (0.803571 points rate in Phase 2; 14-2 head-to-head).
2. **Inconclusive Superiority:** Because the paired whole-roster difference 95% bootstrap CI crosses zero (`[-0.044643, +0.276786]`), Prvsiyan cannot be declared an unconditional global winner over Arsgorynich.
3. **Actionable Recommendations:**
   * **Do not execute an unapproved Kaggle upload.** Keep the active submissions untouched.
   * **Investigate Prvsiyan's Jaxa Vulnerability:** Analyze the 16 Jaxa match traces to determine the cause and impact of the `cattle_failed_purchase_units` signal.
   * **Profile Serialized Latency:** Benchmark both candidates in isolation to verify whether the 14 latency spikes over 100 ms persist without concurrent host load.
   * **Proceed with Scoped Mechanistic Experiments:** Advance to P2 (market order optimization) and P3 (finite-horizon herd valuation) using this calibrated 8-seed confirmation panel.

---

## 8. Artifacts & Data Provenance

All underlying data artifacts remain preserved and byte-frozen in the experiment directory:
* **Candidate Manifest:** [`candidates.json`](candidates.json) (SHA-256: `d0e1dc3208df1f3dd67b17a317c48118320ed5b55de5d07483f13992068df2c8`)
* **Screening Aggregate Summary:** [`screening_summary.json`](screening_summary.json)
* **Confirmation Aggregate Summary:** [`confirmation_summary.json`](confirmation_summary.json)
* **Screening Raw Seed Files:** `screening_seed_*.json` (seeds: `256507559`, `336278987`, `522388730`, `972925858`)
* **Confirmation Raw Seed Files:** `confirmation_seed_*.json` (seeds: `300914001`, `590003991`, `738084249`, `739524397`, `811995954`, `846313352`, `896328793`, `966857091`)

## Sources

[1] https://www.kaggle.com/competitions/kaggriculture/overview/evaluation
[26] https://www.kaggle.com/code/arsgorynich/herd-safe-v3-experimental-risk-aware-feed
[33] https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v57-funding-order-invariant
[36] https://www.kaggle.com/competitions/kaggriculture/submissions
[37] https://www.kaggle.com/code/prvsiyan/kaggriculture-frontier-the-moon-counts-melons
