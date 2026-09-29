"""
Prvsiyan Global SELL-Slot Challenger V3 (P3 Standalone Submission)
==================================================================
Standalone submission candidate package for Kaggle Kaggriculture.
Lineage: Prvsiyan "Kaggriculture Frontier — The Moon Counts Melons"
with reviewed bounded multiset permutation search across eligible SELL indices only
and disciplined commodity lot metering (capping strawberry sales to town lots).

Files in package:
- main.py (entrypoint)
- baseline.py (exact frozen Prvsiyan Moon Counts Melons baseline)
- optimizer.py (reviewed P2 market slot optimizer)
- meter.py (disciplined commodity lot metering)
- LICENSE.txt (Apache-2.0)
- NOTICE.txt (Apache-2.0 attribution notices)
"""

from __future__ import annotations

import hashlib
import sys
import types
from pathlib import Path
from typing import Any


def _find_package_dir() -> Path:
    f = globals().get("__file__")
    if f is not None:
        p = Path(f).resolve().parent
        if (p / "meter.py").is_file():
            return p
    for candidate in [
        Path.cwd() / "submission" / "prvsiyan_v3_package",
        Path("/kaggle_simulations/agent"),
        Path.cwd(),
        Path(),
    ] + [Path(p) for p in sys.path if p]:
        if (candidate / "meter.py").is_file():
            return candidate.resolve()
    return Path.cwd()


_PKG_DIR = _find_package_dir()
EXPECTED_BASELINE_SHA256 = (
    "178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a"
)
EXPECTED_HELPER_SHA256 = (
    "6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59"
)
EXPECTED_METER_SHA256 = (
    "a4403a92d3274ed8aef7fd9413e86747a1573613ec83f74bcd8748e71e60ac71"
)


def _load_verified_helper() -> types.ModuleType:
    helper_path = _PKG_DIR / "optimizer.py"
    if not helper_path.is_file():
        raise FileNotFoundError(f"Missing helper file: {helper_path}")
    helper_bytes = helper_path.read_bytes()
    actual_hash = hashlib.sha256(helper_bytes).hexdigest()
    if actual_hash != EXPECTED_HELPER_SHA256:
        raise ValueError(
            f"Helper optimizer.py SHA256 mismatch: "
            f"expected {EXPECTED_HELPER_SHA256}, got {actual_hash}"
        )

    module_name = f"{__name__}._p2_optimizer_frozen"
    helper_mod = types.ModuleType(module_name)
    helper_mod.__file__ = str(helper_path)
    sys.modules[module_name] = helper_mod

    try:
        exec(
            compile(helper_bytes.decode("utf-8"), str(helper_path), "exec"),
            helper_mod.__dict__,
        )
    finally:
        sys.modules.pop(module_name, None)
    return helper_mod


def _load_verified_meter() -> types.ModuleType:
    meter_path = _PKG_DIR / "meter.py"
    if not meter_path.is_file():
        raise FileNotFoundError(f"Missing meter file: {meter_path}")
    meter_bytes = meter_path.read_bytes()
    actual_hash = hashlib.sha256(meter_bytes).hexdigest()
    if actual_hash != EXPECTED_METER_SHA256:
        raise ValueError(
            f"Meter meter.py SHA256 mismatch: "
            f"expected {EXPECTED_METER_SHA256}, got {actual_hash}"
        )

    module_name = f"{__name__}._p3_meter_frozen"
    meter_mod = types.ModuleType(module_name)
    meter_mod.__file__ = str(meter_path)
    sys.modules[module_name] = meter_mod

    try:
        exec(
            compile(meter_bytes.decode("utf-8"), str(meter_path), "exec"),
            meter_mod.__dict__,
        )
    finally:
        sys.modules.pop(module_name, None)
    return meter_mod


def _load_verified_baseline() -> types.ModuleType:
    baseline_path = _PKG_DIR / "baseline.py"
    if not baseline_path.is_file():
        raise FileNotFoundError(f"Missing baseline file: {baseline_path}")
    source_bytes = baseline_path.read_bytes()
    actual_hash = hashlib.sha256(source_bytes).hexdigest()

    if actual_hash != EXPECTED_BASELINE_SHA256:
        raise ValueError(
            f"Frozen Prvsiyan baseline.py SHA256 mismatch: "
            f"expected {EXPECTED_BASELINE_SHA256}, got {actual_hash}"
        )

    module_name = f"{__name__}._prvsiyan_baseline_frozen"
    baseline_mod = types.ModuleType(module_name)
    baseline_mod.__file__ = str(baseline_path)
    sys.modules[module_name] = baseline_mod

    try:
        exec(
            compile(source_bytes.decode("utf-8"), str(baseline_path), "exec"),
            baseline_mod.__dict__,
        )
    finally:
        sys.modules.pop(module_name, None)
    return baseline_mod


_HELPER_MOD = _load_verified_helper()
find_eligible_sell_indices = _HELPER_MOD.find_eligible_sell_indices
optimize_sell_slots = _HELPER_MOD.optimize_sell_slots

_METER_MOD = _load_verified_meter()
meter_sell_orders = _METER_MOD.meter_sell_orders

_BASELINE_MOD = _load_verified_baseline()

# V3.1 opening restoration (see submission/prvsiyan_v21_package/main.py).
#
# baseline.py ships V9_OPENING_STEP0 = BUY 20 / SELL 15, but the comment block
# immediately above it documents the cash-safety analysis for BUY 10 / SELL 5.
# V3 inherits the identical frozen baseline and therefore the identical defect.
#
# A 960-match sweep showed the retained wheat buffer is the whole mechanism and
# must be exactly 5: every buy size in [6, 16] holding that buffer produces
# identical outcomes, while BUY 20 uniquely breaks the plateau (0% vs the Jaxa
# router lineage) and dropping the buffer below 5 is catastrophic.
#
# Rebinding the module constant keeps baseline.py byte-frozen (so its SHA-256
# integrity guard stays meaningful) while routing the change through the
# baseline's own _v9_opening overlay, which still validates the route tape.
V31_OPENING_STEP0 = (("BUY_PRODUCT", "WHEAT", 10), ("SELL", "WHEAT", 5))
_BASELINE_MOD.V9_OPENING_STEP0 = V31_OPENING_STEP0

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
    action = _BASE_AGENT(observation, configuration)
    _P2_REPORT["p2_calls"] += 1

    try:
        # Phase 2 V2: Bounded multiset permutation search on eligible SELL orders
        if (
            step >= 216
            and isinstance(action, dict)
            and "market" in action
            and isinstance(action["market"], list)
        ):
            orders = [
                list(o) if isinstance(o, (list, tuple)) else o for o in action["market"]
            ]
            eligible_indices = find_eligible_sell_indices(orders)

            if len(eligible_indices) >= 2:
                _P2_REPORT["p2_eligible_turns"] += 1
                view = _FARM_VIEW(observation)
                raw_stock = _PROJECTED_SHED(action, view)
                stock = {k: max(0, int(v)) for k, v in raw_stock.items()}
                params = _V44Y_PARAMS(observation)
                inv0 = {
                    k: int(v) for k, v in observation["market"]["inventory"].items()
                }
                opp = [list(o) if isinstance(o, (list, tuple)) else o for o in orders]
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

    # Phase 3: Apply disciplined commodity lot metering to prevent market quote crashes
    try:
        raw_mkt = action.get("market") or []
        metered_mkt = meter_sell_orders(observation, raw_mkt, max_strawberry_lot=6)
        action = dict(action, market=metered_mkt)
    except Exception:
        pass

    _sync_telemetry()
    return action


_sync_telemetry()
kaggle_submission_agent = agent
