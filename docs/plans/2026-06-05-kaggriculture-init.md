# Kaggriculture Workspace Initialization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize the complete, idiomatic, fully typed Kaggriculture project with functional environment transitions, agent models, evaluation arenas, utilities, unit tests, a compilation pipeline, and detailed documentation.

**Architecture:** A pure functional, state-transition-based environment simulation matching Kaggle-style multi-agent challenges. State is represented as immutable slatted dataclasses. Transition functions are stateless utilities. Decision runtime matches greedy heuristics and pure MCTS structures. A dedicated compiler flattens modular code into a single submission bundle.

**Tech Stack:** Python 3.10+, NumPy, pytest, ruff, black.

**Spec:** `/Users/aleix.lopez/kaggriculture/README.md` (and related system instructions)

## Global Constraints
- Target python version: py310.
- Pure state transitions must be immutable. State objects use `@dataclass(frozen=True, slots=True)`.
- Ruff line-length: 88.
- Agent processing time budget per turn: < 100ms.
- High-efficiency array featurization using optimized NumPy views/operations.

---

## Tasks

### Task 1: Environment & Root Configuration
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/requirements.txt`
- Create: `/Users/aleix.lopez/kaggriculture/pyproject.toml`
- Create: `/Users/aleix.lopez/kaggriculture/README.md`

- [ ] Write `requirements.txt` with numpy, pytest, ruff, black.
- [ ] Write `pyproject.toml` configuring Black and Ruff.
- [ ] Write `README.md` with complete agronomics, market curves, wages, land expansion, and front-running order mechanics.

### Task 2: Environment State & Logic (src/env/)
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/src/env/__init__.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/env/state.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/env/transitions.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/env/parser.py`

- [ ] Implement typed frozen slots dataclasses: `CropState`, `AnimalState`, `WorkerState`, `FarmState`, `WorldState`.
- [ ] Implement stateless transitions: `step_crop(crop, watered, weather)` with water decay rules, weather adjustments, growth phases.
- [ ] Implement `step_world(state, joint_actions) -> WorldState` skeleton executing tilling, planting, harvesting, and order clearing.
- [ ] Implement `parser.py` converting Kaggle observation dicts into structured dataclasses.

### Task 3: Decision Utilities (src/utils/)
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/src/utils/__init__.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/utils/routing.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/utils/market.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/utils/calculators.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/utils/state_featurizer.py`

- [ ] Implement Manhattan distance and routing sequence generators (`["MOVE", dir]`).
- [ ] Implement premium goods prioritization logic to front-run town demand consumption.
- [ ] Implement caretakers bonus and crop yield estimators.
- [ ] Implement featurizer converting `WorldState` into flat 2D numpy arrays.

### Task 4: Agents (src/agents/)
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/src/agents/__init__.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/agents/base.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/agents/heuristic.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/agents/mcts.py`

- [ ] Create abstract `BaseAgent` with standard `act` signature.
- [ ] Implement greedy prioritized tasks `HeuristicAgent`.
- [ ] Implement standard `MCTSAgent` with selection, expansion, simulation, backpropagation.

### Task 5: Evaluation Arena (src/arena/)
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/src/arena/__init__.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/arena/evaluator.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/arena/self_play.py`
- Create: `/Users/aleix.lopez/kaggriculture/src/arena/logger.py`

- [ ] Implement 720-turn local match simulator with seed support and ELO-like ranking.
- [ ] Implement parallel self-play loop using multi-core workers.
- [ ] Implement Krobus replay logger format.

### Task 6: Unit Tests (tests/)
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/tests/__init__.py`
- Create: `/Users/aleix.lopez/kaggriculture/tests/test_env_transitions.py`
- Create: `/Users/aleix.lopez/kaggriculture/tests/test_agent_actions.py`

- [ ] Create tests verifying crop water decay, weather updates, state immutability, grid parity.
- [ ] Create tests verifying priority sorting in market transactions, and task allocation legality.

### Task 7: Submission Compiler (submission/)
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/submission/compile_submission.py`

- [ ] Implement relative import stripping, sequential class merging, and flattening into `submission/submission.py`.

### Task 8: AI System Instructions
**Files:**
- Create: `/Users/aleix.lopez/kaggriculture/GEMINI.md`
- Create: `/Users/aleix.lopez/kaggriculture/AGENTS.md`
- Create: `/Users/aleix.lopez/kaggriculture/CLAUDE.md`

- [ ] Implement system instruction files outlining specific constraints, IDE integration tips, and developer cheat-sheets.
