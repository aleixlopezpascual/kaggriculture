from src.env.state import StrategicTarget


def test_strategic_target_instantiation():
    target = StrategicTarget(
        target_workers=4,
        target_cows=3,
        target_sheep=2,
        target_geese=1,
        crop_priorities={"Wheat": 8, "Strawberries": 12},
        budget_reserved_for_seeds=200.0,
        is_liquidating=False,
    )
    assert target.target_workers == 4
    assert target.target_cows == 3
    assert target.crop_priorities["Wheat"] == 8
    assert target.is_liquidating is False
