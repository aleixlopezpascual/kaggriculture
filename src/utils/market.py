"""Kaggriculture market prioritizing and sequential order utilities."""

import math

PREMIUM_GOODS = {"Milk", "Wool", "Strawberries", "Melons", "Strawberry", "Melon"}


def sort_market_commands(commands: list[dict]) -> list[dict]:
    """Sorts market sell actions so premium goods appear at the front.

    Assumes commands are dicts or tuples representing transactions:
    {"action": "SELL", "item": str, "quantity": int}
    """

    def priority_key(cmd: dict) -> int:
        item = cmd.get("item", "")
        # Return 0 for premium, 1 for normal
        return 0 if item in PREMIUM_GOODS else 1

    return sorted(commands, key=priority_key)


# === KAITO'S PRICE-IMPACT SELLER PORT ===

_LATEST_MARKET_STATE = {
    "inventory": {},
    "prices": {},
    "unlocked_shops": ()
}

_PRICE_FLOOR = 1
_DEMAND_ALPHA = 0.25

_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}

_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "FARMERS_MARKET": ("TOMATO", "STRAWBERRY", "MELON", "CARROT"),
    "COFFEE_SHOP": ("MILK",),
    "BURGER_JOINT": ("TOMATO", "CARROT"),
    "TACO_STAND": ("TOMATO", "WHEAT"),
    "SOUVENIR_SHOP": ("WOOL",),
}

_ITEM_NAME_MAP = {
    "WHEAT": "WHEAT",
    "CARROT": "CARROT",
    "TOMATO": "TOMATO",
    "STRAWBERRY": "STRAWBERRY",
    "MELON": "MELON",
    "EGG": "EGG",
    "MILK": "MILK",
    "WOOL": "WOOL",
    "FERTILIZER": "FERTILIZER",
    "CARROTS": "CARROT",
    "TOMATOES": "TOMATO",
    "STRAWBERRIES": "STRAWBERRY",
    "MELONS": "MELON",
    "EGGS": "EGG",
}


def update_market_state(obs: dict) -> None:
    """Updates the internal market state cache with the latest official observation."""
    global _LATEST_MARKET_STATE
    market_data = obs.get("market", {}) or {}

    # Store uppercase keys
    inventory_raw = market_data.get("inventory", {}) or {}
    _LATEST_MARKET_STATE["inventory"] = {
        str(k).upper(): int(v) for k, v in inventory_raw.items()
    }

    prices_raw = market_data.get("prices", {}) or {}
    _LATEST_MARKET_STATE["prices"] = {
        str(k).upper(): float(v) for k, v in prices_raw.items()
    }

    town_data = obs.get("town", {}) or {}
    unlocked_raw = town_data.get("unlocked_shops", []) or []
    _LATEST_MARKET_STATE["unlocked_shops"] = tuple(
        str(s).upper() for s in unlocked_raw
    )


def _shape(name: str, value: float) -> float:
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    raise ValueError(f"Unknown shape function: {name}")


def _market_price(item: str, inventory: int) -> int:
    params = _MARKET_PARAMS.get(item)
    if not params:
        return 1
    base, equilibrium, scale, below_func, below_target, above_func, above_target = params
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below_func, scale)
        price = base + amplitude * _shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / _shape(above_func, scale)
        price = base - amplitude * _shape(above_func, inventory - equilibrium)
    return max(_PRICE_FLOOR, int(round(price)))


def _demand_per_day(item_upper: str, unlocked_shops: tuple[str, ...]) -> float:
    turns_per_day = 24
    shop_interval = 4
    demand = 0.0
    for shop in unlocked_shops:
        products = _SHOP_PRODUCTS.get(shop, ())
        if item_upper in products:
            demand += (turns_per_day / shop_interval) * (
                2 if len(products) == 1 else 1
            )
    if item_upper != "FERTILIZER":
        center_interval = 24
        demand += (turns_per_day / center_interval)
    return demand


def _impact_score(item_upper: str, quantity: int) -> float:
    current_inventory = int(_LATEST_MARKET_STATE["inventory"].get(item_upper, 10000))
    current_quote = float(_LATEST_MARKET_STATE["prices"].get(
        item_upper, _market_price(item_upper, current_inventory)
    ))
    later_quote = float(_market_price(item_upper, current_inventory + quantity))
    return float(quantity) * max(0.0, current_quote - later_quote)


def _order_score(item_upper: str, quantity: int) -> float:
    score = _impact_score(item_upper, quantity)
    if score <= 0:
        return score

    current_inventory = int(_LATEST_MARKET_STATE["inventory"].get(item_upper, 10000))
    unlocked_shops = _LATEST_MARKET_STATE["unlocked_shops"]
    demand = max(0.25, _demand_per_day(item_upper, unlocked_shops))
    excess = max(0.0, current_inventory + quantity - 10000)
    urgency = min(1.0, (excess / demand) / 10.0)
    return score * (1.0 + _DEMAND_ALPHA * urgency)


def rank_sell_orders(sell_orders: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    """Ranks and sorts sell orders using Kaito's price-impact scoring algorithm.

    Falls back to normal static premium-goods ordering if no market state is active.
    """
    if not _LATEST_MARKET_STATE["inventory"] or not _LATEST_MARKET_STATE["prices"]:
        # Fallback to static premium goods sorting
        premium_goods = {"Milk", "Wool", "Strawberry", "Melon", "Egg"}
        return sorted(sell_orders, key=lambda o: 0 if o[1] in premium_goods else 1)

    rows = []
    for index, (action, item, qty) in enumerate(sell_orders):
        item_upper = _ITEM_NAME_MAP.get(str(item).upper(), str(item).upper())
        if item_upper in _MARKET_PARAMS:
            score = _order_score(item_upper, qty)
        else:
            score = 0.0
        rows.append((score, -index, (action, item, qty)))

    rows.sort(reverse=True)
    return [row[2] for row in rows]
