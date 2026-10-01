# AI Workflow Post-Mortem & Competitive Strategist Playbook

**Competition:** Kaggle Kaggriculture (720-step multi-agent agricultural & economic simulation)  
**Date:** October 1, 2026  
**Audience:** Competitive AI Engineers, Kaggle Grandmasters, Simulation Specialists  
**Scope:** Evaluation of Human-LLM Collaboration, Operational Bottlenecks, and the 5-Step Playbook for Future Competitions

---

## Executive Summary

Across the 2026 Kaggle Kaggriculture campaign (10,246 competing teams), our workspace achieved exceptional **engineering and execution rigor**:
- **Zero Simulation Crashes:** Pure-functional, immutable state transitions (`frozen=True`, `slots=True`) achieving 100% parity with official physics across 139 automated tests.
- **Superior Mathematical Optimality:** Replaced the community's fragile 41-wrapper chain (`Step1009`) with an exact $O(K!)$ bounded permutation search running in $<78.75\text{ ms}$ (mean $2.75\text{ ms}$).
- **Automated Toolchain:** Standalone AST compiler, counterfactual replay parsers, and a paired seed/seat head-to-head tournament arena.

However, the campaign encountered a **hard strategic ceiling**: while our agents dominated baseline heuristics and reached competitive ratings (~1,800–2,000 Elo), we did not autonomously discover the breakthrough macro-architectures defining the 3,000+ Elo frontier (such as DECEM's 1-tile radial hub geometry or Day 0 dual-species kickstart).

This post-mortem diagnoses why this occurred: **it was not a failure of coding or software architecture, but a structural limitation in how the LLM was prompted, framed, and integrated into the search loop.**

---

## 1. Underutilized Capabilities: What Was Missed

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THE THREE MISSED FRONTIER LEVERS                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. THE "FUNSEARCH / EUREKA" MUTATION LOOP                             │
│    • From: Conversational prompts ("make it score higher").           │
│    • To: Headless daemon mutating functions + autonomous test cycles. │
├────────────────────────────────────────────────────────────────────────┤
│ 2. CAUSAL REPLAY FORENSICS (DIFFERENTIAL JSON PROMPTING)               │
│    • From: Abstract macro ideation.                                    │
│    • To: Point-in-time delta analysis between winning/losing replays. │
├────────────────────────────────────────────────────────────────────────┤
│ 3. ADVERSARIAL MULTI-AGENT TRIADS (SYCOPHANCY BREAKERS)                │
│    • From: Single model acting as architect, coder, and judge.         │
│    • To: Challenger Agent vs. Red-Team Opponent Exploiter.             │
└────────────────────────────────────────────────────────────────────────┘
```

### A. The "FunSearch / Eureka" Automated Mutation Loop
- **The Workflow Used:** Conversational prompting (*"Improve current agents by running local simulations until it finds a better candidate"*).
- **The Missed Capability:** In competitive simulation programming (inspired by DeepMind's *FunSearch* and NVIDIA's *Eureka*), human-in-the-loop chatting is replaced by a headless script:
  1. An orchestrator extracts an isolated policy module (e.g., `plan_market_orders()` or `assign_worker_targets()`).
  2. The LLM is prompted via API with the target function, environmental invariants, and the failure logs of the previous 3 attempts.
  3. The harness runs a 30-seed tournament against a fixed benchmark.
  4. If win-rate delta $\le 0$, the git worktree automatically reverts and attempts a new mutation prompt.
- **The Consequence:** Human supervision created an iteration bottleneck of 5–10 manual turns per day instead of 200+ autonomous overnight mutations.

### B. Causal Replay Forensics via Differential Prompts
- **The Workflow Used:** Asking the model to "invent" or "brainstorm" strategic improvements in the abstract.
- **The Missed Capability:** LLMs struggle at unconstrained game-theoretic synthesis from scratch, but excel at **comparative log analysis**. The highest-leverage prompt in simulation competitions is the **differential trace prompt**:
  > *"Here is the telemetry JSON for Seed 848617604. At Step 288, our cash led DECEM by +$7,000. By Step 456, we trailed by -$16,000. Compare the shed inventory transactions, worker coordinates, and crop moisture levels of both players across this window. Identify the exact physical divergence."*
- **The Result:** When given differential logs, LLMs instantly identify concrete physical mechanisms (e.g., DECEM's workers taking 3 steps to feed cows vs. our workers taking 14 steps; or shed capacity overflowing and purging valuable strawberries).

### C. Adversarial Multi-Agent Triads
- **The Workflow Used:** Single-agent loop where the same model generated code, reviewed its own logic, and evaluated the results.
- **The Missed Capability:** LLMs suffer from severe confirmation bias and sycophancy when auditing their own code. Implementing an adversarial pair prevents rationalizing bad heuristics:
  - **The Architect:** Implements an optimization hypothesis.
  - **The Exploiter (Red Team):** Prompted strictly as an aggressive adversary: *"You are an opponent playing against this updated code. What edge cases (e.g. 5 consecutive sunny days, opponent dumping wheat on Step 0, shed saturation) will break this logic and cause a match loss?"*

---

## 2. Workflow Bottlenecks: Human Drag vs. AI Automation

| Operational Bottleneck | What Happened Manually | What Should Have Been Automated | Lost Leverage |
|:---|:---|:---|:---|
| **Human-in-the-Loop Hill Climbing** | Human monitored each prompt turn, inspected terminal outputs, and made manual "keep/revert" decisions. | A Python daemon running headless mutation loops logging to an SQLite results database. | Iteration throughput was limited to waking hours and manual attention. |
| **Monolithic Kernel Decompilation** | Reading through 9,000-line monolithic public notebooks (`Step1009`, `GuruPrasaath`) to find edits. | Automated AST diff script: stripping boilerplate, formatting, and isolating purely the new function definitions. | Hours spent parsing redundant wrapper code instead of analyzing strategy shifts. |
| **Matchmaking Telemetry Tracking** | Manually checking Kaggle submissions via CLI every few hours. | Background daemon scraping public episode APIs, computing live rating drift ($\Delta \text{Elo}/\text{ep}$), and flagging opponent archetype shifts. | Chasing variance by resubmitting identical code near the deadline. |

---

## 3. Quality & Accuracy Control: Defeating the "Local Mirage"

The defining empirical discovery of this campaign (`docs/experiments.md` §1) was **The "Slightly Better Local Model" Fallacy**: an offline parameter sweep produced +$1,051 higher gold against a static baseline, but resulted in a **-149.4 Elo collapse** on the live ladder.

### Why the AI Misled the Optimization
When instructed to optimize parameters against a local simulator, the AI naturally optimized for the *low-entropy, passive environment* present in the test script. In that static context, delaying sales until maturity eliminated rare instances where early sales starved animal feed budgets. But in live multiplayer matchmaking, passive selling dumped crops directly into saturated markets.

### The Accuracy Control Protocol for Future Contests

```
┌────────────────────────────────────────────────────────────────────────┐
│               HETEROGENEOUS 4-ARCHETYPE VALIDATION MATRIX             │
├────────────────────────────────────────────────────────────────────────┤
│ Candidate must score positive net win-rate against ALL FOUR:           │
│                                                                        │
│ 1. THE FAST DUMPER        → Aggressively clears orders in Slots 0–1.   │
│ 2. THE RADIAL LIVESTOCK   → Replays DECEM's Day 0 Cow/Sheep schedule.  │
│ 3. THE IDENTICAL CLONE    → Replays candidate's own twin (tiebreakers).│
│ 4. THE PASSIVE BASELINE   → Measures raw unhindered economic yield.    │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Heterogeneous Opponent Matrix:** Never validate against a single baseline. A candidate must show non-negative delta against a Fast Dumper, a Heavy Livestock agent, an Identical Clone, and a Passive Baseline across paired seats ($2 \times \text{Seeds} \times \text{Opponents}$).
2. **Assertion-Driven Contract Guardrails:** Embed inviolable runtime contracts into the simulation harness. The harness must instantly reject any AI-generated agent that:
   - Takes $>85\text{ ms}$ on any turn (timeout safety margin).
   - Suffers worker target thrashing (swapping targets for $>2$ turns without movement).
   - Generates cash-bounced transactions (purchases preceding sales in the same turn).

---

## 4. The 5-Step Actionable Playbook for Future Competitions

To break into the Gold and Master tier in future simulation and multi-agent competitions, apply these five foundational workflow rules:

### Step 1: Model Triangulation by Cognitive Domain
Do not rely on a single LLM for all engineering tasks. Assign specialized models to their core competencies:
- **Claude 3.5 Sonnet / Opus:** Primary code architect for **spatial algorithms, 2D grid pathfinding, and multi-file refactoring**.
- **OpenAI Reasoning Models (o1 / o3-mini):** Lead for **combinatorial optimization, game theory, and mathematical proofs** (e.g. $O(K!)$ permutation bounds, dynamic programming tables).
- **Gemini CLI / Flash:** Orchestrator for **large-context ingestion, digesting 40+ competitor notebooks simultaneously, and high-throughput CLI tool automation**.

### Step 2: Invert the Prompt Direction (Diagnose Delta, Don't Guess Strategy)
- **Anti-Pattern:** *"AI, look at our agent and write new strategy logic to get a higher score."*  
  *(Produces generic heuristic bloat, hallucinated parameter gains, and fragile rules).*
- **Winning Pattern:** *"Here is the action trace of our agent on Seed 42 ($78k) and the world champion's trace on Seed 42 ($105k). Identify the 3 points where cumulative value diverged most sharply. Propose a targeted 15-line wrapper resolving Divergence #1."*

### Step 3: Build the Headless "Mutation Daemon" on Day 1
Before developing complex agent heuristics, build an automated local evaluation harness:
```bash
python run_autoloop.py --target-module src/agents/market.py --iterations 50
```
The daemon extracts candidate functions, calls the LLM API with targeted feedback, runs a 30-seed tournament, parses win rate, and automatically commits winning diffs or rolls back.

### Step 4: Enforce the Heterogeneous Opponent Panel Before Touching Code
Construct a local benchmark pool containing at least 4 fundamentally different opponent archetypes (fast seller, heavy livestock, identical clone, passive baseline) evaluated in both seats. Eliminate all offline single-baseline sweeps.

### Step 5: Implement the Mathematical "Variance vs. Target" Submission Rule
Formally adhere to the statistical rule established in Phase 14:
- **Never replace your best-observed live submission to chase variance unless the target medal threshold is within $\le 1$ standard deviation ($\sigma$) of your rating.**
- If the cutoff is $>2\sigma$ away, submitting identical code or random micro-variants has negative expected value. Allocate daily submission quotas exclusively to **fundamentally distinct macro-architectures**, never to parameter noise.

---

## Document Status & Repository Cross-References
- **Document Path:** `docs/ai_workflow_post_mortem_and_playbook.md`
- **Related Retrospectives:**
  - Full Experiment Ledger: [`docs/experiments.md`](experiments.md)
  - DECEM World #2 Forensics: [`docs/decem_world_2_playbook.md`](decem_world_2_playbook.md)
  - Master Engineering Retrospective: [`docs/kaggriculture_master_retrospective_2026_09_23.md`](kaggriculture_master_retrospective_2026_09_23.md)
  - Post-Competition Top Solutions Analysis: [`docs/post_competition_top_solutions_analysis.md`](post_competition_top_solutions_analysis.md)
