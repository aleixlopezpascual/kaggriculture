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
- **`src/agents/`**: High-level policy brains (MCTS strategies, rule baselines, Escalation core).
- **`src/utils/`**: Numerical calculations, pricing curves, and routing pathfinders.
- **`src/arena/`**: Evaluators, self-play suites, and head-to-head tournament managers.
- **`competitors/`**: Raw `.ipynb` competitor notebooks and their extracted/decompressed python script baselines.
- **`data/`**: Raw daily dataset manifest indexes and other telemetry csv logs.
- **`replays/`**: Telemetry JSON replays captured from match execution.
- **`submission/`**: Portable compiled submission scripts and output standalone single-file agent binaries.

---

## 🧪 4. Testing & Validation

- Write new tests under `/tests` for every bug fix or feature addition.
- Run `pytest` and verify linting with `ruff check .` before completing any development task.

---

## 🏆 5. Kaggle Submission & Matchmaking Constraints

- **The Active Matchmaking Limit (The Two-Agent Rule):** Only the **latest two submissions** are active in the live simulation pool. All older submissions are retired and freeze their Elo ratings. Currently, **Shepherd Sovereign** (Ref `56490949`, Score 2154.3, Private blank) and **Jaxa 2802 Variant B** (Ref `56467787`, Score 1786.3, Private blank) are our active submissions climbing the live ladder side-by-side (Retrieved 2026-09-23 15:44 UTC).
- **Evaluating Live Submissions:** Any comparison against the active leaderboard must be performed using exclusively the latest two submitted agents. Do not rely on scores of older submissions to evaluate real-time agent strength, as they are no longer playing new matches.
- **Leaderboard Ghosting (Hide-The-Meta Strategy):** To prevent competitor teams from scraping our match replays and performing Behavior Cloning / Imitation Learning on our elite trajectories, we must **NEVER** leave our absolute strongest agent active on the leaderboard for long periods. Once we upload a shiny new candidate and confirm it is highly competitive on the ladder, we should immediately submit a slightly weaker or older agent (a decoy) to replace it, taking our elite bot down from active evaluation until the final days of the competition.

---

## 🌾 6. Physical Simulation Parity & Rules

When building or updating agent logic, strictly align with these official physics constraints:
- **Empty Soil Parity:** In the official simulation, empty tiles (`T_EMPTY`) are already empty plantable soil. They do not require tilling (`DIG`), which acts as a no-op under official physics.
- **Maturity Check Parity:** Crop `growth_stage` is absent in official observation dicts; a crop is harvestable if and only if `yield_units > 0`.
- **Watering Parity:** Crop moisture is absent in official observations (hardcoded to 50 in parser); daily watering must be tracked exclusively via the `watered_today` flag.
- **Labor Capping:** Labor hand hiring fees scale via Fibonacci sequences starting at $500, with max hands capped at `1 + (unlocked_quadrants * 2)`.

---

## 🧠 7. Strategic Agent Traps & Solutions

- **Stateless Target Thrashing:** Multi-worker task allocation calculated from scratch on every step causes workers to swap targets and walk in circles indefinitely; resolve by mapping workers to persisted coordinate targets (`self.worker_targets`) until completion.
- **Infinite Seed-Exhaustion Loops:** Assigning planting targets on empty tiles when the farm has 0 seeds results in ignored, no-op `PLANT` actions, which keeps the targets valid and locks workers in an infinite loop; resolve by checking seed inventory before assigning/persisting `PLANT` tasks.
- **Price-Impact Seller:** Sorting multiple sell orders in descending order of their price impact (Quantity * (Current Quote - Post-Sale Quote)) maximizes trade revenue under market saturation.
- **The "Slightly Better Local Model" Fallacy (Offline Overfitting):** Micro-optimizing parameters on small local offline sweeps (e.g., shrinking `HORIZON` to 1 turn or reducing Turn-0 wash `OPEN_UNITS` to 8 to gain +$1k gold against static baselines) severely overfits. In live multiplayer matchmaking, robust macro-market dictation (24-turn pre-selling horizons to front-run town demand decay, 2-turn cash advances) generalizes far better, dominating local-sweep variants by over +140 Elo.

---

## 📦 8. Standalone Single-File Compilation

All submissions must be compiled into a single file under `/submission/submission.py`.
- **How to Compile:** Execute the compiler script from the project root:
  ```bash
  .venv/bin/python submission/compile_submission.py
  ```
- **Adding Modules:** To add a new file to the submission stack, register its relative path under the `modules` array inside `/submission/compile_submission.py` in its correct dependency order.

---

## ⚔️ 9. Elite Competitor Portfolios

This repository integrates and benchmarks the highest-Elo competitor portfolios from the Kaggle ladder inside `/competitors/notebooks/`:
- **`Jaxa 2802 Elo Router` (`jaxa_2802_router/main.py`):** The absolute world-champion router. Uses 128/128 world multi-world predictive routing forests. Local Solo Avg Gold: **`$161,858`** (100.0% win rate in tournament).
- **`Reyhan Dynamic Route Agent` (`reyhan_dynamic_router.py`):** The world-class runner-up. Uses shifted dynamic public-state decision forests. Local Solo Avg Gold: **`$172,897`** (77.8% win rate in tournament).
- **Evaluating Competitors:** Run the systematically streamlined tournament `src/arena/run_tournament.py` to evaluate your agent's win rate and average margin against these top-tier baselines.
