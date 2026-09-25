# Local Agent Selection Experiment Report: Screening & Confirmation Tournament

## Executive Summary

This report documents the local, offline evaluation of ten competitive agent architectures for the Kaggle Kaggriculture environment. The evaluation was structured in two rigorous phases:

1. **Phase 1 (Screening):** A full round-robin tournament across all ten candidate agents using four fixed seeds (360 matches total; 72 matches per candidate; both seat orientations per pair).
2. **Phase 2 (Confirmation):** An independent holdout benchmarking tournament between the top two finalists—**Shepherd Sovereign** (`shepherd_sovereign`) and **Prvsiyan Moon Counts Melons** (`prvsiyan_moon_counts_melons`)—competing directly against each other and across the eight remaining roster candidates across eight fresh held-out seeds (272 matches total; 144 matches per finalist).

### Key Findings
* **Phase Distinction & Confirmation Leader:** In Phase 1's 10-agent round-robin screening, **Shepherd Sovereign** ranked #1 with a match-points rate of **.8333 (60-12-0)** and **Prvsiyan Moon Counts Melons** ranked #2 with **.8056 (58-14-0)**. In Phase 2's finalist-vs-roster confirmation panel, Prvsiyan emerged as the provisional confirmation-panel leader, leading the pooled match-points rate at **.8750 (126-18-0)** across 144 games against identical opponent panels and winning **16-0-0** in direct head-to-head play against Shepherd (+1,723.5 mean margin).
* **The Jaxa 2802 Matchup Contrast:** Prvsiyan is **not** an unconditional global winner across opponents. Against **Jaxa 2802 Variant B**, Prvsiyan won 2/16 sampled games (**2-14-0**, -9,998.2 mean margin). In contrast, **Shepherd Sovereign** won 16/16 sampled games vs Jaxa 2802 (**16-0-0**, +6,088.8 mean margin) and achieved a higher overall mean margin across the confirmation roster (+1,456.3 vs +955.6). This is an observed matchup outcome on this panel, not a proven causal mechanism.
* **Cluster Uncertainty Across Opponents:** In an independent paired cluster analysis across the eight confirmation seed clusters, the mean paired match-points difference ($\Delta = \text{Prvsiyan} - \text{Shepherd}$) was **+9.03 percentage points** (+.09028), but the 95% whole-seed cluster bootstrap interval is **`[-.02778, +.27083]`**. Because this interval crosses zero, broad all-opponent superiority is not statistically decisive at an 8-seed sample size.
* **Latency Telemetry Warning:** Neither candidate strictly satisfies the workspace `<100 ms` per-call latency guideline across all turns. In 103,536 callbacks per candidate, Shepherd recorded 2 calls exceeding 100 ms (max 107.20 ms), and Prvsiyan recorded 11 calls exceeding 100 ms (max 132.78 ms).
* **Operational Decision:** Treat **Prvsiyan Moon Counts Melons** as the provisional confirmation-panel leader for counter-strategy research; **retain Shepherd Sovereign as the user's local baseline**; investigate Prvsiyan's observed Jaxa matchup deficit and latency tail before any consideration of deployment. No submission occurred during the local tournament itself; a separate live follow-up package was subsequently submitted at the user's explicit request and has completed evaluation (latest snapshot: 110 public episodes, score 2071.7; see Section 9).

---

## 1. Experimental Design & Provenance

### 1.1 Simulation Engine & Rules
* **Engine:** `kaggle-environments` version `1.32.7` (verified via `importlib.metadata`).
* **Game Horizon:** 720 discrete simulation turns per episode.
* **Primary Evaluation Metric:** Match points rate, where a win = 1.0, a tie = 0.5, and a loss = 0.0 (reflecting competitive match outcomes rather than raw coin margin).
* **Tiebreak & Secondary Metrics:** Mean terminal coin margin ($\text{Coins}_{\text{candidate}} - \text{Coins}_{\text{opponent}}$) and mean own terminal coin balance.
* **Submission Policy:** Offline local benchmark only. **No Kaggle submissions were executed during the local tournament itself**. (Subsequent to this offline experiment, a separate live follow-up package was submitted at the user's explicit direction; see Section 9 for early live follow-up status. That upload contributes no evidence to the offline results.)
* **Public Page Scores:** Kaggle notebook page scores (e.g., historical best scores) are recorded in discovery manifests strictly as provenance metadata. They are **never** treated as empirical evidence or used for local tournament ranking.

### 1.2 Candidate Roster & Provenance
The ten evaluated candidates represent three distinct provenance groups:
1. **User Snapshot Submissions:** Shepherd Sovereign and Jaxa 2802 Variant B (recorded from local submission snapshot metadata; not queried as currently active live submissions during this offline test).
2. **Repository Local Prior Benchmarks:** High-performing internal models (The 2950 Peak Farm, Herd-Safe Race, V57 Invariant, Thomas 2945 Farm).
3. **Public Kaggle Community Candidates:** Clean single-file extractions of prominent public competitors (Ahmed V39, Ahmed V55, Cha22 Multi-Route, Prvsiyan Moon Counts Melons). Note: Cha22 Multi-Route was deduplicated against Guruprasaathas Master Engine V3 as both output identical SHA256 bytes.

All candidate code paths and SHA256 hashes are recorded in the manifest artifacts. Only the canonical RACE aggregate and four batches had path values normalized; `candidates.frozen_original.json` remains byte-preserved with historical machine paths (hash `dfa516424369d4fa30e35cd06da95bff1ffe09a73919a549dc1ca78c6b078a46`, used by historical tournament result files), while `candidates.json` is the portable rerun manifest; hashes of candidate source bytes did not change:

| Candidate ID | Name | Group / Lineage | Source File | SHA256 Digest |
| :--- | :--- | :--- | :--- | :--- |
| `shepherd_sovereign` | Shepherd Sovereign | User Baseline (Snapshot Ref 56490949) | `competitors/notebooks/shepherd_sovereign_main.py` | `5f2b51a2beaf5e08cb73e82f0e03e02e56de601563b28344e49b7058e371b247` |
| `prvsiyan_moon_counts_melons` | Prvsiyan Moon Counts Melons | Public Agent (`prvsiyan`) | `sources/prvsiyan_moon_counts_melons/main.py` | `178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a` |
| `herd_safe_race` | Herd-Safe Race | Local SOTA Benchmark | `competitors/notebooks/herd_safe_main.py` | `29454a13477f827c34615300f90a7bdb074ea3c9bcb948f3372bf95fa1fb207d` |
| `v57_invariant` | V57 Invariant | Local SOTA Benchmark | `competitors/notebooks/v57_main.py` | `2ee689fdc58f38b7bf6b80b8d3f48129d19b47201dbee51fdcbd977498a5106f` |
| `jaxa_2802_variant_b` | Jaxa 2802 Variant B | User Baseline (Snapshot Ref 56467787) | `competitors/notebooks/jaxa_2802_router/main_variant_b_h24.py` | `944aa64c5ae1296a9a17eb7961ed8d5a96d0b80183d41e954389983d73420a56` |
| `cha22_multi_route` | Cha22 Multi-Route | Public Agent (`flexonafft`) | `sources/cha22_multi_route/main.py` | `127ed3e62988c0474d386db6527ae8ca9de9bb1fe7004128557ddef67126c652` |
| `ahmed_v55` | Ahmed V55 | Public Agent (`ahmedberatozer`) | `sources/ahmed_v55/main.py` | `f09034624844da494669c4ab0e0d9a797da1a19db95eb138b875d309bd1aa01b` |
| `peak_2950` | The 2950 Peak Farm | Local SOTA Benchmark | `competitors/notebooks/peak_2950_main.py` | `613245d98c5066f9c393de866b0e19998c0f7ba636be08b2990a3e5e79d18ca7` |
| `thomas_2945_farm` | Thomas 2945 Farm | Local SOTA Benchmark | `competitors/notebooks/thomas_2945_main.py` | `4f3ca95dd12d9a94b03339999d8803c155f450a8d3956636f050643301fcc5dd` |
| `ahmed_v39` | Ahmed V39 | Public Agent (`ahmedberatozer`) | `sources/ahmed_v39/main.py` | `708c7485fa964853b193f175dcd83020602c005e159ce82e38dc350b22e970c8` |

### 1.3 Execution Integrity & Verification
* **Screening Phase Execution:**
  * 4 fixed seeds (`353711617`, `139535007`, `824705151`, `547805795`).
  * 45 unique unordered pairs $\times$ 2 seat orientations (Seat 0 and Seat 1) $\times$ 4 seeds = **360 games**.
  * **Integrity Audit:** 360/360 games completed; 720/720 player terminal statuses were `DONE`; 0 invalid matches; 0 callback errors; 0 technical errors; 100% manifest SHA256 match.
* **Confirmation Phase Execution:**
  * 8 fresh held-out seeds (`78284910`, `49798149`, `16980293`, `629521872`, `245925070`, `913117904`, `542891421`, `905658093`).
  * Schedule per seed: 2 direct H2H (both seats) + 16 Shepherd games (vs 8 opponents in both seats) + 16 Prvsiyan games (vs 8 opponents in both seats) = 34 games/seed $\times$ 8 seeds = **272 games**.
  * **Integrity Audit:** 272/272 games completed; 544/544 player terminal statuses were `DONE`; 0 invalid matches; 0 callback errors; 0 technical errors; 100% manifest SHA256 match.

---

## 2. Phase 1: Screening Tournament Results

In Phase 1, all ten candidates competed in a complete round robin across four seeds. Each candidate completed exactly 72 matches (8 matches against each of the 9 other candidates: 4 seeds $\times$ 2 seat positions).

Candidates are ranked by **match-points rate** ($\text{Points} / 72$), with **mean terminal margin** serving as the secondary tiebreaker.

### 2.1 Screening Leaderboard (72 Matches / Candidate)

| Rank | Candidate | Record (W-L-T) | Match-Points Rate | Mean Terminal Margin | Mean Own Cash | Invalid / Errors | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **Shepherd Sovereign** | **60-12-0** | **.8333** | **+1695.8** | $80,858.8 | 0 / 0 | **Advanced to Finals** |
| **2** | **Prvsiyan Moon Counts Melons** | **58-14-0** | **.8056** | **-55.0** | $82,955.0* | 0 / 0 | **Advanced to Finals** |
| 3 | Herd-Safe Race | 46-26-0 | .6389 | +1428.7 | $80,672.1 | 0 / 0 | Eliminated |
| 4 | V57 Invariant | 44-28-0 | .6111 | -476.3 | $82,935.8 | 0 / 0 | Eliminated |
| 5 | Jaxa 2802 Variant B | 38-34-0 | .5278 | +2341.3 | $90,808.0 | 0 / 0 | Eliminated |
| 6 | Cha22 Multi-Route | 32-40-0 | .4444 | +689.4 | $80,397.1 | 0 / 0 | Eliminated (Tiebreak 1) |
| 7 | Ahmed V55 | 32-40-0 | .4444 | -44.1 | $82,066.7 | 0 / 0 | Eliminated (Tiebreak 2) |
| 8 | The 2950 Peak Farm | 28-44-0 | .3889 | -183.5 | $80,848.3 | 0 / 0 | Eliminated |
| 9 | Thomas 2945 Farm | 20-52-0 | .2778 | +39.7 | $79,895.2 | 0 / 0 | Eliminated |
| 10 | Ahmed V39 | 2-70-0 | .0278 | -5436.1 | $77,546.4 | 0 / 0 | Eliminated |

*\*Exact raw summary mean own cash for Prvsiyan: 82,954.9583.*

### 2.2 Phase 1 Analysis
* **Clear Tier Separation:** Shepherd Sovereign ranked #1 (.8333, 60-12-0) and Prvsiyan ranked #2 (.8056, 58-14-0), clearly separating themselves from the rest of the field and finishing at least 12 wins ahead of third-place Herd-Safe Race (.6389, 46-26-0).
* **Cash Ceiling vs Match-Points Rate:** Jaxa 2802 Variant B recorded the highest individual screening mean cash ($90,808.0) and highest positive margin (+2341.3), but recorded a lower match-points rate of .5278 (38-34-0).
* **Observed Screening Dispersion:** Ahmed V39 recorded a .0278 match-points rate (2 wins in 72 games) on this frozen roster and engine version. Ahmed V55 and Cha22 Multi-Route each achieved .4444 (32-40-0), while Prvsiyan (.8056) advanced to the confirmation phase alongside Shepherd Sovereign (.8333).

---

## 3. Phase 2: Confirmation Tournament & Finalist Benchmarking

Phase 2 evaluated finalists **Shepherd Sovereign** and **Prvsiyan Moon Counts Melons** across eight newly generated fixed seeds. Both finalists faced the exact same schedule:
- 16 head-to-head matches against each other (8 seeds $\times$ 2 seat orientations).
- 128 matches against the eight non-finalist roster agents (8 seeds $\times$ 2 seat orientations $\times$ 8 opponents).
- Total: 144 matches per finalist (272 games in the tournament).

### 3.1 Pooled Confirmation Performance (144 Matches / Finalist)

| Finalist | Record (W-L-T) | Match-Points Rate | Mean Margin | Mean Own Cash | Mean Opponent Cash |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Prvsiyan Moon Counts Melons** | **126-18-0** | **.8750** | **+955.6** | **$99,568.0** | $98,612.3 |
| **Shepherd Sovereign** | 113-31-0 | .7847 | +1456.3 | $98,741.8 | $97,285.5 |

### 3.2 Direct Head-to-Head Benchmark
In direct competition across the 8 confirmation seeds in both seat positions:
* **Prvsiyan Moon Counts Melons vs Shepherd Sovereign:** **16-0-0**
* **Prvsiyan Mean Margin:** **+1,723.5** coins ($99,342.9 vs $97,619.4)
* **Cluster Dependence Note:** These 16 matches represent 8 seed clusters tested in both seat orientations (`Seat 0` and `Seat 1`). **They must not be treated as 16 independent worlds.** Because market fluctuations and map layouts are identical within each seed cluster, seat swaps are correlated pairs rather than independent samples.

### 3.3 Independent Paired Cluster Analysis Across Seeds
To determine whether Prvsiyan's broad superiority across the full opponent schedule is statistically decisive, we conduct an independent paired cluster analysis using the **seed** as the sampling unit ($N = 8$ clusters).

For each seed $s \in \{1, \dots, 8\}$, each finalist plays 18 matches (2 direct H2H + 16 against the 8 opponents). We compute the match-points rate for each finalist on that seed, and calculate the paired difference:
$$\Delta_s = \text{Rate}_{\text{Prvsiyan}, s} - \text{Rate}_{\text{Shepherd}, s}$$

| Seed Cluster ID | Prvsiyan Points Rate (18 g) | Shepherd Points Rate (18 g) | Paired Difference ($\Delta_s$) |
| :--- | :---: | :---: | :---: |
| `78284910` | 0.8889 (16/18) | 0.7222 (13/18) | **+.1667** |
| `49798149` | 0.8889 (16/18) | 0.8889 (16/18) | **0.0000** |
| `16980293` | 0.8889 (16/18) | 0.2222 (4/18) | **+.6667** |
| `629521872` | 0.8889 (16/18) | 0.8889 (16/18) | **0.0000** |
| `245925070` | 0.8889 (16/18) | 0.8889 (16/18) | **0.0000** |
| `913117904` | 0.8889 (16/18) | 0.8889 (16/18) | **0.0000** |
| `542891421` | 0.8889 (16/18) | 0.8889 (16/18) | **0.0000** |
| `905658093` | 0.7778 (14/18) | 0.8889 (16/18) | **-.1111** |
| **Mean Paired Difference** | — | — | **+.09028 (+9.03 pp)** |

#### Cluster Bootstrap Analysis
* **Method:** 100,000 resamples of whole seed clusters with replacement, evaluated with random seed `207`. Per-match i.i.d. intervals are strictly avoided due to strong intra-cluster correlation.
* **95% Percentile Confidence Interval:** **`[-.02778, +.27083]`**
* **Statistical Interpretation:** **The 95% confidence interval clearly includes zero.** While Prvsiyan holds a +9.03 percentage point mean advantage across seeds, the advantage is heavily influenced by a single seed cluster (`16980293`, where Shepherd dropped matches to multiple opponents). Across the eight seed clusters, five are equal (0.0000 difference), two are positive for Prvsiyan (+.1667 and +.6667), and one is negative for Prvsiyan (-.1111, where Shepherd outperformed Prvsiyan). Therefore, **broad all-opponent superiority is not statistically decisive at this sample size.**

---

## 4. Head-to-Head Matchup Breakdown & The Jaxa Anomaly

Examining the confirmation results broken down by individual opponent (16 matches per opponent: 8 seeds $\times$ 2 seats) reveals critical structural differences between the two finalists.

### 4.1 Shepherd Sovereign Matchup Matrix (16 Matches / Opponent)
*Note: The W-L-T column indicates Shepherd Sovereign's record against that specific opponent.*

| Opponent Candidate | Shepherd Record (W-L-T) | Shepherd Mean Cash | Opponent Mean Cash | Shepherd Mean Margin |
| :--- | :---: | :---: | :---: | :---: |
| vs Prvsiyan Moon Counts Melons | 0-16-0 | $97,619.4 | $99,342.9 | -1723.5 |
| vs Ahmed V39 | 16-0-0 | $98,859.4 | $92,063.1 | +6796.3 |
| vs Ahmed V55 | 14-2-0 | $98,862.0 | $98,880.9 | -18.9 |
| vs Cha22 Multi-Route | 12-4-0 | $99,067.6 | $98,389.9 | +677.6 |
| vs Herd-Safe Race | 14-2-0 | $99,307.3 | $99,009.5 | +297.8 |
| vs **Jaxa 2802 Variant B** | **16-0-0** | **$98,211.0** | **$92,122.2** | **+6088.8** |
| vs The 2950 Peak Farm | 14-2-0 | $98,905.8 | $98,886.1 | +19.6 |
| vs Thomas 2945 Farm | 14-2-0 | $99,132.9 | $97,753.4 | +1379.4 |
| vs V57 Invariant | 13-3-0 | $98,710.6 | $99,121.2 | -410.6 |

### 4.2 Prvsiyan Moon Counts Melons Matchup Matrix (16 Matches / Opponent)
*Note: The W-L-T column indicates Prvsiyan's record against that specific opponent.*

| Opponent Candidate | Prvsiyan Record (W-L-T) | Prvsiyan Mean Cash | Opponent Mean Cash | Prvsiyan Mean Margin |
| :--- | :---: | :---: | :---: | :---: |
| vs Shepherd Sovereign | 16-0-0 | $99,342.9 | $97,619.4 | +1723.5 |
| vs Ahmed V39 | 16-0-0 | $99,008.7 | $91,666.4 | +7342.3 |
| vs Ahmed V55 | 16-0-0 | $99,500.7 | $98,194.1 | +1306.6 |
| vs Cha22 Multi-Route | 16-0-0 | $99,924.2 | $97,633.2 | +2291.0 |
| vs Herd-Safe Race | 16-0-0 | $99,963.3 | $98,057.5 | +1905.8 |
| vs **Jaxa 2802 Variant B** | **2-14-0** | **$101,433.7** | **$111,431.9** | **-9998.2** |
| vs The 2950 Peak Farm | 16-0-0 | $99,004.7 | $97,663.6 | +1341.1 |
| vs Thomas 2945 Farm | 12-4-0 | $99,021.8 | $97,355.0 | +1666.8 |
| vs V57 Invariant | 16-0-0 | $98,911.8 | $97,889.9 | +1021.9 |

### 4.3 Detailed Matchup Dynamics: Intransitive Matchup Relationships
The confirmation matchup data displays an intransitive relationship among these three candidates:

```
          ┌────────────────────────────────────────┐
          │  Prvsiyan Moon Counts Melons           │
          │  (.8750 pooled rate; +1723.5 vs Shep)  │
          └──────────────────┬─────────────────────┘
                             │
                  Sweeps 16-0│Deficit 2-14
                  (-1723.5)  │(-9998.2)
                             ▼
 ┌──────────────────────┐         ┌────────────────────────┐
 │ Shepherd Sovereign   │◄────────┤  Jaxa 2802 Variant B   │
 │ (.7847 pooled rate)  │ 16-0-0  │  (.5278 screening rate)│
 └──────────────────────┘ (+6088.8)└────────────────────────┘
```

1. **Prvsiyan Confirmation Sweeps:** On this confirmation panel, Prvsiyan swept six opponents 16-0-0: Shepherd Sovereign, Ahmed V55, Cha22 Multi-Route, Herd-Safe Race, The 2950 Peak Farm, and V57 Invariant, posting positive mean margins against each.
2. **Prvsiyan vs Jaxa 2802 Matchup Deficit:** In the 16 sampled confirmation matches against Jaxa 2802 Variant B, Prvsiyan won 2 and lost 14, with Jaxa Variant B outscoring Prvsiyan by a mean margin of 9,998.2 coins per game ($111,431.9 vs $101,433.7).
3. **Shepherd vs Jaxa 2802 Matchup Result:** In contrast, Shepherd won 16/16 sampled games vs Jaxa 2802 Variant B on this confirmation panel (with a +6,088.8 mean coin margin), while Prvsiyan won 2/16. This is an observed matchup result on this panel, not a proven causal mechanism.
4. **Opponent Mix Implication:** If likely opponents include Jaxa-like routing agents, this observed weakness matters; this fixed panel does not estimate their live prevalence. The optimal choice between Shepherd and Prvsiyan depends heavily on the actual distribution of opponent architectures encountered in competitive play.

---

## 5. Execution Health & Latency Analysis

Under the rules established in `GEMINI.md`, every call to `agent.act()` must return in **under 100 ms** to prevent timeouts on Kaggle matchmaking servers. Telemetry was tracked across all 144 confirmation matches per finalist (719 turns/match $\times$ 144 matches = **103,536 callbacks** per agent).

### 5.1 Runtime & Latency Benchmark Table

| Metric | Shepherd Sovereign | Prvsiyan Moon Counts Melons | Guideline Threshold |
| :--- | :---: | :---: | :---: |
| **Total Callbacks Evaluated** | 103,536 | 103,536 | — |
| **Callback Exceptions / Errors** | **0** | **0** | 0 |
| **Invalid Matches / Forfeits** | **0** | **0** | 0 |
| **Mean Cumulative Time / Match** | 798.15 ms | 856.73 ms | — |
| **Mean Time / Callback** | ~1.11 ms | ~1.19 ms | < 100.0 ms |
| **Maximum Individual Callback** | **107.20 ms** | **132.78 ms** | < 100.0 ms |
| **Callbacks Exceeding 100 ms** | **2** | **11** | **0** |

### 5.2 Latency Assessment
* **Zero Systemic Failures:** All matches completed `DONE` with no recorded callback exceptions or technical errors across 144 consecutive games per finalist. Average callback latency for both is negligible (~1.1–1.2 ms).
* **Deployment Concern:** **Neither candidate strictly satisfies the `< 100 ms` latency gate across all calls.**
  * Shepherd Sovereign recorded two callbacks above 100 ms, reaching a maximum of 107.20 ms.
  * Prvsiyan recorded eleven callbacks above 100 ms, reaching a maximum of 132.78 ms.
* **Recommendation:** These tail latency spikes represent a deployment risk on shared, virtualized Kaggle execution workers. Profiling and micro-optimizing pathfinding / tree-search loops is required prior to considering either agent for live matchmaking.

---

## 6. Strategic Decision & Operational Synthesis

### 6.1 Synthesis
1. **Phase Distinctions & Rankings:** **Shepherd Sovereign** won Phase 1 screening, ranking #1 in the 10-agent round robin (.8333 match-points rate, 60-12-0), while **Prvsiyan Moon Counts Melons** ranked #2 (.8056, 58-14-0). In Phase 2's confirmation panel, Prvsiyan emerged as the provisional confirmation-panel leader by virtue of leading the pooled match-points rate (.8750, 126-18-0) and sweeping Shepherd 16-0 in direct head-to-head play (+1,723.5 mean margin).
2. **Conditional Superiority:** Prvsiyan is **not an unconditional global winner**. Its paired all-opponent bootstrap confidence interval crosses zero (`[-.02778, +.27083]`), indicating that its edge over Shepherd across independent seed environments is sensitive to sample variation.
3. **Observed Matchup Contrast:** Prvsiyan's 2-14 record against Jaxa 2802 Variant B (-9,998.2 mean margin) represents an observed matchup deficit on this panel. Shepherd Sovereign performed better against Jaxa in this sample (16-0 vs 2-14) and maintained a higher average margin across the confirmation roster (+1,456.3 vs +955.6).

### 6.2 Recommended Next Actions
1. **Designate Provisional Confirmation Leader:** Officially record Prvsiyan Moon Counts Melons as the provisional confirmation-panel leader for internal research, while noting Shepherd Sovereign's #1 rank in Phase 1 screening.
2. **Retain Shepherd Baseline:** Retain Shepherd Sovereign as the user's local baseline. Make no live replacement or submission to Kaggle based solely on this experiment without understanding the observed Jaxa matchup deficit.
3. **Investigate the Jaxa Matchup:** Analyze match replays from Prvsiyan vs Jaxa 2802 to inspect why Jaxa generated a +10k coin margin surplus against Prvsiyan on this panel, and compare against Shepherd's play in that matchup.
4. **Profile Latency:** Profile both agents' worst-case step execution to eliminate callback spikes over 100 ms.
5. **No Automatic Live Replacement:** Strictly enforce the rule that no automatic live replacement or ladder conclusions are authorized based solely on these offline results. (A separate live-test package for Prvsiyan was subsequently submitted at the user's explicit request as a live follow-up—now COMPLETE with score 2071.7 across 110 public episodes; no matched Shepherd-vs-Prvsiyan A/B result established—while Shepherd was not re-uploaded; see Section 9.)

---

## 7. Threats to Validity & Limitations

To ensure sound scientific interpretation, the following experimental boundaries must be recognized:
1. **Fixed Roster Scope ($N=10$):** Results reflect relative performance within this specific 10-candidate panel. They do not generalize automatically to unseen architectures or private competitors.
2. **Finite Seed Panels:** Phase 1 utilized 4 seeds (360 games); Phase 2 utilized 8 seeds (272 games). While seed-paired seat balancing eliminates seat advantage, environmental variance across maps remains a factor.
3. **Cluster Dependence (Seed as Cluster Unit):** Paired seat swaps on the same seed share environmental conditions (crop weather, starting layout). Treating seat-swapped matches as independent i.i.d. observations artificially inflates statistical confidence; whole-cluster analysis must always be used.
4. **Equal Opponent Weighting:** The confirmation tournament weighs each opponent equally (1/9 of matches each). In live competition, the actual opponent distribution may be non-uniform; this offline panel does not estimate live opponent prevalence.
5. **Static Code Snapshots:** All candidates were tested from frozen byte manifests (`candidates.json`) under engine version `1.32.7`. Any upstream changes to public notebooks or engine physics will alter relative rankings.

---

## 8. Artifact Traceability Matrix

Every figure, table, and claim in this report can be verified against the following versioned JSON artifacts in `docs/experiments/agent_selection/`:

| Report Section / Metric | Primary Source Artifact | Key JSON Paths |
| :--- | :--- | :--- |
| Candidate Roster & Hashes | `candidates.frozen_original.json` / portable `candidates.json` | `manifest.candidates[*]`, `source_sha256` |
| Screening Matches (360) | `screening_seed_*.json` (4 files) | `screening_seed_*.json:results` (90 matches/seed) |
| Screening Summary Leaderboard | `screening_summary.json` | `screening_summary.json:agent_summaries[*]` |
| Confirmation Matches (272) | `confirmation_seed_*.json` (8 files)| `confirmation_seed_*.json:results` (34 matches/seed) |
| Confirmation Pooled Totals | `confirmation_summary.json` | `confirmation_summary.json:agent_summaries.shepherd_sovereign`, `...prvsiyan_moon_counts_melons` |
| Direct H2H (16 matches) | `confirmation_summary.json` | `confirmation_summary.json:confirmation_stats` |
| Seed Cluster Differences | `confirmation_seed_*.json` (8 files)| Match points aggregated per seed file for finalists |
| Pairwise Matchup Breakdown | `confirmation_summary.json` | `agent_summaries[*].pairwise[*]` |
| Callback Latency & Spikes | `confirmation_seed_*.json` (8 files)| `results[*].agent_*.stats.max_ms`, `over_100ms`, `total_ms` |

### 8.1 Reproducibility & Portable Source Bundle
The historical selection experiment is now portable. Only the canonical RACE aggregate and four batches had path values normalized; `candidates.frozen_original.json` remains byte-preserved with historical machine paths (SHA256 `dfa516424369d4fa30e35cd06da95bff1ffe09a73919a549dc1ca78c6b078a46`), matching the hash retained by historical tournament JSONs, while `candidates.json` is the portable rerun manifest (SHA256 `65262dc81cc801106dce848d88c720c3531f59db409421f56bd42cf710829624`) with paths relative to the manifest; candidate source hashes are unchanged. The tested public code and license artifacts for candidates (`ahmed_v39`, `ahmed_v55`, `cha22_multi_route`, and `prvsiyan_moon_counts_melons`) are included byte-for-byte under `sources/`. The path-resolution unit test passed, and local smoke schedules exercised Shepherd-vs-Prvsiyan (2 games) and all four bundled public candidates against one another (12 games); every game completed `DONE` with zero errors or invalid matches. This verifies portable loading, not a rerun of the historical 632-game selection tournament. Historical outcomes and raw JSONs were not modified.

---

## 9. Live Follow-Up & Ladder Telemetry

*Note: This section records an operational follow-up performed after the completion of the offline tournament. It contributes no evidence to the offline tournament findings or rankings above.*

* **Event Date:** 2026-09-24 (initial upload)
* **Context & Timing:**
  * During the offline screening and confirmation tournament itself, **no Kaggle upload was executed**.
  * After the offline experiment concluded, at the user's explicit request, a live confirmation candidate package for Prvsiyan Moon Counts Melons was submitted to the Kaggle competition platform to initiate live ladder benchmarking.
  * **Shepherd Sovereign was already submitted and was NOT re-uploaded.**
  * No submission was made during this documentation refresh.
* **Submission Details & Source Verification:**
  * **Submission Ref:** `56531885`
  * **Archive Filename:** `prvsiyan_kaggriculture_submission.tar.gz`
  * **Submission Description:** `Prvsiyan Moon Counts Melons: local confirmation candidate; Apache-2.0 license and NOTICE included`
  * **API Submission Timestamp:** `2026-09-24T21:25:39.747000`
  * **Uploaded Archive SHA256:** `81fb5c1b14b63ffb795c8b10135cac93caab94b50c4f98b26c250af4155101bb`
  * The uploaded archive contains exactly three files: `main.py`, `LICENSE.txt`, and `NOTICE.txt` (including Apache-2.0 license and attribution).
  * Extracted `main.py` SHA256: `178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a`, matching the frozen candidate manifest (`candidates.json`) identically.

### 9.1 Authoritative CLI Snapshot (2026-09-25 12:08 CEST (+0200))
Command: `kaggle competitions submissions kaggriculture --format json --page-size 100`

* **Latest-Two Tracked Submissions (Active Evaluation Pool):**
  1. **Prvsiyan Moon Counts Melons** (Ref `56531885`): File `prvsiyan_kaggriculture_submission.tar.gz`. Status: `SubmissionStatus.COMPLETE`. Public Score: **2071.7** (Private: blank).
     * Latest episode query (`kaggle competitions episodes 56531885 --format json`): **110 completed public episodes** and **1 completed validation episode** (`113019966`). All completed.
  2. **Shepherd Sovereign** (Ref `56490949`): File `shepherd_sovereign_main.py`. Status: `SubmissionStatus.COMPLETE`. Public Score: **2021.4** (Private: blank).
     * Latest episode query (`kaggle competitions episodes 56490949 --format json`): **272 completed public episodes** and **1 completed validation episode**. All completed.
     * Note: Existing active baseline, submitted 2026-09-23T10:46:41.287000; not re-uploaded.

* **Third / Older (Outside Tracked Pair):**
  3. **Jaxa 2802 Variant B** (Ref `56467787`): Status: `SubmissionStatus.COMPLETE`. Public Score: **1680.8** (Private: blank). Retired to third/older; frozen rating outside the active evaluation pair.

### 9.2 Historical Early Snapshot (2026-09-25 00:13:22 CEST (+0200))
*(Retained for historical progression record)*
* **Prvsiyan Moon Counts Melons** (Ref `56531885`): Status `COMPLETE`, public score `1422.9`, private blank, 11 completed public episodes (`113021238` through `113031699`) and 1 validation episode (`113019966`).
* **Shepherd Sovereign** (Ref `56490949`): Status `COMPLETE`, public score `2117.5`, private blank.
* **Jaxa 2802 Variant B** (Ref `56467787`): Status `COMPLETE`, public score `1680.8`, private blank.

### 9.3 Crucial Matchup & Rating Caveats
* **Not a Matched Head-to-Head A/B Result:** Prvsiyan's displayed public score of `2071.7` is 50.3 points higher than Shepherd's `2021.4`. However, they are dynamic cumulative ratings across different public match histories (110 vs 272 episodes), not a matched head-to-head. They do not represent a head-to-head A/B comparison.
* **Opponent Identities and Outcomes Unknown:** Querying the Kaggle `episodes` endpoint lists episode IDs and completion statuses only. The endpoint does **not** disclose opponent identities, matchups, or individual match winners. No claim is made that any public episode was played between Prvsiyan and Shepherd.
* **Zero Offline Tournament Evidentiary Weight:** These live ladder ratings and episode tallies contribute zero empirical evidence to the offline tournament findings, cluster bootstrap intervals, or candidate rankings documented above.

## Sources

[1] https://www.kaggle.com/competitions/kaggriculture — Kaggriculture competition overview
