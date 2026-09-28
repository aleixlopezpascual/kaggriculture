"""
P3 Metered Challenger Agent
===========================
Integrates our confirmed P2 V2 market slot optimizer with disciplined
commodity lot metering (capping strawberry sales to town absorption lots).
Preserves room-guard inventory safety and 100ms latency limits.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from src.utils.commodity_lot_meter import meter_sell_orders


def _resolve_pkg_main() -> Path:
    f = globals().get("__file__")
    if f is not None:
        p = (
            Path(f).resolve().parent.parent.parent
            / "submission"
            / "prvsiyan_v2_package"
            / "main.py"
        )
        if p.is_file():
            return p
    for base in [
        Path.cwd() / "submission" / "prvsiyan_v2_package",
        Path("submission/prvsiyan_v2_package"),
    ]:
        candidate = base / "main.py"
        if candidate.is_file():
            return candidate.resolve()
    return Path("submission/prvsiyan_v2_package/main.py").resolve()


_PKG_MAIN = _resolve_pkg_main()

_spec = importlib.util.spec_from_file_location("prvsiyan_v2_submodule", str(_PKG_MAIN))
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load P2 V2 package from {_PKG_MAIN}")

_p2_v2_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_p2_v2_mod)


def agent(observation: dict[str, Any], configuration: Any = None) -> dict[str, Any]:
    # 1. Run verified P2 V2 optimizer
    raw_action = _p2_v2_mod.agent(observation, configuration)

    # 2. Apply disciplined commodity lot metering
    market_orders = raw_action.get("market") or []
    metered_market = meter_sell_orders(observation, market_orders, max_strawberry_lot=6)

    return dict(raw_action, market=metered_market)
