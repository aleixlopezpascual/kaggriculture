"""
Prvsiyan Global SELL-Slot Challenger (P2)
=========================================
Experiment-only challenger variant of the audited Prvsiyan baseline:
Lineage: Prvsiyan "Kaggriculture Frontier — The Moon Counts Melons"
Frozen Baseline Path:
  docs/experiments/agent_selection/sources/prvsiyan_moon_counts_melons/main.py
Audited SHA-256: 178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a

Mechanism & Invariants:
1. Loads the frozen Prvsiyan baseline by explicit relative/absolute path.
2. Verifies the exact SHA-256 before executing the baseline code.
3. Calls the frozen baseline's agent first, preserving its core strategy and
   internal telemetry.
4. Activation Condition: Activated if and only if step >= 216 and standard
   configuration matches Prvsiyan's existing final SELL reorder gate
   (_ig_standard).
5. Permutes eligible SELL order objects among the EXISTING ELIGIBLE SELL
   INDICES ONLY.
6. Preserves exact market-list length; leaves every non-SELL order, blank/None
   slot, and wash SELL (items present in BUY_PRODUCT orders) pinned at its
   exact index.
7. Strictly conserves the multiset of SELL items and quantities; alters no
   order contents.
8. Scores against the baseline self-clone using the baseline's lockstep scoring
   helpers (_v44y_factor_margin / _v44y_lockstep).
   NOTE: Model score is a money-unbounded lockstep approximation, NOT exact cash
   or official match outcome. Full tournament outcomes, win-points rate, and
   failed-purchase telemetry are the true validation.
9. Bounded to at most 800 unique candidates/callback, deterministic and
   reproducible.
10. Baseline action is always retained as a no-op candidate; a candidate is
    adopted only for a gain > 0.5, with stable tie-breaking.
11. Optimizer failures are safely caught, returning the baseline action.
12. Preserves baseline telemetry and exposes P2 telemetry to tournament runner.
"""

from __future__ import annotations

import hashlib
import sys
import types
from pathlib import Path
from typing import Any


# Locate workspace root dynamically
def _find_workspace_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [current, *current.parents]:
        if (p / "pyproject.toml").exists() or (p / "GEMINI.md").exists():
            return p
    return current.parents[5]


_WORKSPACE_ROOT = _find_workspace_root()
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

EXPECTED_HELPER_SHA256 = (
    "1b97d5cc9fff730b9c0e529e48018891536c516b8425ffc9b2e8ffc2038de94a"
)
EXPECTED_BASELINE_SHA256 = (
    "178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a"
)


def _resolve_helper_path() -> Path:
    """Resolve the audited helper path (scripts/p2_market_slot_optimizer.py)."""
    # 1. Path relative to workspace root:
    ws_candidate = _WORKSPACE_ROOT / "scripts" / "p2_market_slot_optimizer.py"
    if ws_candidate.exists():
        return ws_candidate

    # 2. Path relative to this source file:
    rel_candidate = (
        Path(__file__).resolve().parents[6] / "scripts" / "p2_market_slot_optimizer.py"
    )
    if rel_candidate.exists():
        return rel_candidate

    # 3. Path relative to current working directory:
    cwd_candidate = Path.cwd() / "scripts" / "p2_market_slot_optimizer.py"
    if cwd_candidate.exists():
        return cwd_candidate

    raise FileNotFoundError(
        "Could not locate helper scripts/p2_market_slot_optimizer.py at "
        f"{ws_candidate}"
    )


def _verify_helper_bytes() -> None:
    """Verify the exact SHA-256 hash of the helper before importing it."""
    helper_path = _resolve_helper_path()
    helper_bytes = helper_path.read_bytes()
    actual_hash = hashlib.sha256(helper_bytes).hexdigest()
    if actual_hash != EXPECTED_HELPER_SHA256:
        raise ValueError(
            "Helper p2_market_slot_optimizer SHA256 mismatch: "
            f"expected {EXPECTED_HELPER_SHA256}, got {actual_hash}"
        )


_verify_helper_bytes()

from scripts.p2_market_slot_optimizer import (  # noqa: E402
    find_eligible_sell_indices,
    optimize_sell_slots,
)


def _resolve_baseline_path() -> Path:
    """Resolve the audited frozen Prvsiyan baseline path."""
    # 1. Path relative to this source file:
    # __file__ is docs/experiments/agent_selection/p2_market_slot_ordering/...
    # parents[3] is docs/experiments/agent_selection
    rel_candidate = (
        Path(__file__).resolve().parents[3]
        / "sources"
        / "prvsiyan_moon_counts_melons"
        / "main.py"
    )
    if rel_candidate.exists():
        return rel_candidate

    # 2. Path relative to current working directory:
    cwd_candidate = (
        Path.cwd()
        / "docs"
        / "experiments"
        / "agent_selection"
        / "sources"
        / "prvsiyan_moon_counts_melons"
        / "main.py"
    )
    if cwd_candidate.exists():
        return cwd_candidate

    # 3. Path relative to workspace root:
    ws_candidate = (
        _WORKSPACE_ROOT
        / "docs"
        / "experiments"
        / "agent_selection"
        / "sources"
        / "prvsiyan_moon_counts_melons"
        / "main.py"
    )
    if ws_candidate.exists():
        return ws_candidate

    raise FileNotFoundError(
        "Could not locate frozen Prvsiyan baseline at "
        f"{rel_candidate} or {cwd_candidate}"
    )


def _load_verified_baseline() -> types.ModuleType:
    """Load and execute frozen Prvsiyan baseline after verifying SHA-256."""
    baseline_path = _resolve_baseline_path()
    source_bytes = baseline_path.read_bytes()
    actual_hash = hashlib.sha256(source_bytes).hexdigest()

    if actual_hash != EXPECTED_BASELINE_SHA256:
        raise ValueError(
            "Frozen Prvsiyan SHA256 mismatch: "
            f"expected {EXPECTED_BASELINE_SHA256}, got {actual_hash}"
        )

    module_name = f"{__name__}._prvsiyan_moon_counts_melons_frozen_baseline"
    baseline_mod = types.ModuleType(module_name)
    baseline_mod.__file__ = str(baseline_path.resolve())
    sys.modules[module_name] = baseline_mod

    exec(
        compile(source_bytes.decode("utf-8"), str(baseline_path), "exec"),
        baseline_mod.__dict__,
    )
    return baseline_mod


# Load the audited baseline module
_BASELINE_MOD = _load_verified_baseline()
_BASE_AGENT = _BASELINE_MOD.agent
_V44Y_PARAMS = _BASELINE_MOD._v44y_params
_V44Y_FACTOR_MARGIN = _BASELINE_MOD._v44y_factor_margin
_FARM_VIEW = _BASELINE_MOD.FarmView
_PROJECTED_SHED = _BASELINE_MOD.projected_shed
_IG_STANDARD = _BASELINE_MOD._ig_standard
_RACE_STATE = getattr(_BASELINE_MOD, "_RACE_STATE", {})

# P2 Telemetry Report
_P2_REPORT: dict[str, Any] = {
    "p2_calls": 0,
    "p2_eligible_turns": 0,
    "p2_evals": 0,
    "p2_budget_hits": 0,
    "p2_changed_turns": 0,
    "p2_changed_slots": 0,
    "p2_model_gain": 0.0,
    "p2_errors": 0,
}


def _sync_telemetry() -> None:
    """Synchronize exposed telemetry combining baseline and P2 reports."""
    combined: dict[str, Any] = {}
    base_tel = getattr(_BASE_AGENT, "telemetry", None)
    if isinstance(base_tel, dict):
        combined.update(base_tel)

    # Publish references to every baseline module variable ending _REPORT/_STATS
    for k, v in vars(_BASELINE_MOD).items():
        if (
            isinstance(k, str)
            and (k.endswith("_REPORT") or k.endswith("_STATS"))
            and isinstance(v, dict)
        ):
            combined[k] = v

    combined.update(_P2_REPORT)
    agent.telemetry = combined


def agent(observation: dict[str, Any], configuration: Any = None) -> dict[str, Any]:
    """
    P2 Prvsiyan Global SELL-Slot Challenger Entrypoint.

    Calls the frozen baseline agent, then applies bounded permutation search
    across all eligible SELL slots when the activation condition is satisfied.
    """
    step = int(observation.get("step", 0))

    if step == 0:
        for k in _P2_REPORT:
            if isinstance(_P2_REPORT[k], float):
                _P2_REPORT[k] = 0.0
            else:
                _P2_REPORT[k] = 0

    _P2_REPORT["p2_calls"] += 1

    # 1. Execute baseline policy first
    action = _BASE_AGENT(observation, configuration)

    # 2. Gate condition: step >= 216 and standard configuration (matching
    # baseline final sell block reorder)
    try:
        is_standard = _IG_STANDARD(configuration)
        if step >= 216 and is_standard:
            _P2_REPORT["p2_eligible_turns"] += 1

            market = action.get("market") or []
            if len(market) >= 2:
                orders = [
                    list(o) if isinstance(o, (list, tuple)) else o for o in market
                ]
                eligible_indices = find_eligible_sell_indices(orders)

                if len(eligible_indices) >= 2:
                    # Construct scoring callback using baseline lockstep helpers
                    # against self-clone
                    view = _FARM_VIEW(observation)
                    raw_stock = _PROJECTED_SHED(action, view)
                    stock = {k: max(0, int(v)) for k, v in raw_stock.items()}
                    params = _V44Y_PARAMS(observation)
                    inv0 = {
                        k: int(v) for k, v in observation["market"]["inventory"].items()
                    }
                    opp = [
                        list(o) if isinstance(o, (list, tuple)) else o for o in orders
                    ]
                    scoring_fn = _V44Y_FACTOR_MARGIN(opp, inv0, stock, params)

                    # Optimize eligible sell slots up to 800 candidates
                    revised_orders, stats = optimize_sell_slots(
                        orders,
                        eligible_indices,
                        scoring_callback=scoring_fn,
                        budget=800,
                        min_gain=0.5,
                    )

                    _P2_REPORT["p2_evals"] += stats["evals"]
                    _P2_REPORT["p2_budget_hits"] += stats["budget_hits"]
                    _P2_REPORT["p2_errors"] += stats["errors"]

                    if stats["changed_slots"] > 0:
                        _P2_REPORT["p2_changed_turns"] += 1
                        _P2_REPORT["p2_changed_slots"] += stats["changed_slots"]
                        _P2_REPORT["p2_model_gain"] += stats["gain"]
                        action = dict(action, market=revised_orders)

                        # Maintain race state parity with baseline if active
                        player = int(observation.get("player", 0))
                        state = _RACE_STATE.get(player)
                        if (
                            state is not None
                            and state.get("prev_action") is not None
                            and state.get("step") == step
                        ):
                            state["prev_action"] = action
    except Exception:
        _P2_REPORT["p2_errors"] += 1

    # 3. Synchronize exposed telemetry combining baseline report, baseline
    # module globals, and P2 report
    _sync_telemetry()

    return action


_sync_telemetry()
kaggle_submission_agent = agent
