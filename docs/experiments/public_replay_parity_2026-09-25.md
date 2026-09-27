# Experiment: Kaggle episode action-tape replay parity

**Date:** 2026-09-25
**Status:** Passed terminal reward/status parity on 3/3 captured public episodes.
**Purpose:** Complete P0 from the public-research backlog before strategy tuning.

## Question and scope

Can the local `kaggle-environments==1.32.7` engine reproduce the recorded terminal rewards when given both players' exact actions, the recorded seed, and the recorded seat order from completed Kaggle episodes?

This is a simulator/action-tape calibration, **not** an evaluation of the agents' competitive strength. The replay JSON was parsed as inert data; no downloaded notebook or opponent policy code was imported or executed.

## Method

- Retrieved the three completed public episode replays with Kaggle CLI (`kaggle competitions replay <episode_id>`). Each replay reports `module_version=1.32.7`, `episodeSteps=720`, and 720 stored state rows.
- The replay configuration's `seed` is null, so the run uses the recorded `info.seed` (and rejects a conflicting non-null configuration seed).
- Treated row 0 as the initial state. For acting turn `t`, replayed the action at `steps[t + 1][seat].action`, giving 719 actions for each seat. Each local callback checked the sequential `day * turnsPerDay + hour` clock, returned a deep copy of the recorded action, and failed closed on a missing/malformed action or extra call.
- Compared local final rewards and statuses exactly with both the top-level replay metadata and terminal row. No tolerance was used.
- This run checked per-turn clock/index alignment, but **did not perform a field-by-field diff of every observation payload**. Replay metadata identifies opponent team names, not submitted source-code lineages; distinct team identities below do not prove independent policy ancestry.

## Results

| Episode | Seed | Seat 0 | Seat 1 | Actions per seat | Recorded rewards (0, 1) | Local rewards (0, 1) | Status / parity |
|---:|---:|---|---|---:|---|---|---|
| `113283880` | `1714719438` | Aleix López | 断罪の孤高の神・大宇宙草莓覇皇 | 719 / 719 | 124586.0, 126767.0 | 124586.0, 126767.0 | DONE / exact |
| `113284254` | `493147447` | AdamHsieh | Aleix López | 719 / 719 | 100191.0, 103349.0 | 100191.0, 103349.0 | DONE / exact |
| `113283141` | `2126140119` | Aleix López | Kavinkumar M | 719 / 719 | 85041.0, 84335.0 | 85041.0, 84335.0 | DONE / exact |

**Outcome:** all six seat rewards matched exactly; all six local seat statuses were `DONE`; all six action callbacks consumed exactly 719 actions. The three opponent team identities are different. This clears the terminal reward/action-offset calibration gate for these episodes, subject to the observation-diff limitation above.

## Reproduction and provenance

Run from the repository root:

```sh
.venv/bin/python scripts/validate_replay_parity.py \
  --replay /path/to/episode-113283880-replay.json \
  --replay /path/to/episode-113284254-replay.json \
  --replay /path/to/episode-113283141-replay.json \
  --output /path/to/replay-parity-results.json
```

- Verifier: `scripts/validate_replay_parity.py`; focused tests: `tests/test_replay_parity.py`.
- Captured result JSON (profile scratch, not committed): `/Users/aleix.lopez/.hermes/profiles/kaggle-bot/cache/scratch/kaggriculture-review/replay-parity-p0-results-2026-09-25.json`.
- Raw replay SHA-256: `113283880` → `9fedd6340af150f86564e4a69a0175bc126a074fd4f58fa5112a7e631a727a31`; `113284254` → `7a89db4637e973b33e6122f958274155fcc63289e56cdf1c0133f5235b557971`; `113283141` → `3a885a276d9e657e95055ddfac42c3352c7e7c3ce3eb047a6c70d08c194bfa26`.
- Kaggle's replay-index guidance reviewed: https://www.kaggle.com/competitions/kaggriculture/discussion/737480

## Verification and caveats

- `.venv/bin/pytest -q tests/test_replay_parity.py`: **12 passed**.
- `.venv/bin/pytest -q`: **75 passed**.
- `git diff --check`: passed.
- Repo-wide style/lint checks: original 2026-09-25 counts (49 Black files would reformat, 17,966 Ruff findings, including findings in the new verifier) are retained explicitly as historical. As of 2026-09-26, repo-wide checks still fail (49 Black files would reformat; Ruff 19,383 findings), while `scripts/validate_replay_parity.py` and `tests/test_replay_parity.py` now pass scoped Black/Ruff after the monotonic-timing regression fix. No bulk formatting or unrelated cleanup was applied, and legacy files were not reformatted.
- **Dated Instrumentation Note (2026-09-26):** Subsequent to the original 2026-09-25 audit, the verifier's elapsed `runtime_seconds` instrumentation in `scripts/validate_replay_parity.py` was switched to monotonic `time.perf_counter()`, accompanied by regression test `test_validate_replay_uses_monotonic_perf_counter` in `tests/test_replay_parity.py`. This update does not alter the P0 parity findings, match rewards, or status verifications. The original 12/75 test counts above are preserved as historical results from that initial run.
- The note that no commit was created describes only the original 2026-09-25 replay run (no agent behavior change or Kaggle submission); it does not imply no commit exists now.

## Decision / next experiment

**P0 terminal-reward calibration: pass for these three episodes.** Do not overread it: it confirms deterministic local reward parity for the captured action tapes, not complete observation equality, current-opponent coverage, or a medal likelihood. The ordered next item remains P1: refresh and freeze a diverse recent opponent panel, then run paired-seed/both-seat screening and untouched confirmation before promoting any strategy change.
