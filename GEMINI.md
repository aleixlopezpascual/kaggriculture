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
