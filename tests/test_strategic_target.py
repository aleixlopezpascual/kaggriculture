from src.env.state import StrategicTarget, WorkerState


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


def test_worker_state_carrying_sequence():
    worker = WorkerState(
        worker_id=1,
        x=2,
        y=3,
        carrying=("Wheat", "Strawberries"),
        is_busy=False,
    )
    assert worker.carrying == ("Wheat", "Strawberries")
    assert len(worker.carrying) == 2

