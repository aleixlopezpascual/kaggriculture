# Kaggriculture: Top 30 Competitor Notebook Analysis

**Date:** 2026-09-02
**Source:** Kaggle `kaggriculture` Competition Leaderboard (Top 30 by VoteCount/Score)

---

## 1. Overview and Methodology

We downloaded and analyzed the top 30 most-voted and highest-scoring Jupyter Notebooks from the active Kaggle competition ladder. The analysis focused on extracting structural architectures, strategic metadata, and execution paradigms currently defining the "Gold-Medal" tier. 

**Key Finding:** Standard Deep Reinforcement Learning (e.g., PPO, DQN, SAC) is completely absent from the top ladder. Zero exact occurrences of PPO were found in any top-tier notebook. The astronomical action space and strict 100ms timeout penalty force competitors into **Rule-Based Hybrid Systems**, **MCTS**, and **Macro-Trajectory Cloning**.

---

## 2. The Core Meta: The `8C/4S` Route

The undisputed king of the current meta is the **8C/4S Premium Lead Route** (8 Cows, 4 Sheep). This was observed explicitly in over a dozen top-tier notebooks (e.g., `v16-rc5-high-score-8c-4s-premium-market-lead.ipynb`, `v111-8c4s-economic-core-premium-lead.ipynb`).

### Why 8C/4S Works:
1. **Compounding Yields:** Cows (Milk) and Sheep (Wool) provide the highest margin-per-turn in the late game. 8 Cows and 4 Sheep precisely balance the yield throughput of a single farmer and 4 hired hands (the optimal Fibonacci wage point).
2. **Wheat Feed Loop:** The exact amount of wheat required to sustain 8C/4S can be optimally grown in exactly one unlocked land quadrant, leaving the remaining quadrants entirely dedicated to high-yield cash crops (Melons, Strawberries).

---

## 3. High-Fidelity Tactical Paradigms

### A. Replay Cloning (The "Imitation" Meta)
Many competitors (e.g., *Kaito Fukami*, *boatlee*) are not running dynamic planners from scratch. Instead, they extract public match replays of the #1 overall players (e.g., `Nikita Lugovoy's submission 55440039`) and program their agents to exactly clone the successful 719-step opening macro trajectory.
- **How they do it:** They parse out the target hiring times, land expansion triggers, and seed purchase distributions, essentially hardcoding the macro-strategy while letting a local A* / heuristic route the micro-movements.

### B. Premium Market Front-Running
Due to Kaggle's sequential processing of the command array, competitors aggressively front-run market drops. 
- Notebooks like `Shape the Shop Work the Pasture` specifically implement order-sorting logic, ensuring `SELL MILK`, `SELL WOOL`, `SELL STRAWBERRY` are the first elements in their returned action dictionaries.

### C. Fallback and "Slip" Recovery
When executing a strict 8C/4S route, weather variations (e.g., consecutive Sunny days) can cause unexpected crop death ("Weed slips"). Top notebooks (`159-160-vs-frontier-v20-weed-slip-recovery.ipynb`) dedicate significant heuristic code to:
- Instantly overriding planned movement if a crop falls below 30% moisture.
- Prioritizing `DIG` and `TILL` actions if a weed appears to quickly restore land capacity.

---

## 4. Local Validation Suites

The community explicitly acknowledges that single-submission ladder probing is noisy.
- **Seat-Invariance:** Notebooks execute heavy `Seed x Seat` cross-validation (e.g., `103/128 Fresh Public holdout`). Agents are tested on 100+ random seeds, acting as both Player 1 (Seat 0) and Player 2 (Seat 1).
- **Ablation Studies:** They remove individual logic blocks (e.g., "fixed default" vs "sparse YARN routing") and measure the delta in win rate across the holdout set to evaluate the usefulness of a feature.

---

## 5. Strategic Takeaways for Our Baseline

Our current **Gold-Medal Hybrid Agent (Decoupled MCTS + Heuristic Core)** is perfectly positioned to absorb these insights:
1. **MCTS Macro Options:** We must ensure one of our MCTS Strategic Targets is exactly `FocusLivestock(target_cows=8, target_sheep=4)` to mimic the `8C/4S` meta.
2. **Order Prioritization:** We already implemented sequential market front-running in our Heuristic Core.
3. **Emergency States:** Our Heuristic Core's "Watering Emergency" (<30% moisture) natively solves the "Weed-Slip" problem that plagues rigid replay-cloning bots.

By utilizing dynamic MCTS for macro-targets instead of brittle replay cloning, our agent possesses the resilience to recover from opponent disruption while executing the proven `8C/4S` mathematical optimal ceiling.