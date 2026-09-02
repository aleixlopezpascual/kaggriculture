"""Kaggriculture market prioritizing and sequential order utilities."""

PREMIUM_GOODS = {"Milk", "Wool", "Strawberries", "Melons"}


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
