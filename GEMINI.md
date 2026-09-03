# Gemini CLI Workspace Guidelines: Kaggriculture

This workspace is optimized for the Kaggle Kaggriculture 720-turn simulation competition. Adhere strictly to the guidelines below to maintain system performance, safety, and codebase elegance.

---

## 🎯 1. Coding Style & Conventions

- **Language Standard:** Python 3.10+ with comprehensive type hinting (`tuple`, `dict`, `int | None`, etc.).
- **Immutability Principle:** Game states MUST remain completely immutable. Use `frozen=True` and `slots=True` on all dataclasses in `src/env/state.py`.
- **Pure-Functional Transitions:** Keep transition logic in `src/env/transitions.py` completely decoupled and stateless. Updates should return new state instances via `replace(state, ...)` or standard property instantiation.

---

## ⚡ 2. Performance & Search Optimizations

- **The 100ms Latency Limit:** Every call to `agent.act()` must return in **under 100ms** to prevent match timeouts on the live Kaggle matchmaking server.
- **Rollout Vectorization:** If expanding lookahead nodes or running Monte Carlo simulation rollouts, optimize using **NumPy vectorized operations**. Avoid running large nested loops in pure Python.
- **Worker Allocation Scaling:** Keep low-level pathfinding fast. Utilize pre-calculated Manhattan matrices or early-termination A* searches to keep pathfinding overhead to a minimum.

---

## 🔄 3. Workspace Layout Boundaries

- **`src/env/`**: Core definitions of domain models, moisture depletion rules, feeding, and JSON parsing. 
- **`src/agents/`**: High-level policy brains (MCTS strategies, rule baselines).
- **`src/utils/`**: Numerical calculations, pricing curves, and routing pathfinders.
- **`src/arena/`**: Evaluators and self-play suites for local Elo scoring.

---

## 🧪 4. Testing & Validation

- Write new tests under `/tests` for every bug fix or feature addition.
- Run `pytest` and verify linting with `ruff check .` before completing any development task.

---

## 🏆 5. Kaggle Submission & Matchmaking Constraints

- **The Active Matchmaking Limit (The Two-Agent Rule):** Only the **latest two submissions** are active in the live simulation pool. All older submissions are retired and freeze their Elo ratings (no new matches are played for them).
- **Evaluating Live Submissions:** Any comparison against the active leaderboard must be performed using exclusively the latest two submitted agents. Do not rely on scores of older submissions to evaluate real-time agent strength, as they are no longer playing new matches.
- **Leaderboard Ghosting (Hide-The-Meta Strategy):** To prevent competitor teams from scraping our match replays and performing Behavior Cloning / Imitation Learning on our elite trajectories, we must **NEVER** leave our absolute strongest agent active on the leaderboard for long periods. Once we upload a shiny new candidate and confirm it is highly competitive on the ladder, we should immediately submit a slightly weaker or older agent (a decoy) to replace it, taking our elite bot down from active evaluation until the final days of the competition.
