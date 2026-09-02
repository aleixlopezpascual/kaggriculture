"""Kaggriculture wage, expansion, and yield mathematical calculators."""

from src.env.transitions import get_fibonacci_number


def get_worker_wage(worker_index: int, base_wage: int = 100) -> int:
    """Calculates Fibonacci-scaled worker hiring wage contract."""
    return base_wage * get_fibonacci_number(worker_index)


def get_expansion_cost(quadrant_index: int, base_cost: int = 1000) -> int:
    """Calculates exponential land expansion cost."""
    return base_cost * (2**quadrant_index)


def estimate_crop_yield(
    moisture: int, crop_type: str, has_care_bonus: bool = False
) -> float:
    """Estimates the yield of a crop based on moisture, type, and care bonuses.

    Crops suffer optimal moisture range penalties (optimal is 20 to 90).
    Outside of optimal bounds, yield drops significantly.
    Care bonus provides a 1.25x multiplier on the resulting yield.
    """
    base_yield = 1.0
    if crop_type in {"Strawberries", "Melons"}:
        base_yield = 1.5

    # Moisture penalty factor
    if 20 <= moisture <= 90:
        moisture_factor = 1.0
    else:
        # Penalize if too dry or flooded
        moisture_factor = 0.4

    yield_val = base_yield * moisture_factor
    if has_care_bonus:
        yield_val *= 1.25

    return round(yield_val, 2)
