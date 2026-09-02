"""Unit tests for Kaggriculture state transitions."""

from src.env.state import CropState
from src.env.transitions import step_crop


def test_step_crop_moisture_sunny():
    """Verify crop moisture depletion under Sunny conditions."""
    crop = CropState(
        crop_type="Strawberries",
        growth_stage=0,
        moisture=50,
        is_watered=False,
        x=0,
        y=0,
    )
    # Sunny weather decreases moisture by 10
    next_crop = step_crop(crop, watered=False, weather="Sunny")
    assert next_crop.moisture == 40
    assert next_crop.is_watered is False


def test_step_crop_watering():
    """Verify watering increases moisture and registers as watered."""
    crop = CropState(
        crop_type="Wheat",
        growth_stage=1,
        moisture=30,
        is_watered=False,
        x=1,
        y=1,
    )
    # Sunny weather decreases by 10, watering adds 30 -> +20 net
    next_crop = step_crop(crop, watered=True, weather="Sunny")
    assert next_crop.moisture == 50
    assert next_crop.is_watered is True


def test_step_crop_growth_optimal():
    """Verify crop grows under optimal moisture (20-90) and watering."""
    crop = CropState(
        crop_type="Wheat",
        growth_stage=1,
        moisture=50,
        is_watered=False,
        x=0,
        y=0,
    )
    next_crop = step_crop(crop, watered=True, weather="Sunny")
    # Growth stage should advance since moisture was in optimal range (50) and it was watered
    assert next_crop.growth_stage == 2
