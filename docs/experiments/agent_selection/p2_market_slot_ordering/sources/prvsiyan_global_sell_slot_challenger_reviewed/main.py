"""
Prvsiyan Global SELL-Slot Challenger (P2) - Reviewed V2
=======================================================
Experiment-only challenger variant of the audited Prvsiyan baseline:
Lineage: Prvsiyan "Kaggriculture Frontier — The Moon Counts Melons"
Frozen Baseline Path:
  docs/experiments/agent_selection/sources/prvsiyan_moon_counts_melons/main.py

Mechanism & Invariants:
1. Loads the frozen Prvsiyan baseline by explicit relative/absolute path.
2. Verifies the exact SHA-256 before executing the baseline code.
3. Calls the frozen baseline's agent first.
4. Activated if and only if step >= 216 and standard configuration.
5. Permutes eligible SELL order objects among the EXISTING ELIGIBLE SELL INDICES ONLY.
6. Preserves exact market-list length; non-SELL, blank, and wash SELLs are pinned.
7. Conservates multiset of SELL items and quantities.
8. Scores against the baseline self-clone using baseline's lockstep scoring helpers.
9. Bounded to at most 800 unique candidates/callback, deterministic and reproducible.
10. Baseline action is retained as a no-op candidate (gain > 0.5 to adopt).
11. Optimizer failures caught securely.
12. Preserves baseline telemetry.
13. FIX V2: Secure direct execution of helper bytes avoiding sys.path shadowing.
"""

from __future__ import annotations

import hashlib
import sys
import types
from pathlib import Path
from typing import Any


def _find_workspace_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [current, *current.parents]:
        if (p / "pyproject.toml").exists() or (p / "GEMINI.md").exists():
            return p
    return current.parents[6]


_WORKSPACE_ROOT = _find_workspace_root()
EXPECTED_BASELINE_SHA256 = (
    "178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a"
)
EXPECTED_HELPER_SHA256 = (
    "6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59"
)


def _resolve_helper_path() -> Path:
    ws_candidate = _WORKSPACE_ROOT / "scripts" / "p2_market_slot_optimizer_reviewed.py"
    if ws_candidate.exists():
        return ws_candidate
    cwd_candidate = Path.cwd() / "scripts" / "p2_market_slot_optimizer_reviewed.py"
    if cwd_candidate.exists():
        return cwd_candidate
    raise FileNotFoundError(
        "Could not locate helper scripts/p2_market_slot_optimizer_reviewed.py"
    )


def _load_verified_helper() -> types.ModuleType:
    helper_path = _resolve_helper_path()
    helper_bytes = helper_path.read_bytes()
    actual_hash = hashlib.sha256(helper_bytes).hexdigest()
    if actual_hash != EXPECTED_HELPER_SHA256:
        raise ValueError(
            f"Helper p2_market_slot_optimizer_reviewed SHA256 mismatch: "
            f"expected {EXPECTED_HELPER_SHA256}, got {actual_hash}"
        )

    module_name = f"{__name__}._p2_market_slot_optimizer_reviewed_frozen"
    helper_mod = types.ModuleType(module_name)
    helper_mod.__file__ = str(helper_path.resolve())
    sys.modules[module_name] = helper_mod

    try:
        exec(
            compile(helper_bytes.decode("utf-8"), str(helper_path), "exec"),
            helper_mod.__dict__,
        )
    finally:
        sys.modules.pop(module_name, None)
    return helper_mod


_HELPER_MOD = _load_verified_helper()
find_eligible_sell_indices = _HELPER_MOD.find_eligible_sell_indices
optimize_sell_slots = _HELPER_MOD.optimize_sell_slots


def _resolve_baseline_path() -> Path:
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

    raise FileNotFoundError("Could not locate frozen Prvsiyan baseline")


def _load_verified_baseline() -> types.ModuleType:
    baseline_path = _resolve_baseline_path()
    source_bytes = baseline_path.read_bytes()
    actual_hash = hashlib.sha256(source_bytes).hexdigest()

    if actual_hash != EXPECTED_BASELINE_SHA256:
        raise ValueError(
            f"Frozen Prvsiyan SHA256 mismatch: expected {EXPECTED_BASELINE_SHA256}, "
            f"got {actual_hash}"
        )

    module_name = f"{__name__}._prvsiyan_moon_counts_melons_frozen_baseline"
    baseline_mod = types.ModuleType(module_name)
    baseline_mod.__file__ = str(baseline_path.resolve())
    sys.modules[module_name] = baseline_mod

    try:
        exec(
            compile(source_bytes.decode("utf-8"), str(baseline_path), "exec"),
            baseline_mod.__dict__,
        )
    finally:
        sys.modules.pop(module_name, None)
    return baseline_mod


_BASELINE_MOD = _load_verified_baseline()
_BASE_AGENT = _BASELINE_MOD.agent
_V44Y_PARAMS = _BASELINE_MOD._v44y_params
_V44Y_FACTOR_MARGIN = _BASELINE_MOD._v44y_factor_margin
_FARM_VIEW = _BASELINE_MOD.FarmView
_PROJECTED_SHED = _BASELINE_MOD.projected_shed
_IG_STANDARD = _BASELINE_MOD._ig_standard
_RACE_STATE = getattr(_BASELINE_MOD, "_RACE_STATE", {})

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
    combined: dict[str, Any] = {}
    base_tel = getattr(_BASE_AGENT, "telemetry", None)
    if isinstance(base_tel, dict):
        combined.update(base_tel)

    for k, v in vars(_BASELINE_MOD).items():
        if (
            isinstance(k, str)
            and (k.endswith("_REPORT") or k.endswith("_STATS"))
            and isinstance(v, dict)
        ):
            combined[k] = v

    combined.update(_P2_REPORT)
    agent.telemetry = combined  # type: ignore


def agent(observation: dict[str, Any], configuration: Any = None) -> dict[str, Any]:
    step = int(observation.get("step", 0))

    if step == 0:
        for k in _P2_REPORT:
            if isinstance(_P2_REPORT[k], float):
                _P2_REPORT[k] = 0.0
            else:
                _P2_REPORT[k] = 0

    _P2_REPORT["p2_calls"] += 1

    action = _BASE_AGENT(observation, configuration)

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

    _sync_telemetry()
    return action


_sync_telemetry()
kaggle_submission_agent = agent
