# Kaggriculture: Multi-Agent AI & Macro-Economic Simulation Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter: ruff](https://img.shields.io/badge/linter-ruff-red.svg)](https://github.com/astral-sh/ruff)
[![Tests: pytest](https://img.shields.io/badge/tests-139%20passed-brightgreen.svg)](tests/)
[![Kaggle: Simulation](https://img.shields.io/badge/kaggle-simulation-20BEFF.svg)](https://www.kaggle.com/competitions/kaggriculture)

**Kaggriculture** is an engineering research workspace and high-performance multi-agent simulation framework designed for the Kaggle Kaggriculture simulation competition. Agents compete head-to-head over 720 turns to optimize farm management, soil agronomics, moisture mechanics, livestock production, Fibonacci worker logistics, quadrant land expansion, and dynamic town market clearance curves.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Game Engine Mechanics & Formulas](#game-engine-mechanics--formulas)
  - [1. Agronomics & Moisture Life-Cycle](#1-agronomics--moisture-life-cycle)
  - [2. Dynamic Market Curves & Clearance Queue](#2-dynamic-market-curves--clearance-queue)
  - [3. Fibonacci Labor Wage Contracts](#3-fibonacci-labor-wage-contracts)
  - [4. Land Expansion Costs](#4-land-expansion-costs)
  - [5. Order Execution Microstructures](#5-order-execution-microstructures)
- [Key Strategic Discoveries & SOTA Insights](#key-strategic-discoveries--sota-insights)
- [Repository Organization](#repository-organization)
- [Quickstart & Development Setup](#quickstart--development-setup)
  - [Environment Provisioning](#environment-provisioning)
  - [Running the Head-to-Head Tournament](#running-the-head-to-head-tournament)
  - [Compiling Standalone Submissions](#compiling-standalone-submissions)
  - [Testing and Linting](#testing-and-linting)
- [Research & Tournament Retrospective Archive](#research--tournament-retrospective-archive)
- [License & Attributions](#license--attributions)

---

## Overview

In Kaggriculture, two competing agricultural syndicates manage parallel 2D farm plots over a 720-step horizon. While farm plots operate independently, both agents compete for liquidity in a single shared, dynamic town marketplace.

Success requires balancing micro-level operations (pathfinding, tilling, watering, fertilizing, harvesting) with macro-economic strategy (front-running town demand decay, predicting market saturation, timing capital deployment for labor hiring and land expansion).

---

## System Architecture

The codebase is built on strict software engineering principles: **immutability**, **pure-functional state transitions**, and a **fully decoupled architecture**:

```
kaggriculture/
├── src/
│   ├── env/          # Immutable dataclasses & stateless transition physics
│   ├── agents/       # Multi-route predictive routers, MCTS & rule policies
│   ├── utils/        # Pathfinders, market curves, price impact calculators
│   └── arena/        # High-throughput head-to-head tournament runner
├── competitors/      # Elite 2800+ Elo competitor agent portfolio & extracted tapes
├── submission/       # Standalone compiler, manifest verifiers, & single-file artifacts
├── scripts/          # Counterfactual replay parsers, latency meters, & A/B testers
├── docs/             # Technical designs, replay playbooks, & experiment retrospectives
└── tests/            # Exhaustive test suite (139 unit & integration tests)
```

- **`src/env/`**: Fast, immutable game-state representation (`frozen=True`, `slots=True`) with stateless transitions (`src/env/transitions.py`) guaranteeing parity with official Kaggle simulation physics.
- **`src/agents/`**: Policy implementations ranging from foundational rule heuristics to Monte Carlo Tree Search lookahead planners and multi-world predictive routers.
- **`src/utils/`**: Numerical routines for market pricing curves, sequential impact orderers, and spatial pathfinders.
- **`src/arena/`**: Multi-agent tournament engine that executes round-robin simulations across paired seats and fresh seeds with detailed win/loss and coin margin diagnostics.
- **`submission/`**: Zero-dependency bundler that collapses modular multi-file pipelines into self-contained single-file submission scripts (`submission.py`) with byte-level integrity verification.

---

## Game Engine Mechanics & Formulas

### 1. Agronomics & Moisture Life-Cycle
Soil tile state evolves on every step according to agricultural and atmospheric conditions:
- **Tilled Soil**: Planting consumes the tilled state; harvesting restores it. Empty tiles are naturally plantable under official physics.
- **Moisture Level**:
  - Maximum moisture is capped at $100$.
  - Water level evolves dynamically based on turn weather:
    $$\text{Moisture}_{t+1} = \text{Moisture}_t - \text{Decay}(\text{Weather})$$
    - **Sunny**: $-10$ moisture per turn.
    - **Overcast**: $-5$ moisture per turn.
    - **Rainy**: $+15$ moisture per turn (capped at $100$).
  - Crops suffer yield decay if moisture falls below $20$ (drought) or rises above $90$ (flood state).

### 2. Dynamic Market Curves & Clearance Queue
The town market follows an automated demand-responsive pricing mechanism. Market clearance rates and price appreciation/depreciation depend on remaining town inventory:
- **Town Inventory Ratio ($IR$)**:
  $$IR = \frac{\text{Current Inventory}}{\text{Target Capacity}}$$
- **Pricing Curve**:
  $$\text{Market Price} = \text{Base Price} \times \left(1.5 - IR\right)$$
- Premium goods (Milk, Wool, Strawberries, Melons) exhibit aggressive price appreciation when town shelves are depleted, and sharp price drops when cleared in large unmetered batches.

### 3. Fibonacci Labor Wage Contracts
Hiring farm hands scales labor throughput at non-linear capital cost. Hands are contracted via a Fibonacci activation schedule:
$$\text{Wage}(n) = \text{Base Wage} \times F(n)$$
where $F(n)$ is the $n$-th Fibonacci term ($500$, $500$, $1000$, $1500$, $2500$, ...). Hands are capped at $1 + 2 \times \text{Unlocked Quadrants}$.

### 4. Land Expansion Costs
Farms can unlock adjacent land quadrants to scale farming and animal pastures. The cost of acquiring quadrant $k$ grows exponentially:
$$\text{Expansion Cost}(k) = \text{Base Cost} \times 2^k$$

### 5. Order Execution Microstructures
Market orders execute sequentially in the clearance queue. An agent selling early in a turn front-runs town demand decay, realizing higher prices before rival sales deplete town buying capacity.

---

## Key Strategic Discoveries & SOTA Insights

Across hundreds of tournament matches, replay analyses, and live ladder evaluations, several critical engineering insights were established:

1. **The "Slightly Better Local Model" Fallacy (Offline Overfitting):**
   Micro-optimizing parameters against static offline opponents (e.g., shrinking lookahead horizons to 1 turn to capture minor local gains) fails in live multiplayer matchmaking. Robust macro-market dictation (long-horizon pre-selling to front-run town demand decay) dominated local-sweep variants by over $+140$ Elo on the live ladder.

2. **Price-Impact Order Sorting:**
   Selling multiple commodities in descending order of their price impact:
   $$\text{Impact} = \text{Quantity} \times (\text{Current Quote} - \text{Post-Sale Quote})$$
   consistently maximizes revenue under market saturation.

3. **Commodity Lot Metering:**
   Unmetered bulk liquidation of high-tier crops (e.g. Strawberries, Melons) instantly collapses town price multipliers. Throttling sales into disciplined town lots (e.g., lots of $\le 6$) prevents price slippage and yields superior cumulative gold.

4. **Dead Stock Liquidation:**
   Carrying inventory into the terminal turns that will never be sold wastes shed capacity. Activating terminal liquidation guarantees converting surplus goods into liquid gold without stalling worker queues.

5. **Multi-World Predictive Routing:**
   State-of-the-art agents (such as the Jaxa 2802 and Meta V4 architectures) utilize multi-world predictive routing forests: matching initial observed public state against pre-computed optimal trajectory banks to execute high-margin, error-free playbooks.

---

## Repository Organization

```text
├── src/                          # Primary framework source code
│   ├── agents/                   # Agent policies (base, heuristic, mcts, escalation)
│   ├── arena/                    # Multi-agent simulation arena & tournament runner
│   ├── env/                      # Environment models, parser, & state transitions
│   └── utils/                    # Routing, pathfinding, calculators, & featurizers
├── competitors/                  # Top-tier competitor baselines & extracted scripts
│   ├── notebooks/                # Vendored competitor research notebooks (.ipynb)
│   ├── jaxa_2802_router/         # Jaxa 2802 Elo multi-world router
│   ├── tetsu_smart_router/       # Tetsu market-smart router baseline
│   └── six_day_agent_source/     # Six-day public-state C++ runtime baseline
├── data/                         # Manifest indexes and telemetry metadata
├── docs/                         # Extensive research documentation and retrospectives
│   ├── experiments/              # A/B test logs, selection reports, and parity studies
│   ├── decem_world_2_playbook.md # Strategy teardown of World #2 DECEM agent
│   └── experiments.md            # Comprehensive phase-by-phase experiment ledger
├── scripts/                      # Evaluation utilities, parsers, and packaging tools
├── submission/                   # Single-file submission compiler & candidate packages
│   ├── compile_submission.py     # Main compilation script
│   └── submission.py             # Generated Kaggle submission artifact
└── tests/                        # Full test suite covering env, agents, and rules
```

---

## Quickstart & Development Setup

### Environment Provisioning

This project requires **Python 3.10+** and depends exclusively on public PyPI packages:

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

*Note for shells exporting private `PIP_INDEX_URL` / `UV_INDEX_URL`: override with public PyPI:*
```bash
PIP_INDEX_URL=https://pypi.org/simple PIP_EXTRA_INDEX_URL= pip install -r requirements.txt
```

### Running the Head-to-Head Tournament

Simulate round-robin matches between agents using the built-in arena tournament runner:

```bash
# Run tournament across default candidate pool
.venv/bin/python src/arena/run_tournament.py
```

The runner outputs:
- Per-match live progression and gold scores.
- Summary table with win rates, average gold, and margins.
- Full head-to-head matchup win-loss matrix.

### Compiling Standalone Submissions

Kaggle requires self-contained single-file submissions. The compiler concatenates dependencies in topological order, verifies imports, and performs syntax validation:

```bash
.venv/bin/python submission/compile_submission.py
```

Output is written to `submission/submission.py`.

### Testing and Linting

The repository maintains strict testing and styling standards:

```bash
# Run full automated test suite (139 tests)
.venv/bin/python -m pytest

# Check code formatting and linting
.venv/bin/ruff check .
.venv/bin/black --check .
```

---

## Research & Tournament Retrospective Archive

The `docs/` directory contains comprehensive analyses from each phase of the competition:

| Document | Description |
|:---|:---|
| [`docs/experiments.md`](docs/experiments.md) | **Experiment Version Ledger**: 15 distinct development phases, ablation studies, and mathematical retrospectives. |
| [`docs/decem_world_2_playbook.md`](docs/decem_world_2_playbook.md) | Deep forensic analysis of World #2 rank agent DECEM (3,021+ Elo) reverse-engineered from public replays. |
| [`docs/kaggriculture_system_design.md`](docs/kaggriculture_system_design.md) | Core system architecture, state transitions, and simulation physics specification. |
| [`docs/kaggriculture_master_retrospective_2026_09_23.md`](docs/kaggriculture_master_retrospective_2026_09_23.md) | Retrospective on SOTA tournament, non-transitive matchups, and route-planning trade-offs. |
| [`docs/competitor_tournament_results_2026_09_23.md`](docs/competitor_tournament_results_2026_09_23.md) | Empirical tournament leaderboard comparing top public and private architectures. |

---

## License & Attributions

- **License:** Distributed under the [Apache License 2.0](LICENSE).
- **Competitor Lineages:** Third-party baselines in `competitors/` are collected from public Apache-2.0 Kaggle notebooks with full attribution and SHA-256 integrity pinning documented in [`docs/experiments.md`](docs/experiments.md).
