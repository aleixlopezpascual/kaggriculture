# Kaggriculture: Competitor Analysis & Strategy Deep Dive

This document compiles findings from an exhaustive review of Kaggle community code notebooks, discussion boards, and open-source GitHub repositories for the **Kaggriculture** simulation competition (Google x Kaggle Vibe Coding, August 2026). It details the current state of the meta, winning approaches, and local testing frameworks.

---

## 🔍 1. What Approaches are Competitors Doing?

Competitors fall into three distinct camps, ranging from classical deterministic heuristics to hybrid machine learning architectures:

### A. Pure Deterministic Rule-Based Scheduling (The Ladder Dominator)
Due to Kaggriculture's **zero-tolerance mechanics** (missing a single watering cycle turns a high-value crop into weeds; missing a feeding cycle causes expensive livestock to escape) and strict **100ms per-turn response limits**, the leaderboard is heavily dominated by deterministic schedulers.
- **Priority Job Queues:** Instead of searching the entire action space, these agents parse the 10x10 grid each turn and generate an ordered list of tasks:
  $$\text{Harvest} \rightarrow \text{Feed Livestock} \rightarrow \text{Water Plants} \rightarrow \text{Clear Weeds} \rightarrow \text{Apply Care} \rightarrow \text{Plant Seeds} \rightarrow \text{Build/Expand}$$
- **Greedy Task Allocation:** Available workers (farmer + hired hands) are dispatched using greedy pathfinding (e.g., Manhattan distance or A* search) to resolve tasks starting from the top of the queue.

### B. Hybrid Strategic ML + Deterministic Execution (The SOTA Approach)
Standard Reinforcement Learning (PPO, SAC) struggles because the action space is astronomical (controlling up to 11 workers simultaneously plus up to 10 market transactions per turn). Successful ML teams use a decoupled hybrid setup:
- **The Strategic Brain (ML Model):** A lightweight neural network or heuristic model makes high-level, discrete planning decisions once per day (or every 3 turns), such as:
  - *"Should we buy another cow or 10 melon seeds?"*
  - *"Should we hire a 3rd hand today?"*
  - *"Should we buy the Eastern land quadrant?"*
- **The Execution Core (Deterministic Rules):** Once a high-level plan is active, a deterministic rule-based scheduler controls worker pathfinding, item storage (`DROP`/`PICKUP` at the shed), watering, and feeding. The model is only queried again when the sub-plan completes or a safety limit is breached.

### C. Imitation Learning / Behavior Cloning (BC)
Teams are utilizing public match replays from the Hugging Face dataset `KiroSamurai/kaggriculture-il` to pre-train policy networks. This teaches models:
- Valid action grammar (preventing invalid action logs).
- Spatial movement patterns (such as keeping workers clustered instead of scattering them).
- Optimal crop planting sequences.

---

## 🏆 2. The Ideal Path to Win (Strategic Blueprint)

Analysis of top-performing agent architectures (e.g., `deepeshumrao/kaggriculture-agent`) reveals a highly specific, dominant economic cycle required to secure a 1st-place rating:

### Phase I: The "Melon / Strawberry Rush" (Turns 0–120)
* **Goal:** Accumulate seed capital as quickly as possible.
* **Execution:** Plant nothing but high-yield crops (Melons, Strawberries) in the active NW quadrant. Keep labor low (0–1 hired hands) to preserve cash.
* **Logistics:** Ensure watering is executed with 100% reliability.

### Phase II: Labor Scaling & Fibonacci Margins (Turns 120–240)
* **Goal:** Scale labor capability without bankrupting the agent.
* **Execution:** Hire exactly **3 to 5 farm hands** per day. 
  - Hired hands scale actions linearly, but their wage increases exponentially (Fibonacci). 
  - Having 4 hands is highly cost-effective; scaling to 10 hands costs a prohibitive **$143/day**, which is only viable during a massive late-game crop gluts.

### Phase III: The Self-Sustaining Livestock Engine (Turns 240–680)
* **Goal:** Establish a massive, compounding compounding cash-flow engine.
* **Execution:** Transition from one-time crops to livestock (targeting 8 Cows and 4 Sheep).
  - **The Feed Cycle:** Dedicate 1 land quadrant strictly to growing Wheat. Wheat seeds cost $5 and harvest in 2 days. 
  - **The Consumption:** Cows and Sheep produce premium commodities (Milk, Wool) infinitely, but consume 1 Wheat daily.
  - **The Fertilizer Loop:** Livestock produce Fertilizer over time. Use workers to harvest Fertilizer and apply it to the Wheat fields, cutting crop growth times in half and boosting wheat yields. This creates a fully closed, high-margin agricultural machine.
  - **Care Mults:** Keep animal care scores high to trigger the $+1$ yield caret multipliers.

### Phase IV: Finite-Horizon Salvage Run (Turns 680–720)
* **Goal:** Liquidate all assets into cash; zero-salvage optimization.
* **Execution:** At Turn 680+:
  - Stop buying seeds and animals.
  - Stop tilling new fields.
  - Stop feeding animals (let them run away—they have no salvage value anyway).
  - Harvest every mature crop.
  - Dump the entire contents of the shed onto the market to maximize terminal liquidity.

### Phase V: Sorted Market Ordering (Front-Running)
* Market orders are processed sequentially and interleaved between players. 
* To capture premium town multipliers before prices crash:
  1. **Sort Sell Orders:** Always place high-value, high-sensitivity orders (Milk, Wool, Strawberries, Melons) at the **very top of your command list**.
  2. **Staple Ordering:** Place low-value staples (Wheat, Carrots) at the bottom. This prevents staple goods from soaking up town demand multipliers and ensures premium goods are sold at peak prices.

---

## 📊 3. How Competitors Evaluate Locally

Submitting to the Kaggle ladder is highly variable due to matchmaking noise and different opponent strategies. Top teams rely on robust local validation suites:

### A. Multi-Seed, Both-Seat Benchmarking
Because starting weather, item drops, and opponent placement are randomized, single-game evaluations are useless. Teams benchmark using:
- **Random Seeds:** A suite of **50–100 distinct seeds**.
- **Seat Invariance:** Running matches twice per seed: once with Agent A in Seat 0 (Player 1) and once in Seat 1 (Player 2).
- **Metric:** Evaluate performance based on **Win Rate** and **Elo/Trueskill progression**, rather than absolute cash totals.

### B. Lightweight Fast-Simulators
Running the full environment inside Docker can be slow. Advanced competitors have built high-speed local simulators in pure Python (using standard dataclasses) to run full 720-turn matches in under **10 milliseconds** on a single thread. This allows running millions of self-play games to optimize heuristic parameters.

### C. Replay Visualization (Krobus)
Competitors use visual replay viewers like **`Krobus`** (`rooklift/krobus`) to visualize grid states and worker paths step-by-step. This immediately reveals:
- Pathfinding inefficiencies (e.g., workers overlapping or colliding).
- Delays in item drop-off at the shed.
- Missed watering or feeding cycles.

---

## 🛠️ Community Tooling Inventory
When setting up our workspace, we should integrate or support compatibility with:
1. **`Krobus` Compatibility:** Ensure our simulator or agent logs match history files in the exact JSON format consumed by the Krobus replay viewer.
2. **Hugging Face `KiroSamurai/kaggriculture-il`:** Design our state featurizers to easily consume these JSON replays for eventual policy network training.

---

## ⚡ 4. Final-Week Meta Discoveries (September 21–23, 2026)

Deep analysis of the top-trending notebooks published during the final 48 hours before the code freeze (`shiiin9`, `ahmedberatozer` V56/V57, `statma`, `arsgorynich`) reveals five critical game mechanics and exploits that define the current 3000+ Elo ceiling:

### A. Layer D: "Your Market List Is an Order Book" (Slot-by-Slot Lockstep Execution)
*   **The Underlying Physics:** In the official Kaggle engine, both players' market lists (`farm_actions`) are settled **slot-by-slot in lockstep**:
    *   Slot 0 (Player 0) and Slot 0 (Player 1) execute simultaneously at the current quote, one unit at a time.
    *   Then Slot 1 of each player executes, and so on.
*   **The Exploit:** Units sold in earlier slots capture peak prices before later sales depress the market quote. Placing high-value premium sales (`STRAWBERRY`, `WOOL`, `MILK`) in **Slots 0 and 1** guarantees our orders fill at top dollar before the opponent dumps their harvest.
*   **The V57 Funding-Order Invariant:** When sorting orders, purchases (`HIRE`, `BUY_SEED`, `BUY_LAND`) must **never be placed in a slot earlier than the sales funding them** in the same turn. V56 had a causal bug where purchases failed due to insufficient funds; V57 guarantees that cash-generating sales execute in earlier slots than downstream purchases.

### B. The COURIER Layer: Same-Day Evening Shed Delivery
*   **The Problem:** In standard route tapes, ~40% of strawberry and milk harvests remain in worker cargo bags at Hour 20. The official engine automatically dumps worker cargo into the shed at midnight (Hour 23), meaning standard agents cannot sell the goods until the following morning.
*   **The Exploit:** Town price multipliers do not refresh between Hour 20 and the next morning's dawn. From Hour 20–22, `COURIER` diverts workers carrying premium cargo to immediately deliver to the central shed `(4,4)` and sells them on the evening market, capturing the morning's peak price **24 hours earlier than competitors**.

### C. Dynamic Species Selection (HERD2 & COWSWAP)
*   **The Concept:** Baseline routers buy fixed Day-10 geese for eggs ($50 base price).
*   **The Innovation:** The agent inspects the two town shops revealed on Day 1:
    *   If a **Yarn Store** is present, swap the Goose purchase to a **Sheep** (4 wool every 3 days at $200 base price).
    *   If an **Ice Cream or Pizza Store** is present, swap the Goose purchase to a **Cow** (3 milk every 2 days at $160 base price).
*   **Impact:** Delivers a **+30% to +50% surge in livestock profit** without modifying worker physical pathfinding schedules.

### D. Mirror Gating & Clone Exploitation (`EXP288` / `_RACE_HORIZON_CLONE`)
*   **The Mechanism:** On Turn 1, check `abs(rival_cash - own_cash) < 0.5`. If true, the opponent is an exact byte-clone executing the identical public opening.
*   **The Counter-Strategy:** Against an identified clone, activate a specialized `CLONE_MODE`:
    *   Adjust the reservation horizon (e.g. from 24 to 9 or 44) to intentionally de-synchronize from the clone.
    *   Permute the order-book sell slots so our orders consistently execute one slot ahead of the clone's identical orders, winning 100% of tiebreaker sales.

### E. RACEPX & RACEGATE: Price Floor Guards
*   **The Principle:** Pre-selling reservations (pulling future sales 24 turns forward) should **only occur when the current market price is strictly above the base price ($I_0$)**.
*   **The Defense:** If the market is already glutted (price below base price), pulling sales forward locks in a terrible price; the town drain between turns cannot recover the deficit. Gating reservations on $P > I_0$ preserves peak pricing.

