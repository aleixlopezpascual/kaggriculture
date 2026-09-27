# P2 V2 Market Slot Ordering Empirical Evaluation & Win-Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute empirical monotonic profiling, fresh-seed confirmation tournament, and whole-seed cluster bootstrap evaluation of the reviewed P2 V2 market slot ordering candidate against the frozen Prvsiyan baseline and benchmark panel, determining whether V2 qualifies for live submission packaging.

**Architecture:** Follow the predeclared two-stage evaluation protocol established in `docs/plans/kaggriculture-win-path-handoff-2026-09-27.md`. First, generate a fresh-seed manifest ensuring strict disjointness from all prior seeds. Next, profile callback latency sequentially with monotonic timing (`time.perf_counter()`) on 2 fresh seeds (60 matches) to test the workspace 100ms guideline. Then, complete the full 8-seed confirmation tournament (240 matches), calculate paired point deltas with whole-seed cluster bootstrap (10,000 resamples), and enforce the statistical decision gate.

**Tech Stack:** Python 3.10+, `kaggle-environments 1.32.7`, NumPy, Pytest, JSON.

**Spec:** `docs/plans/kaggriculture-win-path-handoff-2026-09-27.md`

## Global Constraints

- **Prohibited Shard Integrity Gate:** The file `docs/experiments/agent_selection/p2_market_slot_ordering/screening_seed_924705151.json` is strictly quarantined. No tool or script may read, inspect, hash, parse, retry, or aggregate this file.
- **Zero Unprompted Uploads Gate:** Absolutely no automated or unprompted Kaggle uploads. Any live submission requires explicit user authorization with candidate path, commit, SHA256 digest, target active slot, and rollback plan.
- **Engine Standard:** `kaggle-environments==1.32.7`, 720 discrete simulation turns per match.
- **Timing Standard:** Monotonic `time.perf_counter()` for interval timing; internal workspace engineering guideline `<100 ms` per callback.
- **Decision Standard:** Primary metric is match win points rate (win = 1.0, tie = 0.5, loss = 0.0) evaluated by whole-seed cluster bootstrap 95% confidence interval across 8 fresh seeds. Unit test passing alone provides zero claim of competitive playing strength.

## Review Focus

1. **Candidate Artifact & Digest Integrity:** Candidate V2 helper SHA256 must match `6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59` and baseline SHA256 must match `178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a`.
2. **Seed Disjointness:** Confirmation seeds must be fresh and have zero intersection with historical P1/P2 screening or confirmation seeds.
3. **Balanced Confirmation Schedule:** Exactly 30 matches per seed (2 head-to-head matches + 4 matches per benchmark opponent across 7 opponents = 28), ensuring equal seat-0 and seat-1 appearances for both finalists (16 appearances per seed, 128 total per finalist).
4. **Clean Match Termination:** All 240 matches must terminate with status `DONE`, 0 agent exceptions, and 0 invalid actions.
5. **Statistical Decision Boundary:** If the whole-seed cluster bootstrap 95% CI crosses zero, the candidate must NOT be promoted to live submission; it must be preserved as experiment-only.

---

### Task 1: Generate Fresh Seed Manifest & Manifest Integrity Test

**Files:**
- Create: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json`
- Test: `tests/test_p2_v2_manifest.py`

**Interfaces:**
- Consumes: `docs/experiments/agent_selection/sources/prvsiyan_moon_counts_melons/main.py`, `docs/experiments/agent_selection/p2_market_slot_ordering/sources/prvsiyan_global_sell_slot_challenger_reviewed/main.py`, `scripts/p2_market_slot_optimizer_reviewed.py`
- Produces: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json` containing 8 fresh confirmation seeds `[838084248, 690003990, 400914000, 839524396, 946313351, 911995953, 996328792, 134302223]` (RNG seed `20260928`).

- [ ] **Step 1: Write the failing test for P2 V2 manifest and seed disjointness**

```python
# tests/test_p2_v2_manifest.py
import json
import random
from pathlib import Path

def test_p2_v2_manifest_integrity():
    manifest_path = Path("docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json")
    assert manifest_path.is_file(), f"Manifest file missing: {manifest_path}"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    assert manifest["schema_version"] == 1
    assert manifest["engine"]["version"] == "1.32.7"
    
    # Check confirmation finalists
    finalists = manifest["design"]["confirmation_finalists"]
    assert finalists == [
        "prvsiyan_moon_counts_melons",
        "prvsiyan_global_sell_slot_challenger_reviewed"
    ]
    
    # Check seeds
    conf_seeds = manifest["design"]["confirmation_seeds"]
    assert len(conf_seeds) == 8
    assert len(set(conf_seeds)) == 8
    
    # Check disjointness against prior seeds
    p1_seeds = {256507559, 336278987, 522388730, 972925858, 300914001, 590003991, 738084249, 739524397, 811995954, 846313352, 896328793, 966857091}
    p2_seeds = {453711617, 239535007, 924705151, 647805795, 225915100, 563508405, 707885790, 895731764, 955397235, 812292840, 758639642, 352111692}
    prior_seeds = p1_seeds | p2_seeds
    assert not (set(conf_seeds) & prior_seeds), "Confirmation seeds must be disjoint from prior seeds!"
    
    # Check RNG reproducibility
    rng_seed = manifest["design"]["seed_generation_rng_seed"]
    assert rng_seed == 20260928
    rng = random.Random(rng_seed)
    expected_seeds = []
    while len(expected_seeds) < 8:
        s = rng.randrange(100_000_000, 1_000_000_000)
        if s not in prior_seeds and s not in expected_seeds:
            expected_seeds.append(s)
    assert conf_seeds == expected_seeds
    
    # Verify candidate files and SHA256 digests exist
    candidates = {c["id"]: c for c in manifest["candidates"]}
    assert "prvsiyan_moon_counts_melons" in candidates
    assert "prvsiyan_global_sell_slot_challenger_reviewed" in candidates
    
    import hashlib
    for cid, c in candidates.items():
        rel_path = manifest_path.parent / c["source_path"]
        assert rel_path.is_file(), f"Missing source for candidate {cid}: {rel_path}"
        actual_hash = hashlib.sha256(rel_path.read_bytes()).hexdigest()
        assert actual_hash == c["source_sha256"], f"Hash mismatch for candidate {cid}"
        if "helper_path" in c:
            h_path = manifest_path.parent / c["helper_path"]
            assert h_path.is_file(), f"Missing helper for {cid}: {h_path}"
            assert hashlib.sha256(h_path.read_bytes()).hexdigest() == c["helper_sha256"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_p2_v2_manifest.py -v`
Expected: FAIL with "Manifest file missing"

- [ ] **Step 3: Create the P2 V2 Manifest**

Write `docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json`:
Register 9 candidates (the 2 finalists + 7 benchmark opponents: `shepherd_sovereign`, `jaxa_2802_variant_b`, `peak_2950`, `v57_invariant`, `thomas_2945_farm`, `cha22_multi_route`, `arsgorynich_herd_safe_v3`), confirmation seeds `[838084248, 690003990, 400914000, 839524396, 946313351, 911995953, 996328792, 134302223]`, and design metadata.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_p2_v2_manifest.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit manifest and test**

```bash
git add docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json tests/test_p2_v2_manifest.py
git commit -m "feat(experiments): add P2 V2 market slot ordering manifest and seed integrity test"
```

---

### Task 2: Monotonic Latency Profile of P2 V2 Challenger (2 Fresh Seeds)

**Files:**
- Output: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/profile_monotonic_seed_838084248.json`
- Output: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/profile_monotonic_seed_690003990.json`
- Test / Script: `tests/test_p2_v2_latency_profile.py`

**Interfaces:**
- Consumes: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json`, `scripts/run_agent_selection_tournament.py`
- Produces: 2 raw shard profile JSON files (60 matches total, 23,008 callbacks per finalist) with monotonic timing metrics.

- [ ] **Step 1: Write verification test for monotonic latency profile outputs**

```python
# tests/test_p2_v2_latency_profile.py
import json
from pathlib import Path

def test_p2_v2_profile_shards_validity():
    profile_dir = Path("docs/experiments/agent_selection/p2_v2_market_slot_ordering")
    seeds = [838084248, 690003990]
    
    for s in seeds:
        shard_path = profile_dir / f"profile_monotonic_seed_{s}.json"
        assert shard_path.is_file(), f"Profile shard missing: {shard_path}"
        with open(shard_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["seed"] == s
        assert data["phase"] == "confirmation"
        assert len(data["matches"]) == 30
        
        for m in data["matches"]:
            assert m["status"] == "DONE"
            assert m["agent_0_error"] is None
            assert m["agent_1_error"] is None
            assert len(m["agent_0_callbacks"]) == 719
            assert len(m["agent_1_callbacks"]) == 719
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_p2_v2_latency_profile.py -v`
Expected: FAIL with "Profile shard missing"

- [ ] **Step 3: Execute sequential monotonic profile runs on seeds 838084248 and 690003990**

Run:
```bash
.venv/bin/python scripts/run_agent_selection_tournament.py \
  --manifest docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json \
  --phase confirmation \
  --seed 838084248 \
  --finalists prvsiyan_moon_counts_melons prvsiyan_global_sell_slot_challenger_reviewed \
  --output docs/experiments/agent_selection/p2_v2_market_slot_ordering/profile_monotonic_seed_838084248.json \
  --force

.venv/bin/python scripts/run_agent_selection_tournament.py \
  --manifest docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json \
  --phase confirmation \
  --seed 690003990 \
  --finalists prvsiyan_moon_counts_melons prvsiyan_global_sell_slot_challenger_reviewed \
  --output docs/experiments/agent_selection/p2_v2_market_slot_ordering/profile_monotonic_seed_690003990.json \
  --force
```

- [ ] **Step 4: Run test to verify outputs pass validity check & evaluate latency against 100ms guideline**

Run: `.venv/bin/pytest tests/test_p2_v2_latency_profile.py -v`
Expected: PASS (1 passed).
Compute latency summary:
- Baseline callback count, exceedances > 100ms, max callback latency, mean p95.
- V2 Challenger callback count, exceedances > 100ms, max callback latency, mean p95.
Confirm no severe latency regression or crash.

- [ ] **Step 5: Commit profile test and data**

```bash
git add tests/test_p2_v2_latency_profile.py
git commit -m "feat(experiments): record P2 V2 monotonic timing profile on initial fresh seeds"
```

---

### Task 3: Full 8-Seed Confirmation Tournament for P2 V2 vs Baseline Panel

**Files:**
- Output: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/confirmation_seed_<seed>.json` (seeds: 400914000, 839524396, 946313351, 911995953, 996328792, 134302223)
- Output: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/confirmation_summary.json`
- Test: `tests/test_p2_v2_confirmation_audit.py`

**Interfaces:**
- Consumes: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json`, `scripts/run_agent_selection_tournament.py`
- Produces: 8 raw confirmation shards (240 matches total, 128 appearances per finalist) and aggregated `confirmation_summary.json`.

- [ ] **Step 1: Write failing test to audit all 8 confirmation shards and summary**

```python
# tests/test_p2_v2_confirmation_audit.py
import json
from pathlib import Path

def test_p2_v2_confirmation_audit():
    manifest_path = Path("docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    seeds = manifest["design"]["confirmation_seeds"]
    assert len(seeds) == 8
    
    total_matches = 0
    shard_paths = []
    exp_dir = manifest_path.parent
    
    for s in seeds:
        p = exp_dir / f"confirmation_seed_{s}.json"
        assert p.is_file(), f"Confirmation shard missing: {p}"
        shard_paths.append(str(p))
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["seed"] == s
        assert len(data["matches"]) == 30
        for m in data["matches"]:
            assert m["status"] == "DONE"
            assert m["agent_0_error"] is None
            assert m["agent_1_error"] is None
        total_matches += len(data["matches"])
        
    assert total_matches == 240
    
    summary_path = exp_dir / "confirmation_summary.json"
    assert summary_path.is_file(), f"Summary missing: {summary_path}"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["phase"] == "confirmation"
    assert summary["total_matches"] == 240
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_p2_v2_confirmation_audit.py -v`
Expected: FAIL with "Confirmation shard missing"

- [ ] **Step 3: Run tournament for all 8 confirmation seeds and aggregate**

Copy seeds 1 and 2 from profile or rerun:
Run remaining seeds `400914000`, `839524396`, `946313351`, `911995953`, `996328792`, `134302223` (and link/copy seeds `838084248` and `690003990` to `confirmation_seed_<seed>.json`).
Run aggregation:
```bash
.venv/bin/python scripts/run_agent_selection_tournament.py \
  --aggregate \
  --inputs docs/experiments/agent_selection/p2_v2_market_slot_ordering/confirmation_seed_*.json \
  --phase confirmation \
  --output docs/experiments/agent_selection/p2_v2_market_slot_ordering/confirmation_summary.json \
  --force
```

- [ ] **Step 4: Run test to verify confirmation audit passes**

Run: `.venv/bin/pytest tests/test_p2_v2_confirmation_audit.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit confirmation audit test**

```bash
git add tests/test_p2_v2_confirmation_audit.py
git commit -m "feat(experiments): audit and verify full 8-seed P2 V2 confirmation tournament"
```

---

### Task 4: Whole-Seed Cluster Bootstrap Evaluation & Decision Gate

**Files:**
- Create: `scripts/analyze_p2_v2_confirmation.py`
- Create: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/report.md`
- Test: `tests/test_p2_v2_bootstrap_analysis.py`

**Interfaces:**
- Consumes: `docs/experiments/agent_selection/p2_v2_market_slot_ordering/confirmation_summary.json` and 8 raw shards
- Produces: Statistical decision: paired points rate difference, whole-seed cluster bootstrap 95% CI (10,000 resamples), head-to-head record, and decision verdict (Promote / Preserved Experiment-Only / Reject).

- [ ] **Step 1: Write test for whole-seed cluster bootstrap analysis script**

```python
# tests/test_p2_v2_bootstrap_analysis.py
import json
from pathlib import Path
from scripts.analyze_p2_v2_confirmation import compute_whole_seed_bootstrap

def test_bootstrap_reproducibility():
    summary_path = Path("docs/experiments/agent_selection/p2_v2_market_slot_ordering/confirmation_summary.json")
    assert summary_path.is_file()
    
    results = compute_whole_seed_bootstrap(summary_path, n_resamples=1000, rng_seed=42)
    assert "mean_delta" in results
    assert "ci_lower" in results
    assert "ci_upper" in results
    assert "h2h_v2_points_rate" in results
    assert results["ci_lower"] <= results["mean_delta"] <= results["ci_upper"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_p2_v2_bootstrap_analysis.py -v`
Expected: FAIL with "No module named 'scripts.analyze_p2_v2_confirmation'"

- [ ] **Step 3: Implement `scripts/analyze_p2_v2_confirmation.py`**

Implement whole-seed cluster bootstrap algorithm:
- Group matches by seed.
- For each seed, calculate total win points earned by Baseline (`prvsiyan_moon_counts_melons`) and V2 Challenger (`prvsiyan_global_sell_slot_challenger_reviewed`), and per-seed points rate delta.
- Resample seeds with replacement 10,000 times (deterministic seed `20260928`).
- Compute 2.5th and 97.5th percentiles.
- Extract direct head-to-head match outcomes (16 matches).
- Output comprehensive statistical report to `docs/experiments/agent_selection/p2_v2_market_slot_ordering/report.md`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_p2_v2_bootstrap_analysis.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Run analysis and generate decision verdict**

Execute:
```bash
.venv/bin/python scripts/analyze_p2_v2_confirmation.py
```
Check decision:
- If `ci_lower > 0`: Challenger is statistically confirmed positive on this panel.
- If `ci_lower <= 0 <= ci_upper`: Inconclusive; bootstrap interval crosses zero. Preserve as experiment-only.
- If `ci_upper < 0`: Reject.

- [ ] **Step 6: Commit analysis script and report**

```bash
git add scripts/analyze_p2_v2_confirmation.py docs/experiments/agent_selection/p2_v2_market_slot_ordering/report.md tests/test_p2_v2_bootstrap_analysis.py
git commit -m "feat(experiments): evaluate P2 V2 whole-seed cluster bootstrap and generate report"
```

---

### Task 5: Operational Packaging & Handoff Briefing (Gate Controlled)

**Files:**
- Modify (if promoted): `submission/submission.py` or standalone package
- Modify: `docs/experiments.md`
- Test: `tests/test_submission_standalone.py`

**Interfaces:**
- Consumes: Decision from Task 4
- Produces: Updated `docs/experiments.md` ledger and candidate submission briefing for user review.

- [ ] **Step 1: Update experiment ledger `docs/experiments.md`**

Record P2 V2 confirmation results, paired delta, bootstrap confidence interval, head-to-head record, and status verdict.

- [ ] **Step 2: If promoted (ci_lower > 0), compile and test standalone artifact**

Verify:
- Standalone single-file compilation via `submission/compile_submission.py` (or bundled single file).
- SHA256 digest recorded.
- Cold-start test and simulated 720-turn match with zero exceptions.
- License and NOTICE obligations verified.

- [ ] **Step 3: Run full workspace regression test suite**

Run: `.venv/bin/pytest -q`
Expected: All tests pass.

- [ ] **Step 4: Present Candidate Briefing to User for Authorization**

Present:
- Candidate name, SHA256 digest, Git commit.
- Measured paired points delta and 95% bootstrap CI.
- Monotonic latency metrics (max callback, % > 100ms).
- Target active slot to replace (e.g. Shepherd Sovereign Ref `56490949` at 1750.5 vs Prvsiyan Ref `56531885` at 1820.3).
- Strict adherence to rule: AWAIT EXPLICIT USER AUTHORIZATION BEFORE ANY UPLOAD.
