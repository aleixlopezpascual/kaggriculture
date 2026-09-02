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

---

## 🌾 Game Invariant Assertions

Maintain these game parameters in all modifications:
- Crop growth stages range from `0` (seed) to `3` (mature/harvestable).
- Moisture bounds are `0` and `100` inclusive.
- All coordinate accesses must reside within `(0, 0)` and `(grid_width-1, grid_height-1)` inclusive.
