from typing import Any

from src.utils.commodity_lot_meter import meter_sell_orders


def test_metering_caps_strawberry_sales():
    obs: dict[str, Any] = {
        "step": 300,
        "private": {"shed": {"STRAWBERRY": 20, "WHEAT": 10}},
        "town": {"unlocked_shops": ["ICE_CREAM_SHOP"]},
    }
    orders = [["SELL", "STRAWBERRY", 16], ["SELL", "WHEAT", 10]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=6)
    assert metered[0] == ["SELL", "STRAWBERRY", 6]
    assert metered[1] == ["SELL", "WHEAT", 10]


def test_metering_bypassed_at_terminal_step():
    obs: dict[str, Any] = {
        "step": 718,
        "private": {"shed": {"STRAWBERRY": 20}},
        "town": {"unlocked_shops": []},
    }
    orders = [["SELL", "STRAWBERRY", 20]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=6)
    assert metered[0] == ["SELL", "STRAWBERRY", 20]


def test_metering_bypassed_when_shed_nearly_full():
    obs: dict[str, Any] = {
        "step": 400,
        "private": {"shed": {"STRAWBERRY": 50, "WHEAT": 42}},
        "town": {"unlocked_shops": []},
    }
    orders = [["SELL", "STRAWBERRY", 16]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=6)
    assert metered[0] == ["SELL", "STRAWBERRY", 16]


def test_metering_preserves_non_sell_orders():
    obs: dict[str, Any] = {
        "step": 200,
        "private": {"shed": {"STRAWBERRY": 10}},
        "town": {"unlocked_shops": ["ICE_CREAM_SHOP"]},
    }
    orders = [["HIRE"], ["BUY_LAND"], ["SELL", "STRAWBERRY", 12]]
    metered = meter_sell_orders(obs, orders, max_strawberry_lot=4)
    assert metered == [["HIRE"], ["BUY_LAND"], ["SELL", "STRAWBERRY", 4]]
