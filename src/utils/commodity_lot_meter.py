"""Commodity lot metering with room-guard and terminal liquidation safety."""

from __future__ import annotations

from typing import Any

_SHED_CAPACITY_EMERGENCY_THRESHOLD = 90
_TERMINAL_ACT_STEP = 718


def meter_sell_orders(
    observation: dict[str, Any],
    orders: list[list[Any]],
    max_strawberry_lot: int = 6,
) -> list[list[Any]]:
    """Meter high-elasticity crop sales (e.g.

    Strawberry) into absorption-sized lots unless near capacity or at match
    end.
    """
    if not orders:
        return orders

    step = int(observation.get("step", 0))
    if "step" not in observation:
        day = int(observation.get("day", 0))
        hour = int(observation.get("hour", 0))
        step = day * 24 + hour

    # 1. Terminal liquidation guard: always liquidate everything at match end
    if step >= _TERMINAL_ACT_STEP:
        return [list(o) if isinstance(o, (list, tuple)) else o for o in orders]

    # 2. Shed capacity emergency guard: if shed >= 90% full, do not restrict sales
    private = observation.get("private", {})
    shed = private.get("shed", {})
    total_shed = sum(int(v) for v in shed.values())
    if total_shed >= _SHED_CAPACITY_EMERGENCY_THRESHOLD:
        return [list(o) if isinstance(o, (list, tuple)) else o for o in orders]

    # 3. Dynamic lot sizing: count active strawberry-consuming shops
    shops = observation.get("town", {}).get("unlocked_shops", [])
    strawberry_shops = shops.count("ICE_CREAM_SHOP") + shops.count("SMOOTHIE_SHOP")
    effective_cap = (
        max_strawberry_lot if strawberry_shops >= 1 else max(2, max_strawberry_lot - 2)
    )

    out_orders: list[list[Any]] = []
    for order in orders:
        if not isinstance(order, (list, tuple)) or not order:
            out_orders.append(order)
            continue

        op = order[0]
        if op == "SELL" and len(order) >= 3 and order[1] == "STRAWBERRY":
            qty = int(order[2])
            metered_qty = min(qty, effective_cap)
            if metered_qty > 0:
                out_orders.append(["SELL", "STRAWBERRY", metered_qty])
        else:
            out_orders.append(list(order))

    return out_orders
