# Kaggriculture Discussions & Meta Summary

**Date:** 2026-09-02
**Source:** Kaggle Discussion Forums (Top Voted Topics)

An analysis of the top-voted Kaggle discussion threads reveals critical insights into how the leaderboard is currently operating, the viability of Deep Reinforcement Learning, and the systemic issues competitors are encountering.

---

## 1. The Death of End-to-End RL (Behavior Cloning & PPO)
A massive amount of community effort has been poured into training End-to-End Deep Reinforcement Learning (PPO, DQN) and Behavior Cloning (BC) models. **They have all plateaued or failed.**
- **The Cognitive Burden:** Asking a neural network to simultaneously solve high-level economic strategy AND low-level 2D grid pathfinding across an 11-worker, 720-step horizon is simply too hard. 
- **The "PASS" Collapse:** Competitors note that in free-running environments, neural networks eventually hallucinate an invalid state and default to throwing `PASS` commands for the rest of the game, completely destroying their economy.
- **The Solution:** The community consensus (e.g., Zhenyu Zhang's post) is that the only viable way forward is a **Decoupled Architecture**. A model or search tree should only select high-level "Options" (e.g., "Plant Strawberries", "Hire Hand"), while a strict, deterministic, hard-coded execution layer handles the routing, collision avoidance, and compiler legality.

## 2. Extreme Leaderboard Path Dependency
The live Kaggle Leaderboard is currently functioning as a highly volatile, path-dependent Elo ladder. **Do not trust the live public score.**
- **The "1400 Point Gap":** Competitors have submitted byte-identical agents 2 hours apart. One scored 1700, and the other climbed to >3000. 
- **Early Match Weighting:** The Kaggle matchmaking algorithm heavily weights the first ~30 matches. If your agent encounters "unlucky" RNG early on (e.g., a random weed spawns on your crops but not the opponent's), your agent's initial rating plummets. Once trapped in a low-Elo bracket, it can take days of grinding against weak bots to climb out.
- **The Stratification Problem:** It is currently very difficult to break into the top 50 if your first few matches are unlucky. The community actively complains about "false claims" of 3000+ score notebooks that are only up there because of lucky initial matchmaking.

## 3. The Final Private Leaderboard Mechanics
Because the public ladder is so noisy, competitors must understand that the live rating doesn't matter for the final prize.
- **The Final Tournament:** After the submission deadline, the Kaggle servers will run a massive, hidden Bradley-Terry tournament over two weeks. 
- **What Matters:** The system will wipe away all the early "luck" and "submission age" biases. Only the true underlying win rate of your agent against the top percentile of bots will determine the final Gold Medals.

---

### 🚀 Strategic Takeaways for Our Workspace

1. **Stop Chasing the Live Ladder:** We should not submit 10 times a day trying to get a lucky streak. We should rely exclusively on our `src/arena/evaluator.py` running 50–100 random seeds offline to mathematically prove our bot is better.
2. **We Built the Correct Architecture:** The top community minds have realized that End-to-End RL is dead, and "Decoupled Execution" is the only path forward. Our `MCTSAgent` (Strategic Brain) + `HeuristicAgent` (Tactical Execution Core) is exactly the architecture the community is begging for.
3. **Focus on Robustness:** Because early random weeds or dry spells can ruin a match, our focus must remain on ensuring our Heuristic Core handles "Weed Slips" perfectly. If our bot never crashes and never lets a crop die, it will inevitably conquer the final private tournament.

---

## 🧠 4. Deep Dive: Behavioral Cloning (BC) & DAgger in Kaggriculture

Based on an audit of the top competitor notebooks (specifically `kaggriculture-breaking-the-tie.ipynb`), here is the exact methodology top competitors use to train and deploy neural networks in Kaggriculture.

### A. The Model Architecture (`RouterNet`)
Top teams utilize a highly compact, 3-layer Multilayer Perceptron (MLP) built in PyTorch:
- **Layers:** `Linear(d -> 96)` $\to$ `ReLU` $\to$ `Linear(96 -> 64)` $\to$ `ReLU` $\to$ `Linear(64 -> 5)`.
- **Output:** Logits for 5 classes.
- **The Classes:** The outputs correspond to **5 discrete pre-compiled macro-policies (or routes)** (e.g. Strawberry NW focus, Pasture transition, Hired Hand scaling limits, or terminal liquidation), rather than individual grid coordinates or micro-actions.

### B. The Zero-Dependency Inference Trick (`py_predict`)
Importing PyTorch inside a Kaggle evaluation container takes **2–3 seconds**, causing instant timeout on Turn 1.
To bypass this, competitors train the MLP offline, extract the weights and biases into flat Python float lists inside a JSON file, and write a **custom linear algebra matrix multiplier in pure Python** for the live container. This runs the forward-pass inference in **under 0.1ms** with zero external dependencies.

### C. The DAgger (Dataset Aggregation) Loop
Because a cloned agent will inevitably drift into unfamiliar, messy states during self-play, competitors use **DAgger** to teach the student network how to self-heal and recover under random seed disturbances:
1. **Round 0 (Imitation):** Train student model on public high-Elo teacher replays.
2. **Round 1 (Rollout):** Let student play matches. When the student drifts into an unfamiliar state, query a heavy **offline search (Oracle/C95)** to calculate the correct recovery move.
3. **Dataset Aggregation:** Append these new "self-healing" states to the dataset and re-train the student. This completely eliminates the "compounding error" problem.