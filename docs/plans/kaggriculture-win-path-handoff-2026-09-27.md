# Kaggriculture Win-Path Continuation Handoff

* **Handoff Date:** 2026-09-27
* **Branch:** `research/kaggriculture-experiment-archive-20260926` (base commit `9093a52` pushed and tracking origin)
* **Core Goal:** Maximize final competition performance and final standing in Kaggriculture before competition close (last recorded backlog deadline: 2026-09-30 23:59 UTC, which must be freshly verified against official rules).
* **Document Status:** Grounded operational continuation brief and safety protocol.

---

## 1. At-a-Glance State & Repository Context

### Candid Reality Check
Recent engineering work focused on rigorous offline validation, experiment archival, monotonic runtime profiling, and pre-commit code review. **Critically, no new Kaggle submission was made and no submission-attributable live score or rank improvement came from this work; live standings have not been refreshed.** (Do not assert zero live rating changes overall, as unrefreshed live ratings drift from continuous matchmaking.) While software quality, test coverage, and data integrity were strengthened, these activities fell short of the user's primary goal: winning or securing a medal finish on the competition leaderboard. Offline test passing must never be confused with live competitive superiority. Offline evidence does not establish a likely competition winner.

### Workspace State & Integrity Anchors
* **Repository Commit & Working Tree State:** Git branch `research/kaggriculture-experiment-archive-20260926` has base commit `9093a52` pushed and tracking origin. The current working tree is not clean: tracked files `README.md` and `docs/plans/kaggriculture-public-research-backlog-2026-09-25.md` have uncommitted modifications, while this handoff document (`docs/plans/kaggriculture-win-path-handoff-2026-09-27.md`) is a new untracked file. Separately, the pre-existing prohibited screening shard (`screening_seed_924705151.json`) is an untracked file that remains completely untouched.
* **Test Suite Verification:**
  * Full-workspace pytest: **105 collected, 105 passed**.
  * Historical baseline distinction: The previous **93/93** test count reflects the pre-V2 baseline; the current count of **105/105** incorporates 12 focused regression and isolation tests.
  * Focused P2 V2 unit tests: **12/12 passed** (`tests/test_p2_market_slot_optimizer_reviewed.py`), covering strict integer SELL quantity validation, scorer budget accounting, and direct-byte loader isolation with shadow cleanup.
* **Code Hygiene:** Scoped formatting and linting (`black --check` and `ruff check`) pass cleanly on the 9 selected Python files associated with the experiment archive commit.
* **Code Review:** Independent pre-commit review of the P2 V2 candidate was completed with no blocking defects found.
* **Prohibited Shard Gate (Untracked & Untouched):** The exploratory screening shard (`screening_seed_924705151.json`) is a separate pre-existing untracked file that remains completely untouched in the working tree. It was excluded from the tracked evidence bundle under the audit gate and remains completely unaudited and uninspected. There is a strict, permanent no-inspection, no-retry, and no-tool-access gate on this file.
* **Standing Submission & Promotion Gate:** No promotion, active-source change, or Kaggle upload occurred in this work; the current account active pair has not been freshly queried and must be verified before considering replacement.

---

## 2. What We Learned (Empirical Evidence & Reports)

Detailed findings and primary data are recorded in the dedicated experiment reports:
* **P0 Replay Parity Report:** [`docs/experiments/public_replay_parity_2026-09-25.md`](../experiments/public_replay_parity_2026-09-25.md)
* **P1 Refresh Selection Report:** [`docs/experiments/agent_selection/p1_refresh_2026-09-25/report.md`](../experiments/agent_selection/p1_refresh_2026-09-25/report.md)
* **P2 Market Slot Ordering Report:** [`docs/experiments/agent_selection/p2_market_slot_ordering/report.md`](../experiments/agent_selection/p2_market_slot_ordering/report.md)
* **Public Research & Medal Backlog:** [`docs/plans/kaggriculture-public-research-backlog-2026-09-25.md`](kaggriculture-public-research-backlog-2026-09-25.md)
* **Experiment Version Ledger:** [`docs/experiments.md`](../experiments.md)

### P0 Calibration: Action-Tape Replay Parity (Limited)
* **Evidence:** Exact terminal reward and game status parity was confirmed on three captured public episodes (`113283880`, `113284254`, `113283141`) under local `kaggle-environments==1.32.7` (719 action callbacks per seat, all completing with status `DONE`).
* **Boundary:** Parity was verified strictly for terminal rewards and statuses on these three specific replay episodes. A full field-by-field observation payload diff was **not** performed, and this calibration provides zero evidence of dynamic policy strength or medal viability.

### P1 Candidate Selection: 8 Candidates, Screening & Confirmation
* **Screening (4 seeds, 224 matches):** Arsgorynich Herd-Safe V3 led round-robin screening with a points rate of 0.8929 [0.7857, 1.0000] (50-6-0). Prvsiyan Moon Counts Melons placed second at 0.7143 [0.6071, 0.8214] (40-16-0), advancing to confirmation under the protocol.
* **Confirmation (8 fresh seeds, 208 matches, 112 appearances per finalist):**
  * Point estimates favored Prvsiyan over Arsgorynich (points rate 0.8036 [0.7321, 0.8571], 90-22-0 vs 0.6786 [0.5625, 0.8036], 76-36-0), with Prvsiyan winning direct head-to-head 14-2-0 (+927.9 margin).
  * However, a whole-seed cluster bootstrap across the 8 seeds (10,000 resamples) yielded a paired difference (+0.1250) with a 95% confidence interval of `[-0.0446, +0.2768]`, which **crosses zero**. Therefore, no decisive overall winner was established.
* **Severe Matchup Liability:** Prvsiyan lost **0-16** against Jaxa 2802 Variant B (-14,300.2 average margin), whereas Arsgorynich swept Jaxa **16-0** (+4,428.9 average margin). This 0-16 result vs the frozen Jaxa 2802 Variant B is an observed matchup weakness in that specific local panel, not evidence about Jaxa-style policies in the live meta.

### P2 Market Slot Ordering: V1 Fixed-Pair Confirmation vs Baseline
* **Predeclared Confirmation Panel (8 fresh held-out seeds, 240 matches, 128 appearances per finalist):**
  * Baseline (frozen Prvsiyan): 86-40-2 (points rate 0.6796875).
  * Challenger (V1 bounded permutation search): 102-24-2 (points rate 0.8046875).
  * Paired points rate advantage: **+0.1250** (+12.5 percentage points).
  * 10,000 whole-seed cluster bootstrap 95% CI: **`[0.078125, 0.171875]`**, strictly excluding zero.
  * Direct head-to-head: Challenger defeated baseline **14-0-2** (0.9375 points rate, delta +0.8750).
  * Secondary cash/margin means were close ($106,112.50 vs $106,076.39 mean cash; -$354.47 vs -$423.95 margin), and win points—not terminal cash—remain the decision metric.
* **Crucial Scope Limitation:** This positive confirmation applies solely to the frozen V1 candidate and frozen benchmark panel. It does NOT establish live ladder performance, and does NOT apply to the un-benchmarked V2 candidate.

### P2 Exploratory Screening: Incomplete Under Audit Gate
* Phase 1 exploratory screening planned four seeds (72 matches/shard). Shards 1–3 (`453711617`, `239535007`, `647805795`) passed raw audit (216 matches, all `DONE`, 0 errors).
* The fourth shard (`screening_seed_924705151.json`) was generated locally but excluded from tracked evidence under the audit gate and remains completely unaudited and uninspected.
* Phase 1 screening remains incomplete: no aggregate summary and no screening-leader claim exist.
* **Operational Recommendation:** Abandon this exploratory screening path. If a new V2 experiment is justified, establish a distinct predeclared protocol with fresh independent seeds; do not reuse or aggregate the prohibited shard or rewrite V1 evidence.

### Authoritative Monotonic Profiling (V1 Candidate)
* The tournament runner was updated to measure elapsed intervals with monotonic `time.perf_counter()`.
* Dedicated sequential profiling across the first 4 confirmation seeds (120 matches, 46,016 callbacks per finalist) showed:
  * Baseline: 18 callbacks >100 ms (0.0391%), max 303.34 ms.
  * V1 Challenger: 14 callbacks >100 ms (0.0304%), max 248.52 ms.
  * Zero runtime errors; all game outcomes, points, and non-timing telemetry matched original runs exactly.
  * **Guideline Context:** The `<100 ms` value is an **internal workspace engineering guideline** (`GEMINI.md`) to mitigate timeout risk; it is **NOT** an official Kaggle competition API limit.

### P2 V2 Hardening & Status
* Pre-commit review identified defects in V1 (loose bool/string/float quantity coercions, failed scoring attempts bypassing budget accounting, and import shadow risks).
* V2 implementation (`scripts/p2_market_slot_optimizer_reviewed.py`, SHA256 pinned to `6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59`) addressed the listed review blockers (strict positive integer quantity validation, unique permutation enumeration, failed score budget consumption, and direct-byte loader isolation with nested `sys.modules` cleanup).
* V2 passed 12/12 focused tests and 105/105 workspace pytest, with no blocking findings on the independent re-review (while optional test suggestions from the reviewer were noted).
* **Critical Operational Reality:** V2 is code- and regression-tested ONLY. It has received **no tournament evaluation** and **no runtime profile**. Unit test correctness does not demonstrate playing strength or latency compliance; no performance or promotion claim exists.

---

## 3. What Is NOT Established

1. **No Evidence of Live Competition Superiority:** Offline win rates on fixed local rosters do not prove an agent will gain Elo or outcompete dynamic opponents on the live Kaggle ladder. Furthermore, no new Kaggle submission was made and no submission-attributable live score or rank improvement came from recent work; live standings have not been refreshed and may have drifted independently.
2. **Current Standings Are Unknown:** The recorded historical snapshot from 2026-09-25 15:55 CEST (Prvsiyan `56531885` at 2093.9, Shepherd `56490949` at 2034.7, team rank 1,351 / 10,004; cited provenance: [`docs/plans/kaggriculture-public-research-backlog-2026-09-25.md`](kaggriculture-public-research-backlog-2026-09-25.md)) is historical and stale, not current. Fresh Kaggle queries must determine current live ratings, rankings, and team counts.
3. **No Strategic Dominance:** Neither Prvsiyan nor Shepherd is established as dominant. Prvsiyan's 0-16 result vs the frozen Jaxa 2802 Variant B reflects an observed matchup weakness on that specific local panel, not evidence about the live meta.
4. **V2 Playing Strength and Runtime Viability Are Unproven:** Corrected logic in V2 cannot be assumed to yield the same +0.1250 point rate delta observed in V1, nor can its runtime profile be assumed safe without empirical measurement.
5. **Solo Cash Accumulation Is Not Strategic Strength:** High farm revenue or coin margins in uncontested play do not translate to head-to-head match wins against reactive trading agents.
6. **Final-Eligibility and Post-Deadline Dynamics Require Official Verification:** Live scores are dynamic cumulative ratings, but standings have not been refreshed. While the existing backlog discusses final-eligibility and post-deadline matchmaking dynamics (such as paired active play or rating stabilization), current official competition rules must be confirmed rather than asserted as freshly checked mechanics. Do not assume early matches are wiped or that post-deadline match frequency will automatically multiply without verifying current Kaggle documentation.

---

## 4. Fixed Safety & Evidence Gates

Any succeeding agent or operator must adhere strictly to these non-negotiable boundaries:

1. **Active-Submission & Final-Eligibility Rules (Mandatory Rule Check):** Existing project-research claims assert that Kaggle continuously evaluates only a team's latest two submissions and that submitting a new bot risks retiring the older active submission (freezing its match accumulation). These assertions MUST be checked against current official Kaggle rules before an upload. Treat the risk of displacing a viable active submission as a critical factor to verify. Never upload without verifying current official rules and determining which active slot would be affected. Refreshing fresh submission and leaderboard data via the Kaggle CLI is a mandatory first action.
2. **Explicit User Authorization Gate:** **Zero automated or unprompted Kaggle uploads.** Any submission requires explicit user approval containing the candidate's exact path, Git commit, SHA256 digest, target active slot, expected impact, and rollback plan.
3. **Prohibited Shard Integrity Gate:** The file `screening_seed_924705151.json` is strictly quarantined. No tool may read, inspect, hash, parse, retry, or aggregate this file. All screening claims from that phase remain incomplete and abandoned.
4. **Primary Evaluation Metric:** Match win points rate ($1.0$ for win, $0.5$ for tie, $0.0$ for loss) across paired fresh seeds, alternating seats, and diverse reactive opponents, quantified via whole-seed cluster bootstrap confidence intervals. Coin balances and margins are strictly secondary diagnostics.
5. **Runtime & Operational Safety Gates:**
   * Verification must confirm zero runtime exceptions, zero invalid action penalties, and clean termination (`DONE`) across full 720-turn matches.
   * Standalone packaging must pass import and cold-start verification without third-party namespace leakage.
   * The internal `<100 ms` callback timing guideline (`GEMINI.md`) should not be conflated with the official Kaggle API limit; official execution and timeout constraints must be verified directly against competition documentation.
6. **Preservation of Known-Good Fallback:** Always preserve a tested, byte-pinned baseline agent as a safe fallback before staging or evaluating any new candidate.

---

## 5. Ordered Next Actions Aimed at Maximizing Final Rank

With the recorded submission deadline at **2026-09-30 23:59 UTC** (must be freshly verified against official rules), execute the following ordered pipeline:

1. **Step 1: Refresh Official Live Ground Truth** (Query Kaggle CLI for live submissions, active slots, ratings, rank, and official rules).
2. **Step 2: Freeze Baseline & Select a Single Challenger Focus** (Lock primary fallback; select one challenger hypothesis without branching).
3. **Step 3: Empirical Evaluation of P2 V2** (Dedicated monotonic timing profile and fresh-seed confirmation; evaluate bootstrap interval).
4. **Step 4: Single-Factor Alternative — P3 Herd-Value Selector** (Unimplemented/unevaluated research hypothesis from the backlog, not an existing candidate; optional contingency if P2 V2 is concluded or not promoted, time permitting).
5. **Step 5: Comprehensive Operational & Compliance Packaging** (Standalone packaging via `submission/compile_submission.py`, cold-start test, 720-turn run, license/NOTICE verification).
6. **Step 6: Explicit User Approval & Authorized Deployment Protocol** (Present candidate briefing; require explicit user command; execute upload, read back status, and verify active slots).

### Action 1: Refresh Official Live Ground Truth
* Query the Kaggle CLI to inspect live submissions, episode tallies, error states, and public ratings:
  `kaggle competitions submissions kaggriculture --format json --page-size 100`
* Query the current leaderboard to establish exact team rank, team total, and distance to medal cutoffs:
  `kaggle competitions leaderboard kaggriculture --download`
* Verify the official competition closing deadline, active-submission and final-eligibility rules, package requirements, and runtime constraints on the Kaggle competition page.

### Action 2: Freeze Baseline & Select a Single Challenger Focus
* Identify and freeze the primary active fallback agent (e.g., current Prvsiyan or Shepherd baseline).
* Select **one** single challenger hypothesis to investigate to completion. Do not split engineering cycles across multiple divergent candidate branches.

### Action 3: Empirical Evaluation of P2 V2 (If Pursuing Market Slot Ordering)
* **Dedicated Monotonic Profile:** Execute a sequential, monotonic profile of V2 using `time.perf_counter()` to verify callback latency distribution against internal workspace guidelines.
* **Predeclared Fresh-Seed Confirmation:** Run a dedicated fixed-pair confirmation protocol across fresh, previously unused held-out seeds against the frozen benchmark panel (both seats). Do NOT attempt Phase 1 screening and do NOT touch the prohibited shard.
* **Audit & Bootstrap:** Fully audit every result shard. Compute the whole-seed cluster bootstrap 95% confidence interval on paired match points.
* **Candidate Decision Criteria:** If V2 exhibits latency regressions or edge-case failures, reject it. If the bootstrap confidence interval is inconclusive (crosses zero), do not promote; preserve as experiment-only or gather more evidence if time allows, rather than automatically discarding. Under no circumstances should unit test success be treated as a proxy for competitive playing strength or grounds for promotion.

### Action 4: Single-Factor Alternative — P3 Herd-Value Selector (Only if Time Permits)
* Note that P3 is an unimplemented and unevaluated research hypothesis from the backlog, not an existing candidate.
* If P2 V2 is concluded or not promoted, evaluate the remaining-season herd-value selector hypothesis from the research backlog as an isolated single-factor ablation.
* Compare conservative remaining-season cow/sheep purchasing against the baseline across paired seeds and seats.
* Reject immediately if solo cash increases while match-points evidence or feed security degrade.

### Action 5: Comprehensive Operational & Compliance Packaging
* Compile standalone submission artifact using the existing compiler (`submission/compile_submission.py`).
* Verify cold-start execution, package import latency, and 720-turn completion with zero errors or invalid actions.
* Verify applicable license/NOTICE obligations for incorporated components without asserting a specific license unless sourced from its exact artifact manifest.
* Record the immutable SHA256 digest of the compiled artifact.

### Action 6: Explicit User Approval & Live Deployment Protocol
* Present a concise, candid submission briefing to the user containing:
  * Compiled candidate path and SHA256 digest.
  * Measured win-point delta, 95% bootstrap confidence interval, and sample size.
  * Monotonic callback profile statistics (p95, max, over-threshold frequency).
  * Target active slot and the specific existing submission being replaced, qualified by verified official rules.
  * Explicit risk statement and rollback strategy.
* **Await explicit user command before uploading.** Emphasize that there is no guaranteed win.
* Once authorized, execute upload via Kaggle CLI, read back the stable submission reference/status and available validation result with the Kaggle CLI, and verify the latest-two state against current official rules. (Do not rely on hard-coded enum assumptions such as `SubmissionStatus.COMPLETE` or assume a validation episode ID is always available.)

---

## 6. Copyable Continuation Prompt

To resume work immediately in a new session or subagent, copy and paste the prompt below:

```markdown
Resume the Kaggriculture engineering initiative according to `docs/plans/kaggriculture-win-path-handoff-2026-09-27.md`.

Our primary goal is to maximize our final competition rank and medal standing before the deadline (recorded as 2026-09-30 23:59 UTC; confirm first against official rules).

Strict Operating Mandates:
1. Candid, evidence-driven evaluation: Offline unit tests and local cash metrics do not equal live match performance. Note candidly that no new Kaggle submission was made and no submission-attributable live score/rank improvement came from recent work; live standings have not been refreshed. Distinguish offline evidence from live competition outcomes; do not claim or imply recent work won or is likely to win.
2. Adhere to all safety gates: Absolute no-inspection and no-retry gate on the unaudited shard `screening_seed_924705151.json`; zero unprompted Kaggle uploads without explicit user authorization; check existing project-research claims regarding active-submission and two-agent tracking rules against current official Kaggle rules before any upload.
3. Current workspace state: Branch `research/kaggriculture-experiment-archive-20260926` with base commit `9093a52` pushed and tracking origin. Tracked README and backlog files have uncommitted modifications, this handoff doc is a new untracked file, and the pre-existing prohibited shard `screening_seed_924705151.json` is a separate untracked and untouched file. 105/105 tests pass, V2 code review passed (12/12 focused tests pass), but V2 has zero tournament or runtime profile evidence.

Immediate First Actions:
1. Mandatory first action: Query the Kaggle CLI to refresh live submissions, episode counts, standings, team rank, total teams, confirmed competition deadline, and current official active-submission/final-eligibility rules.
2. Formulate a single, focused execution plan for Step 2 and Step 3 (either profiling and testing P2 V2 on fresh held-out seeds, or advancing the P3 herd-value hypothesis).
3. Do not upload or modify active submissions until full empirical confirmation, packaging verification (checking applicable license/NOTICE obligations), and explicit user consent are secured. After authorized upload, read back stable submission reference/status and available validation result via CLI, then verify latest-two state against official rules.
```
