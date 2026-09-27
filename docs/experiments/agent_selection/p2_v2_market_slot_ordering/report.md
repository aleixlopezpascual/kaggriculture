# Empirical Confirmation Report: P2 V2 Market Slot Ordering

## Executive Summary

This report documents confirmation evaluation of **P2 V2** against baseline.

### Primary Decision Metric & Bootstrap Confirmation
* **Primary Metric:** Match win points rate (win=1, tie=0.5, loss=0).
* **Baseline Record:** 86-40-2 (points rate: **0.6796875**).
* **V2 Challenger Record:** 100-26-2 (points rate: **0.7890625**).
* **Paired Points Rate Difference:** **+0.109375** (+10.94%).
* **10,000 Whole-Seed Cluster Bootstrap 95% CI:** **`[0.031250, 0.203125]`**
* **Direct Head-to-Head (16 matches):** V2 won 12-2-2 (points rate **0.8125** vs **0.1875**).
* **Statistical Verdict:** **CONFIRMED_POSITIVE** (CI strictly excludes zero).

### Monotonic Timing & Latency
* Dedicated sequential profiling (60 matches, 23,008 callbacks/finalist):
  * **V2 Challenger:** **0 callbacks > 100 ms (0.0000%)**, max latency **78.75 ms**, mean p95 **2.75 ms**.
  * **Baseline:** 2 callbacks > 100 ms (0.0087%), max latency 128.16 ms, mean p95 2.81 ms.
  * V2 strictly clears the workspace `<100 ms` guideline.

### Per-Seed Paired Deltas
- Seed `134302223`: $\Delta = +0.0000$
- Seed `400914000`: $\Delta = +0.3750$
- Seed `690003990`: $\Delta = +0.1250$
- Seed `838084248`: $\Delta = +0.0000$
- Seed `839524396`: $\Delta = +0.1250$
- Seed `911995953`: $\Delta = +0.0000$
- Seed `946313351`: $\Delta = +0.1250$
- Seed `996328792`: $\Delta = +0.1250$

### Decision & Next Steps
P2 V2 confirmed positive on held-out seeds and passed latency gate.
