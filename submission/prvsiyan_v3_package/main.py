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
        if (p / "baseline.py").is_file():
            return p
    for candidate in [
        Path("/kaggle_simulations/agent"),
        Path.cwd(),
        Path(),
    ] + [Path(p) for p in sys.path if p]:
        if (candidate / "baseline.py").is_file():
            return candidate.resolve()
    return Path.cwd()


_PKG_DIR = _find_package_dir()
EXPECTED_BASELINE_SHA256 = (
    "178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a"
)
EXPECTED_OPTIMIZER_SHA256 = (
    "6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59"
)
EXPECTED_METER_SHA256 = (
    "a4403a92d3274ed8aef7fd9413e86747a1573613ec83f74bcd8748e71e60ac71"
)


def _load_module(
    path: Path, expected_hash: str, subname: str
) -> types.ModuleType:
    if not path.is_file():
        raise FileNotFoundError(f"Missing package file: {path}")
    raw_bytes = path.read_bytes()
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(
            f"Component {path.name} SHA256 mismatch: "
            f"expected {expected_hash}, got {actual_hash}"
        )

    module_name = f"{__name__}._{subname}"
    mod = types.ModuleType(module_name)
    mod.__file__ = str(path)
    sys.modules[module_name] = mod
    exec(compile(raw_bytes.decode("utf-8"), str(path), "exec"), mod.__dict__)
    return mod


_OPTIMIZER_MOD = _load_module(
    _PKG_DIR / "optimizer.py", EXPECTED_OPTIMIZER_SHA256, "p3_opt"
)
_METER_MOD = _load_module(
    _PKG_DIR / "meter.py", EXPECTED_METER_SHA256, "p3_meter"
)

# Load baseline module safely
_baseline_path = _PKG_DIR / "baseline.py"
_baseline_bytes = _baseline_path.read_bytes()
if hashlib.sha256(_baseline_bytes).hexdigest() != EXPECTED_BASELINE_SHA256:
    raise ValueError("Baseline SHA256 mismatch")

_BASELINE_MOD = types.ModuleType(f"{__name__}._baseline_frozen")
_BASELINE_MOD.__file__ = str(_baseline_path)
sys.modules[f"{__name__}._baseline_frozen"] = _BASELINE_MOD
exec(
    compile(_baseline_bytes.decode("utf-8"), str(_baseline_path), "exec"),
    _BASELINE_MOD.__dict__,
)

_BASELINE_AGENT = _BASELINE_MOD.agent
_OPTIMIZER_FN = _OPTIMIZER_MOD.reorder_market_orders
_METER_FN = _METER_MOD.meter_sell_orders


def agent(
    observation: dict[str, Any], configuration: Any = None
) -> dict[str, Any]:
    try:
        raw_action = _BASELINE_AGENT(observation, configuration)
        market = raw_action.get("market") or []

        # 1. Run reviewed market slot optimizer
        optimized_market = _OPTIMIZER_FN(observation, market)

        # 2. Run disciplined commodity lot metering
        metered_market = _METER_FN(
            observation, optimized_market, max_strawberry_lot=6
        )

        return dict(raw_action, market=metered_market)
    except Exception:
        # Fallback to pure baseline action if helper raises
        try:
            return _BASELINE_AGENT(observation, configuration)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}
