# Local Agent Selection Experiment Report: P2 Market Slot Ordering (2026-09-26)

## Executive Summary

This report documents the local, offline P2 market slot ordering experiment (where “P2” is this experiment/workstream label; within it, “Phase 1” means exploratory screening and “Phase 2” means predeclared confirmation) evaluating an isolated experiment-only candidate against the frozen baseline controller in the Kaggle Kaggriculture 720-turn simulation environment (`kaggle-environments 1.32.7`).

The experiment tested whether optimizing the ordering of eligible `SELL` slots within each turn's market action vector affects match outcomes under the local `kaggle-environments 1.32.7` implementation. To ensure strict isolation and eliminate post-hoc selection bias:
* The confirmation comparison between the baseline (**`prvsiyan_moon_counts_melons`**) and the challenger (**`prvsiyan_global_sell_slot_challenger`**) was fixed in advance by the manifest ([`candidates.json`](candidates.json)), regardless of exploratory screening results.
* Active user submissions and source files remain completely unchanged.
* All findings and metrics in this report are strictly scoped to this frozen local panel. No live Kaggle ladder score, rating change, global winner, or competition submission claim is made.

### Key Confirmation Findings
* **Primary Objective:** The primary metric for this local experiment is match win points (win = 1.0, tie = 0.5, loss = 0.0) [not coin margins or terminal bank balances].
* **Full Confirmation Panel (128 Appearances per Finalist):**
  * Baseline **`prvsiyan_moon_counts_melons`**: **86-40-2** across 128 games (points rate **0.6796875**).
  * Challenger **`prvsiyan_global_sell_slot_challenger`**: **102-24-2** across 128 games (points rate **0.8046875**).
  * Points rate difference (challenger minus baseline): **+0.1250** (+12.5 percentage points).
  * Paired points-rate differences across the eight confirmation seeds in order: `[0.125, 0.125, 0.125, 0.125, 0.25, 0.125, 0.0, 0.125]`.
  * Across 10,000 whole-seed cluster bootstrap resamples (RNG seed `20260926`), the 95% percentile confidence interval is **`[0.078125, 0.171875]`**; the stated whole-seed bootstrap interval excludes zero for this eight-seed panel, without generalizing beyond it.
* **Direct Head-to-Head Decisiveness (16 Matches Across Both Seats):**
  * Challenger defeated baseline **14-0-2** (points rate **0.9375** vs **0.0625**, delta **+0.8750**).
  * Seed-cluster bootstrap 95% confidence interval (10,000 resamples, RNG seed `42`): **`[0.625, 1.0]`**.
  * Challenger achieved a 2-0-0 sweep in seven confirmation seeds, and a 0-0-2 tie in seed `758639642`.
* **Secondary Outcomes:** Terminal cash differences were negligible (challenger mean cash $106,112.50 vs baseline $106,076.39; mean margin -$354.47 vs -$423.95). The panel shows higher points alongside close pooled mean cash and does not establish mechanism.
* **Screening Status (Incomplete & Unaudited):** Exploratory screening planned four seeds. Three shards (`453711617`, `239535007`, `647805795`) were audited and verified. A fourth shard (`screening_seed_924705151.json`) was generated locally (exit code 0), but is deliberately excluded from the tracked evidence bundle because its raw audit was not completed and it remains unaudited and uninspected under the audit gate. Phase 1 screening remains incomplete; no aggregate summary or screening-leader claim exists.
* **Runtime Gate & Dedicated Sequential Profiles:**
  * *Runner Timing Instrumentation Correction:* A later code review identified that `scripts/run_agent_selection_tournament.py` originally used `time.time()` for elapsed callback and match intervals (wall-clock timing rather than monotonic interval timing). It is not known whether wall-clock adjustments affected any particular historical value; do not attribute previous spikes to clock changes. The runner now uses monotonic `time.perf_counter()` for all five elapsed-interval reads; the UTC metadata timestamp using `time.strftime/time.gmtime` is unchanged. Four deterministic interval tests were added for callback success/error and run-match normal/runner-exception intervals, with all 29 focused tournament tests, 13 P2 helper tests, and 93 full workspace tests passing.
  * *Authoritative Monotonic Profile Rerun (Four-Seed Characterization):* A dedicated sequential repeat using monotonic timing was executed on the first four predeclared confirmation seeds (`[225915100, 563508405, 707885790, 895731764]`, 120 matches, 64 appearances and 46,016 callbacks per finalist, raw shards: `serial_profile_monotonic_seed_<seed>.json`). It serves as runtime characterization only, not additional strategy evidence. Exact parity was confirmed: 120/120 matches valid, all 240 player statuses `DONE`, manifest/source hashes matched, 0 agent/callback errors, and all match outcomes, points, cash, margins, and non-timing finalist telemetry matched original same-seed runs exactly (`_UPGRADE_STATS/max_planning_ms` is timing telemetry and may differ).
  * *Authoritative Monotonic Profile Results:*
    * Baseline **`prvsiyan_moon_counts_melons`**: 18/46,016 callbacks >100 ms (0.03912%); max callback duration 303.34 ms; mean per-match p95 2.648 ms; max per-match p95 3.06 ms; mean match duration 5.264 s.
    * Challenger **`prvsiyan_global_sell_slot_challenger`**: 14/46,016 callbacks >100 ms (0.03042%); max callback duration 248.52 ms; mean per-match p95 2.560 ms; max per-match p95 3.08 ms; mean match duration 5.166 s.
    * Challenger P2 telemetry in this subset: 46,016 `p2_calls`, 32,192 `eligible_turns`, 15,974 evaluations, 0 `budget_hits`, 126 `changed_turns`, 320 `changed_slots`, 0 `p2_errors`.
  * *Exploratory Attribution Note (Unresolved Mechanism):* In this monotonic subset, the baseline's internal planner metric `_UPGRADE_STATS.max_planning_ms` reached a maximum of 299.247 ms (with >100 ms planner timing in 4/64 appearances), whereas the challenger's planner metric reached a maximum of 33.362 ms (none >100 ms), yet callback exceedances persisted. For the challenger, per-match max callback and aggregate `p2_evals` showed a descriptive Pearson $r = 0.243$, with over-threshold appearances averaging 289.86 P2 evaluations versus 238.32 in clear appearances. Because the runner lacks per-callback sub-component timing, these aggregate observations do not establish the optimizer as cause, and attribution remains unresolved.
  * *Superseded Legacy Non-Monotonic Data:* Earlier eight-seed confirmation latency figures (28/25 calls >100 ms; max 307.18/340.63 ms) and the initial four-seed profile rerun (`serial_profile_seed_*.json`, 17/17 calls >100 ms; max 325.06/246.80 ms) were produced before the monotonic-clock fix. These historical outputs are retained intact but labeled legacy/non-monotonic and superseded for latency-gate conclusions. Strategy outcome evidence remains unchanged and separate from runtime metrics.
  * *Guideline Assessment:* The workspace standard (`GEMINI.md`) defines a guideline of `<100 ms` per callback. This is an internal engineering benchmark to prevent timeout risks on live servers, not an official Kaggle API constraint. Because both finalists still exceed the `<100 ms` guideline under authoritative monotonic profiling, the guideline is not cleared.
* **Operational Decision:** Retain the challenger strictly as an **experiment-only candidate**. No promotion to active baseline or live submission because both arms still exceed the workspace `<100 ms` guideline in dedicated sequential monotonic profiling, Phase 1 screening remains incomplete (shard `screening_seed_924705151.json` was generated locally but is excluded from the tracked evidence bundle under the audit gate and remains unaudited and uninspected), and a profile repeat after any latency optimization is needed before promotion can be considered. No Kaggle upload/submission/package operation, live performance change, or active-source modification occurred.
* **Pre-Commit Code Review Findings & Corrected V2 Candidate:** Following the initial experiment, a pre-commit review identified defects in the V1 challenger and helper:
  1. `find_eligible_sell_indices` lacked strict positive integer quantity validation (accepting two-field SELLs or invalid quantity coercions). V2 enforces strict positive integer quantity validation, rejecting bool, float, or string coercions.
  2. `optimize_sell_slots` used `itertools.permutations` with post-generation deduplication, unnecessarily exhausting identical-order permutations and hitting candidate budgets inefficiently; furthermore, failed scorer attempts did not properly consume evaluation budgets. V2 generates unique multiset permutations directly and ensures that all candidate evaluation attempts—including failed scorer attempts—strictly consume the candidate budget.
  3. The V1 challenger imported the helper via standard Python `sys.path`, risking import shadowing and verification mismatch. V2 implements verified direct-byte loader isolation with cleanup of nested `sys.modules` entries, verified by comprehensive `sys.modules` and `sys.path` shadow tests.
  A corrected V2 candidate (`docs/experiments/agent_selection/p2_market_slot_ordering/sources/prvsiyan_global_sell_slot_challenger_reviewed/main.py`) and reviewed helper (`scripts/p2_market_slot_optimizer_reviewed.py`, SHA256 pinned to `6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59`) resolve these issues. As of the latest run, code/regression verification confirms focused V2 tests 12/12 pass (`tests/test_p2_market_slot_optimizer_reviewed.py`), full workspace pytest collected 105 and all 105 pass, and scoped Black/Ruff pass on 9 selected Python files. The historical 93/93 test count reflects the pre-V2 full-suite baseline and is preserved to distinguish past verification state from current results. **Crucially, V2 remains code/regression tested only: no tournament evaluation, no V2 profile, and no performance or promotion claims.** All historical P2 tournament outcomes, telemetry, and screening audits in this report apply strictly to the exact V1 byte hashes and are retained entirely unchanged as historical provenance, with V1 source hashes preserved. Phase 1 screening remains incomplete with no aggregate summary or screening-leader claim, and the absolute no-inspection and no-retry gate on `screening_seed_924705151.json` remains in full effect.

---

## 1. Experimental Design & Byte-Pinned Provenance

### 1.1 Simulation Engine & Environment
* **Engine:** `kaggle-environments` version `1.32.7`.
* **Episode Horizon:** 720 discrete simulation turns per match.
* **Scoring Standard:** The primary metric for this local experiment is match win points (win = 1.0, tie = 0.5, loss = 0.0). Coin totals and margins are secondary diagnostics.
* **Isolation:** The P2 challenger is an isolated, experiment-only candidate. Active submission files (`submission/submission.py`, `submission/decoy.py`) and active competitor source files are unmodified.

### 1.2 Byte-Pinned Candidate Manifest & Sources
All candidate artifacts are byte-pinned in [`candidates.json`](candidates.json) (SHA256: `2f4566e93d5b280aef0b4468ae775783c086a14bb5a97f32b46837d8f311e39e`):

| Artifact Role | Identifier | File Path | SHA256 Digest |
| :--- | :--- | :--- | :--- |
| Candidate Manifest | `p2_manifest` | [`candidates.json`](candidates.json) | `2f4566e93d5b280aef0b4468ae775783c086a14bb5a97f32b46837d8f311e39e` |
| Frozen Baseline Source | `prvsiyan_moon_counts_melons` | [`../sources/prvsiyan_moon_counts_melons/main.py`](../sources/prvsiyan_moon_counts_melons/main.py) | `178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a` |
| Challenger Source | `prvsiyan_global_sell_slot_challenger` | [`sources/prvsiyan_global_sell_slot_challenger/main.py`](sources/prvsiyan_global_sell_slot_challenger/main.py) | `4fb031794f945318310e143b1fb5609502c12d5bfb153009d6bfe8b0d34077b8` |
| Helper Module | `p2_market_slot_optimizer` | [`../../../../scripts/p2_market_slot_optimizer.py`](../../../../scripts/p2_market_slot_optimizer.py) | `1b97d5cc9fff730b9c0e529e48018891536c516b8425ffc9b2e8ffc2038de94a` |

### 1.3 Challenger Mechanism
The P2 challenger implements bounded permutation search over eligible `SELL` slots within each turn's market action vector:
* Only existing eligible `SELL` indices are reordered.
* Non-`SELL`, blank, and Turn-0 wash slots are preserved in place.
* The multiset of quantities and commodities is preserved exactly.
* Search is bounded by an evaluation budget to prevent runtime runaway.

### 1.4 Predeclared Evaluation Protocol
The manifest established a two-stage evaluation protocol:
1. **Screening (Phase 1):** Exploratory round robin across nine candidates over four seeds.
2. **Confirmation (Phase 2):** Predeclared baseline-vs-challenger evaluation over eight fresh held-out seeds across both seats against each other and seven frozen benchmark opponents, **regardless of exploratory screening rank**.

---

## 2. Phase 1: Screening Status (Incomplete & Unaudited)

Screening was designed as an exploratory 9-candidate round-robin tournament across four planned seeds: `[453711617, 239535007, 924705151, 647805795]`. Each completed seed job produced a 72-match shard.

### 2.1 Audited Screening Shards
Three screening shards were formally audited and verified:
* [`screening_seed_453711617.json`](screening_seed_453711617.json) (72 matches)
* [`screening_seed_239535007.json`](screening_seed_239535007.json) (72 matches)
* [`screening_seed_647805795.json`](screening_seed_647805795.json) (72 matches)

For these three shards only (216 audited matches total):
* Exact 72-match matrix and seat coverage were verified.
* All player terminal statuses were `DONE`.
* Manifest and source SHA256 hashes matched.
* Zero agent errors, callback exceptions, or invalid matches occurred.
* A separate exploratory smoke run is excluded from all counts.

### 2.2 Unaudited Shard & Incomplete Status
The raw file `screening_seed_924705151.json` was generated locally (process exited with code 0), but it is deliberately excluded from the tracked evidence bundle because its raw audit was not completed and it remains unaudited and uninspected under the audit gate:
* Its raw verification audit was not completed.
* In accordance with data integrity mandates and the critical audit gate, this shard was not opened, read, parsed, aggregated, summarized, or inspected.
* No data from this shard is included in any metric, summary, or tracked repository commit.
* Consequently, Phase 1 screening **remains incomplete**.
* No screening summary file exists, and **no screening-leader claim is made**.

---

## 3. Phase 2: Confirmation Tournament Results

Confirmation was executed on an untouched, held-out panel of eight seeds:
`[225915100, 563508405, 707885790, 895731764, 955397235, 812292840, 758639642, 352111692]`.

### 3.1 Confirmation Audit & Integrity
The raw confirmation results were verified across all eight shard files and aggregated in [`confirmation_summary.json`](confirmation_summary.json):
* **Scale:** Exactly 8 seeds $\times$ 30 matches/seed = **240 matches total** (480 player appearances).
* **Appearances:** Each finalist (`prvsiyan_moon_counts_melons` and `prvsiyan_global_sell_slot_challenger`) appeared 16 times per seed (**128 appearances each**). Each of the seven frozen non-finalist opponents appeared 4 times per seed (**32 appearances each**).
* **Execution Integrity:** All 240 matches were valid; all 480 player appearances ended with terminal status `DONE`; scoring basis was `coins`; zero runner or callback errors occurred.
* **Byte Integrity:** Manifest hash matched `2f4566e93d5b280aef0b4468ae775783c086a14bb5a97f32b46837d8f311e39e` in all records.

### 3.2 Primary Outcome: Match-Points Rate
The primary metric for this local experiment is match win points (win = 1.0, tie = 0.5, loss = 0.0), not cash margins.

| Finalist Candidate | Record (W-L-T) | Appearances | Match Points | Points Rate | 95% Seed-Cluster CI | Win Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `prvsiyan_global_sell_slot_challenger` | **102-24-2** | 128 | 103.0 | **0.8046875** | `[0.7265625, 0.8828125]` | 0.796875 |
| `prvsiyan_moon_counts_melons` | **86-40-2** | 128 | 87.0 | **0.6796875** | `[0.578125, 0.765625]` | 0.671875 |

#### Paired Whole-Roster Difference
* **Point Estimate Delta ($\Delta = \text{Challenger} - \text{Baseline}$):** $+16.0 / 128 = \mathbf{+0.125000}$ (+12.5 percentage points).
* **Seed-Level Paired Deltas (in seed order):**
  * Seed `225915100`: $+0.125$
  * Seed `563508405`: $+0.125$
  * Seed `707885790`: $+0.125$
  * Seed `895731764`: $+0.125$
  * Seed `955397235`: $+0.250$
  * Seed `812292840`: $+0.125$
  * Seed `758639642`: $+0.000$
  * Seed `352111692`: $+0.125$
* **Bootstrap Uncertainty:** Across 10,000 whole-seed cluster bootstrap resamples (RNG seed `20260926`), the 95% percentile confidence interval is **`[0.078125, 0.171875]`**. The stated whole-seed bootstrap interval excludes zero for this eight-seed panel, without generalizing beyond it.

### 3.3 Direct Head-to-Head Comparison
The two finalists met in 16 direct head-to-head matches (2 games per seed, evaluating both seat orientations):
* **Challenger Record:** **14-0-2** (14 wins, 0 losses, 2 ties).
* **Baseline Record:** **0-14-2** (0 wins, 14 losses, 2 ties).
* **Points Rates:** Challenger **0.9375** vs Baseline **0.0625** (Delta: **+0.8750**).
* **Seed-Cluster Bootstrap 95% CI:** **`[0.6250, 1.0000]`** (10,000 resamples, RNG seed `42`).
* **Seed-by-Seed Challenger H2H Breakdown:**
  * Seeds `225915100`, `563508405`, `707885790`, `895731764`, `955397235`, `812292840`, `352111692`: Challenger **2-0-0** in each seed.
  * Seed `758639642`: Both games tied (**0-0-2**).

### 3.4 Per-Opponent Matchup Breakdown
Each finalist played exactly 16 matches against each opponent (8 seeds $\times$ 2 seat orientations). Records indicate the named candidate's W-L-T record:

| Opponent | Baseline W-L-T | Challenger W-L-T | Baseline Points Rate | Challenger Points Rate | Delta ($\text{Challenger} - \text{Baseline}$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `shepherd_sovereign` | 14-2-0 | 14-2-0 | 0.8750 | 0.8750 | 0.0000 |
| `jaxa_2802_variant_b` | 2-14-0 | 2-14-0 | 0.1250 | 0.1250 | 0.0000 |
| `peak_2950` | 16-0-0 | 16-0-0 | 1.0000 | 1.0000 | 0.0000 |
| `v57_invariant` | 14-2-0 | 16-0-0 | 0.8750 | 1.0000 | +0.1250 |
| `thomas_2945_farm` | 14-2-0 | 14-2-0 | 0.8750 | 0.8750 | 0.0000 |
| `cha22_multi_route` | 16-0-0 | 16-0-0 | 1.0000 | 1.0000 | 0.0000 |
| `arsgorynich_herd_safe_v3` | 10-6-0 | 10-6-0 | 0.6250 | 0.6250 | 0.0000 |
| Direct H2H (vs Each Other) | 0-14-2 | 14-0-2 | 0.0625 | 0.9375 | +0.8750 |
| **Total Panel Record** | **86-40-2** | **102-24-2** | **0.6796875** | **0.8046875** | **+0.125000** |

*Key Matchup Observations:*
1. **Source of Panel Advantage:** Against six of the seven external opponents (`shepherd_sovereign`, `jaxa_2802_variant_b`, `peak_2950`, `thomas_2945_farm`, `cha22_multi_route`, and `arsgorynich_herd_safe_v3`), the challenger and baseline produced **identical W-L-T records**.
2. **External Opponent Gain:** The challenger gained +2 wins against `v57_invariant` (16-0-0 vs 14-2-0, +2 points).
3. **Direct H2H Gain:** The challenger gained +14 points in direct competition (14-0-2 vs 0-14-2, +14 points).
4. **Observed Jaxa Result:** Both candidates recorded an observed 2-14-0 result against the frozen `jaxa_2802_variant_b` candidate.

### 3.5 Secondary Financial Outcomes
Financial outcomes were tracked across all 128 appearances per finalist:

| Candidate | Mean Cash ($) | 95% Seed-Cluster CI ($) | Mean Margin ($) | 95% Seed-Cluster CI ($) | Mean Opponent Cash ($) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `prvsiyan_global_sell_slot_challenger` | $106,112.50 | `[88240.27, 123649.55]` | -$354.47 | `[-1414.86, +989.56]` | $106,466.97 |
| `prvsiyan_moon_counts_melons` | $106,076.39 | `[88419.94, 123762.58]` | -$423.95 | `[-1462.25, +960.19]` | $106,500.34 |
| **Difference ($\text{Challenger} - \text{Baseline}$)** | **+$36.11** | — | **+$69.48** | — | **-$33.38** |

*Diagnostic Caveat:* The mean terminal cash difference is negligible (+$36.11 coins, a 0.034% shift). The panel shows higher points alongside close pooled mean cash and does not establish mechanism. Cash results do not identify the causal mechanism.

---

## 4. Telemetry & Runtime Latency

### 4.1 Authoritative Monotonic Sequential Profile (Current Characterization)

#### 4.1.1 Runner Clock Instrumentation Correction (`time.perf_counter()`)
A post-experiment code review revealed that `scripts/run_agent_selection_tournament.py` originally used Python's `time.time()` for callback and match elapsed intervals. `time.time()` measures wall-clock time rather than monotonic interval time and is subject to potential system clock adjustments. It is not known whether wall-clock adjustments affected any particular historical value, and previous latency spikes should not be attributed to clock changes.

The tournament runner has been updated to use monotonic `time.perf_counter()` for all five replaced `time.time()` call sites:
1. Callback start
2. Callback success end
3. Callback exception end
4. Match start
5. Match end

The UTC metadata timestamp field (which records execution start time using `time.strftime` and `time.gmtime`) remains unchanged. Four deterministic unit tests were added to verify interval recording for callback success, callback error, normal match completion, and runner exception paths.

#### 4.1.2 Purpose, Execution Context & Exact Parity Verification
* **Purpose:** A new monotonic-clock profile-only repeat was executed sequentially across the first four predeclared confirmation seeds `[225915100, 563508405, 707885790, 895731764]` to provide an authoritative runtime characterization. This run serves strictly as runtime characterization, not additional strategy evidence.
* **Execution Context:** The run evaluated the exact fixed confirmation pair (`prvsiyan_moon_counts_melons` and `prvsiyan_global_sell_slot_challenger`) alongside the seven frozen benchmark opponents in a single sequential shell batch (pre-run check confirmed no concurrent tournament, pytest, or profiling processes; this does not claim the entire host was idle or OS-isolated).
* **Schedule & Integrity:** Exactly 30 matches per seed (120 matches total). All 120 matches were valid; all 240 player terminal statuses were `DONE`; candidate manifest and source SHA256 hashes matched; zero agent or callback errors occurred. Each finalist logged 64 appearances and 46,016 callbacks.
* **Match Outcome & Telemetry Parity:** All underlying match outcomes (wins, losses, ties), match win points, terminal cash balances, margins, and non-timing finalist telemetry matched the original confirmation runs and earlier profile runs exactly. The only telemetry field differing from earlier runs was the internal timing metric `_UPGRADE_STATS/max_planning_ms`.
* **Challenger P2 Telemetry (Monotonic Four-Seed Profile Subset):**
  * Optimizer invocations (`p2_calls`): 46,016
  * Turns with eligible sell actions (`eligible_turns`): 32,192
  * Candidate permutations evaluated (`evaluated_candidates`): 15,974
  * Evaluation budget limits reached (`budget_hits`): 0
  * Reordered action turns (`changed_turns`): 126
  * Reordered action slots (`changed_slots`): 320
  * Optimizer errors (`p2_errors`): 0

#### 4.1.3 Authoritative Monotonic Profile Latency Results
Callback duration distributions across the 46,016 callbacks per finalist in the monotonic profile run are summarized below:

| Finalist Candidate | Total Callbacks | Callbacks >100 ms | Tail Incident Rate (>100 ms) | Max Callback Duration | Mean Per-Match p95 | Max Per-Match p95 | Mean Match Duration |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prvsiyan_moon_counts_melons` | 46,016 | 18 | 0.03912% | 303.34 ms | 2.648 ms | 3.06 ms | 5.264 s |
| `prvsiyan_global_sell_slot_challenger` | 46,016 | 14 | 0.03042% | 248.52 ms | 2.560 ms | 3.08 ms | 5.166 s |

#### 4.1.4 Exploratory Attribution Note (Unresolved Mechanism)
An exploratory examination of internal telemetry was conducted to investigate potential sources of callback spikes:
* **Internal Planner Metric (`_UPGRADE_STATS.max_planning_ms`):** Baseline maximum planner timing reached **299.247 ms**, with planner timing exceeding 100 ms in 4 of 64 appearances. In contrast, challenger maximum planner timing reached only **33.362 ms**, with zero appearances exceeding 100 ms. Despite the challenger's internal planner never reporting >100 ms, callback-level exceedances (>100 ms) still occurred in 14 callbacks across the challenger's appearances.
* **Challenger Evaluation Load Correlation:** Across the challenger's 64 appearances, the correlation between per-match maximum callback duration and total evaluated candidates (`p2_evals`) had a descriptive Pearson correlation coefficient of $r = 0.243$. Appearances that recorded at least one callback over the 100 ms threshold averaged **289.86** P2 evaluations, compared to **238.32** P2 evaluations in clear appearances.
* **Attribution Boundary:** These aggregate observations do not establish the optimizer as the cause of tail latency. The tournament runner measures overall callback duration at the interface boundary and lacks per-callback sub-component timing (e.g., separating policy decision logic, environment parsing, and optimizer search). Consequently, sub-component attribution remains **unresolved and not inferred**.

#### 4.1.5 Profile Interpretation & Latency Gate Assessment
* **Guideline Not Cleared:** The workspace standard (`GEMINI.md`) defines an internal engineering guideline of `<100 ms` per callback to mitigate match timeout risk on live simulation servers; this is not an official Kaggle API constraint. Under authoritative monotonic profiling, both finalists still record tail exceedances (18 for baseline, 14 for challenger), so the workspace `<100 ms` guideline is not cleared.
* **Separation of Concerns:** This profile repeat serves exclusively as runtime characterization. It adds no new strategy evidence, does not alter Phase 1 screening status, and does not establish live performance.

---

### 4.2 Legacy & Superseded Non-Monotonic Latency Diagnostics (Historical Record)

All runtime metrics reported below were collected prior to the monotonic-clock instrumentation fix and reflect legacy wall-clock timing (`time.time()`). They are retained for provenance and historical completeness but are superseded by the monotonic profile results above for latency-gate conclusions. Strategy outcome evidence remains unaffected and separate from runtime metrics.

#### 4.2.1 Eight-Seed Confirmation Tournament Telemetry & Legacy Non-Monotonic Latency Audit
In the full eight-seed confirmation panel (240 matches, 92,032 callbacks per finalist across all eight seeds):
* **Full-Panel Optimizer Activity:**
  * Optimizer invocations (`p2_calls`): 92,032
  * Turns with eligible sell actions (`eligible_turns`): 64,384
  * Candidate permutations evaluated (`evaluated_candidates`): 49,878
  * Reordered action turns (`changed_turns`): 232
  * Reordered action slots (`changed_slots`): 606
  * Evaluation budget limits reached (`budget_hits`): 6
  * Optimizer errors (`p2_errors`): 0
* **Inventory & Purchasing Telemetry:**
  * `cattle_failed_purchase_units`: exactly **66** for both baseline and challenger (identical failure counts occurring across specific test seeds).
  * Worker hire shortfalls: 0
  * Sheep purchase shortfalls: 0
  * Sheep hire shortfalls: 0
  * Crop input stock shortfalls: 0
* **Legacy Wall-Clock Latency Metrics (Superseded):**

| Candidate | Total Callbacks | Callbacks >100 ms | Tail Incident Rate | Max Callback Duration | Mean Game Duration |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `prvsiyan_moon_counts_melons` | 92,032 | 28 | 0.030% | 307.18 ms | 5.39 s |
| `prvsiyan_global_sell_slot_challenger` | 92,032 | 25 | 0.027% | 340.63 ms | 5.29 s |

*Note:* Seed jobs were executed sequentially in a single shell batch without concurrent P2 jobs. Timings reflect normal tournament matches rather than a dedicated serial profile benchmark.

#### 4.2.2 Initial Four-Seed Sequential Profile Rerun (Superseded Legacy Non-Monotonic Shards)
An initial sequential profile rerun over the first four confirmation seeds (`serial_profile_seed_*.json`) was conducted prior to the monotonic clock fix using legacy timing:

| Finalist Candidate | Total Callbacks | Callbacks >100 ms | Tail Incident Rate | Max Callback Duration | Mean Per-Match p95 | Max Per-Match p95 | Mean Match Duration |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prvsiyan_moon_counts_melons` | 46,016 | 17 | 0.03694% | 325.06 ms | 2.717 ms | 3.21 ms | 5.431 s |
| `prvsiyan_global_sell_slot_challenger` | 46,016 | 17 | 0.03694% | 246.80 ms | 2.635 ms | 3.19 ms | 5.334 s |

These initial profile shards are superseded for latency-gate decisions by the monotonic rerun in Section 4.1.

---

## 5. Verification & Test Suite Evidence

The P2 implementation, runner timing fixes, confirmation artifacts, and V2 review fixes were validated through automated test suites:
* **Runner Timing & Interval Tests:** Four deterministic unit tests added in `tests/test_agent_selection_tournament.py` verifying interval measurements across callback success, callback error, normal match completion, and runner exception paths using monotonic `time.perf_counter()`.
* **Focused Tournament Tests:** `tests/test_agent_selection_tournament.py` alone passed all **29/29** tests.
* **Historical P2 (V1) Unit & Regression Tests:** `tests/test_p2_market_slot_optimizer.py` passed all **13/13** tests.
* **Historical Pre-V2 Full Workspace Test Suite:** `.venv/bin/pytest -q` passed all **93/93** tests (preserved as the historical baseline count prior to V2).
* **Current V2 Unit & Regression Tests:** `tests/test_p2_market_slot_optimizer_reviewed.py` passed all **12/12** focused tests, validating strict positive integer quantity validation (rejecting bool/float/string coercions), failed scorer attempts consuming candidate evaluation budget, verified direct-byte loader cleanup of nested `sys.modules` entries, and `sys.modules`/`sys.path` shadow tests.
* **Current Full Workspace Test Suite:** Full workspace pytest collected 105 tests, and all **105/105** passed, distinguished from the historical pre-V2 93/93 baseline.
* **Scoped Linting & Formatting:** Scoped `ruff check` and `black --check` passed cleanly on 9 selected Python files (including `scripts/run_agent_selection_tournament.py`, `tests/test_agent_selection_tournament.py`, `scripts/p2_market_slot_optimizer.py`, `sources/prvsiyan_global_sell_slot_challenger/main.py`, `tests/test_p2_market_slot_optimizer.py`, `scripts/validate_replay_parity.py`, `tests/test_replay_parity.py`, `scripts/p2_market_slot_optimizer_reviewed.py`, and `tests/test_p2_market_slot_optimizer_reviewed.py`).
* **Git Cleanliness:** `git diff --check` passed cleanly with zero whitespace or line-ending anomalies.
* **Legacy Codebase Note:** Repo-wide Ruff and Black checks report pre-existing legacy formatting issues on unrelated files; these files were intentionally preserved and not mass-modified.
* **Confirmation Data Audit:** [`confirmation_summary.json`](confirmation_summary.json) was independently reconciled against all eight raw shard files.
* **V2 Verification Scope:** V2 remains code/regression tested only: no tournament evaluation, no V2 profile, and no performance or promotion claims.

---

## 6. Methodological Insights

### 6.1 Screening vs Confirmation Protocol
* **Screening as Exploratory Filter:** Phase 1 screening evaluates a broad candidate roster across a compact seed panel to discover promising candidate variants.
* **Confirmation as Predeclared Hypothesis Test:** Phase 2 confirmation benchmarks predeclared finalists on fresh, held-out seeds. By fixing the confirmation pair in advance within the manifest, the evaluation avoids post-hoc selection bias.

### 6.2 The Imperative of Whole-Seed Cluster Bootstrapping
Standard independent-match bootstrapping treats each game as an independent, identically distributed observation. In simulation tournaments, a match-level bootstrap resampling individual games as independent would ignore the paired seed/seat structure and can understate uncertainty:
1. **Environmental Confounding:** Matches sharing a random seed share the same market volatility curves, farm terrain, and initial crop prices.
2. **Seat-Swapped Symmetry:** Evaluating both Seat 0 and Seat 1 for each pairing within a seed produces correlated paired outcomes.
3. **Variance Estimation:** Whole-seed resampling keeps all seed-linked matches together, preserving internal correlation structures and yielding valid uncertainty bounds.

### 6.3 Match Points and Cash Metrics
The primary metric for this local experiment is match win points (win = 1.0, tie = 0.5, loss = 0.0), not terminal cash balances or margins. The panel shows higher points alongside close pooled mean cash and does not establish mechanism. Cash totals do not identify the causal driver of the observed match results.

---

## 7. Limitations & Operational Decision

### 7.1 Limitations
1. **Frozen Panel Scope:** Findings reflect performance exclusively against the nine-candidate roster and eight seeds (each finalist played the other finalist plus seven frozen opponents) specified in the byte-pinned manifest. No inference to the unobserved distribution of live Kaggle ladder competitors is warranted.
2. **Incomplete Screening:** Phase 1 screening was not fully audited; `screening_seed_924705151.json` was generated locally but is deliberately excluded from the tracked evidence bundle under the audit gate and remains unaudited and uninspected.
3. **Runtime Tail Spikes & Unmet Guideline:** Both the baseline and challenger exceeded the workspace `<100 ms` guideline (`GEMINI.md`) under authoritative monotonic profiling across 46,016 callbacks per finalist (baseline: 18 callbacks >100 ms, max 303.34 ms; challenger: 14 callbacks >100 ms, max 248.52 ms; legacy non-monotonic figures recorded 17/17 in the initial profile and 28/25 in 8-seed confirmation). The workspace guideline is an internal engineering benchmark, not an official Kaggle API limit. The causal attribution of tail spikes remains unresolved due to runner-level instrumentation boundaries.
4. **Observed Jaxa Result:** Both baseline and challenger recorded an observed 2-14-0 result against the frozen `jaxa_2802_variant_b` candidate.

### 7.2 Operational Decision
* **Candidate Status:** Retain `prvsiyan_global_sell_slot_challenger` strictly as an **experiment-only candidate**.
* **Operational Recommendation (No Promotion):** No promotion to active baseline or live submission because:
  1. Both arms still exceed the workspace `<100 ms` callback guideline (`GEMINI.md`) in dedicated sequential monotonic profiling.
  2. Phase 1 exploratory screening remains incomplete (shard `screening_seed_924705151.json` was generated locally but is excluded from the tracked evidence bundle under the audit gate and remains unaudited and uninspected).
  3. A profile repeat after any latency optimization is needed before promotion can be considered.
* **No-Submission & Scope Statement:** No Kaggle upload/submission/package operation, live performance change, or active-source modification occurred. Do not claim official Kaggle runtime limits or live performance changes.

---

## 8. Reproducibility & Artifact Links

Audited confirmation/profile artifacts and audited screening artifacts are included in the tracked evidence bundle; the specifically named fourth local screening artifact `screening_seed_924705151.json` is excluded because it remains unaudited/uninspected under the gate.

### Manifest & Sources
* Manifest: [`candidates.json`](candidates.json) (SHA256: `2f4566e93d5b280aef0b4468ae775783c086a14bb5a97f32b46837d8f311e39e`)
* Baseline Source: [`../sources/prvsiyan_moon_counts_melons/main.py`](../sources/prvsiyan_moon_counts_melons/main.py) (SHA256: `178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a`)
* Challenger Source: [`sources/prvsiyan_global_sell_slot_challenger/main.py`](sources/prvsiyan_global_sell_slot_challenger/main.py) (SHA256: `4fb031794f945318310e143b1fb5609502c12d5bfb153009d6bfe8b0d34077b8`)
* Helper Script: [`../../../../scripts/p2_market_slot_optimizer.py`](../../../../scripts/p2_market_slot_optimizer.py) (SHA256: `1b97d5cc9fff730b9c0e529e48018891536c516b8425ffc9b2e8ffc2038de94a`)

### Authoritative Monotonic Sequential Runtime Profile Shards (Four-Seed Profile-Only Repeat)
* Seed 225915100 Monotonic Profile: [`serial_profile_monotonic_seed_225915100.json`](serial_profile_monotonic_seed_225915100.json)
* Seed 563508405 Monotonic Profile: [`serial_profile_monotonic_seed_563508405.json`](serial_profile_monotonic_seed_563508405.json)
* Seed 707885790 Monotonic Profile: [`serial_profile_monotonic_seed_707885790.json`](serial_profile_monotonic_seed_707885790.json)
* Seed 895731764 Monotonic Profile: [`serial_profile_monotonic_seed_895731764.json`](serial_profile_monotonic_seed_895731764.json)
*(Authoritative monotonic `time.perf_counter()` sequential callback-profile runs repeating the first four confirmation seeds; runtime characterization only, not strategy evidence).*

### Superseded Legacy Non-Monotonic Runtime Profile Shards (Historical Record)
* Seed 225915100 Legacy Profile: [`serial_profile_seed_225915100.json`](serial_profile_seed_225915100.json)
* Seed 563508405 Legacy Profile: [`serial_profile_seed_563508405.json`](serial_profile_seed_563508405.json)
* Seed 707885790 Legacy Profile: [`serial_profile_seed_707885790.json`](serial_profile_seed_707885790.json)
* Seed 895731764 Legacy Profile: [`serial_profile_seed_895731764.json`](serial_profile_seed_895731764.json)
*(Superseded initial profile runs using legacy non-monotonic timing; preserved for historical auditability).*

### Confirmation Summary & Raw Shards (Audited)
* Aggregate Confirmation Summary: [`confirmation_summary.json`](confirmation_summary.json)
* Seed 225915100: [`confirmation_seed_225915100.json`](confirmation_seed_225915100.json)
* Seed 563508405: [`confirmation_seed_563508405.json`](confirmation_seed_563508405.json)
* Seed 707885790: [`confirmation_seed_707885790.json`](confirmation_seed_707885790.json)
* Seed 895731764: [`confirmation_seed_895731764.json`](confirmation_seed_895731764.json)
* Seed 955397235: [`confirmation_seed_955397235.json`](confirmation_seed_955397235.json)
* Seed 812292840: [`confirmation_seed_812292840.json`](confirmation_seed_812292840.json)
* Seed 758639642: [`confirmation_seed_758639642.json`](confirmation_seed_758639642.json)
* Seed 352111692: [`confirmation_seed_352111692.json`](confirmation_seed_352111692.json)

### Screening Raw Shards
* Seed 453711617 (Audited): [`screening_seed_453711617.json`](screening_seed_453711617.json)
* Seed 239535007 (Audited): [`screening_seed_239535007.json`](screening_seed_239535007.json)
* Seed 647805795 (Audited): [`screening_seed_647805795.json`](screening_seed_647805795.json)
* Seed 924705151 (Unaudited / Excluded from Tracked Bundle): `screening_seed_924705151.json` *(Generated locally with exit code 0; raw audit incomplete; excluded from tracked bundle under audit gate; strictly uninspected)*

### V2 Code Review Addendum
The `prvsiyan_global_sell_slot_challenger_reviewed` (V2) variant was generated solely to address static code review findings regarding:
1. **Quantity Validation:** Implementing strict positive integer quantity validation in `find_eligible_sell_indices`, rejecting `bool`, `float`, or string coercions.
2. **Permutation Generation & Budget Accounting:** Replacing redundant `itertools.permutations` with direct unique multiset permutations in `optimize_sell_slots`, and ensuring that all candidate evaluation attempts—including failed scorer attempts—strictly consume the candidate evaluation budget.
3. **Import Isolation & Shadow Prevention:** Replacing standard `sys.path` imports with verified direct-byte loader isolation and explicit cleanup of nested `sys.modules` entries, verified by dedicated `sys.modules` and `sys.path` shadow tests.

**V2 Artifact Digest:**
* Reviewed Helper Module: `scripts/p2_market_slot_optimizer_reviewed.py` (SHA256: `6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59`).

**Latest Verification Results:**
As of the latest run, code/regression verification confirms:
* Focused V2 tests: **12/12** pass (`tests/test_p2_market_slot_optimizer_reviewed.py`).
* Full workspace pytest: collected 105 tests, and all **105/105** pass.
* Historical baseline comparison: The pre-V2 full-suite baseline of **93/93** passing tests is preserved and distinguished from the current 105/105 count.
* Scoped linting and formatting: Scoped `black --check` and `ruff check` pass cleanly on 9 selected Python files.

**Experimental & Operational Boundaries:**
* **Code/Regression Tested Only:** V2 has NOT been tournament-evaluated or profiled; it makes no performance or promotion claims.
* **V1 Provenance Intact:** All historical P2 tournament outcomes, telemetry, and screening audits in this report apply strictly to the exact original V1 byte hashes and are retained entirely unchanged as historical provenance; V1 source hashes are preserved.
* **Phase 1 Incomplete & Audit Gate Intact:** Phase 1 exploratory screening remains incomplete with no aggregate summary or screening-leader claim. The fourth shard `screening_seed_924705151.json` was generated locally (exit code 0) but is excluded from the tracked evidence bundle under the audit gate and remains unaudited and uninspected under the strict no-inspection and no-retry gate.
