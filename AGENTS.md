# Agentic Workspace Rules: Kaggriculture

This manual defines rules, constraints, and boundaries for AI agents (Cursor, Roo-Code, etc.) working in this repository.

---

## 📂 File Modification Boundaries

- **State Schemas (`src/env/state.py`):** DO NOT alter the core attributes of `CropState`, `AnimalState`, or `WorldState` unless specifically requested by the user. Modifying these schemas without updating parsers, utility modules, and compilers will cause compilation failures.
- **Pure Transitions (`src/env/transitions.py`):** All transitions must remain stateless and deterministic. No database writes, file storage, global caching, or API requests are permitted inside `transitions.py`.

---

## 🛠️ Verification & Testing Guardrails

1. **Strict pytest Rule:** You MUST run `pytest` and confirm that all unit tests pass before proposing any task as complete.
2. **Strict Linting Rule:** You MUST verify formatting using `black --check .` and `ruff check .`. Do not leave lint warnings unfixed.
3. **Compilation Parity:** After changing any source file in `src/`, always run `python submission/compile_submission.py` to regenerate the unified standalone script. Ensure the compiled output compiles without errors.
4. **Toolchain:** Run these via `.venv/bin/...`. If the venv is missing or empty, provision it per the "Development Setup" section of `README.md`. This project uses public PyPI only — if installs fail with `HTTP 401`, a private-index `PIP_INDEX_URL`/`UV_INDEX_URL` is set in the environment; override it as documented rather than treating the linters as unavailable.
5. **Lint Scope:** `competitors/`, `docs/`, and `submission/` are excluded from `ruff`/`black` in `pyproject.toml`. They are vendored, byte-pinned captures whose SHA-256 hashes are verified at runtime — **never reformat them**, as this breaks the integrity guards.

---

## 🌾 Game Invariant Assertions

Maintain these game parameters in all modifications:
- Crop growth stages range from `0` (seed) to `3` (mature/harvestable).
- Moisture bounds are `0` and `100` inclusive.
- All coordinate accesses must reside within `(0, 0)` and `(grid_width-1, grid_height-1)` inclusive.

---

## 🏗️ C++ Dynamic Compilation Guardrails

When working on or updating the C++ portfolios inside `/competitors/six_day_agent_source/`:
- **macOS Compilation:** Always compile the shared library to a `.dylib` using `-O3` optimization:
  ```bash
  g++ -O3 -shared -fPIC -std=c++17 policy_v2.cpp submission_bridge.cpp -o agent_v2.dylib
  ```
- **Execution Testing:** Verify compiled binary integrity by running the tournament runner `src/arena/run_tournament.py` to confirm that the C++ agent is recognized and loaded dynamically.

---

## ⚔️ Systematic Tournament Evaluation Guidelines

Before declaring any agent modification complete:
- Run the systematic head-to-head tournament:
  ```bash
  .venv/bin/python src/arena/run_tournament.py
  ```
- Ensure the newly modified version preserves its competitive win rate against baseline and competitor portfolios (especially elite portfolios like `Thomas 93.8% Router` and `Lynn Mathematical Router`).
