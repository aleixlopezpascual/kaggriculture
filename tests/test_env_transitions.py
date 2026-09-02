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
    # Growth stage should advance since moisture was in optimal range (50)
    # and it was watered
    assert next_crop.growth_stage == 2


def test_physical_drop_and_pickup_and_harvest():
    """Verify physical DROP, PICKUP, and harvest-to-bag transit mechanics."""
    from src.env.state import CropState, FarmState, WorkerState, WorldState
    from src.env.transitions import step_world

    # 1. Harvest to bag check
    harvestable_crop = CropState(
        crop_type="Strawberries",
        growth_stage=3,
        moisture=50,
        is_watered=True,
        x=0,
        y=1,
    )
    worker = WorkerState(worker_id=1, x=0, y=0, carrying=(), is_busy=False)
    farm = FarmState(
        gold=1000,
        inventory={},
        seed_inventory={},
        workers=(worker,),
        expansion_quadrants=1,
    )
    state = WorldState(
        turn=1,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(harvestable_crop,),
        animals=(),
        farm=farm,
        tilled_tiles=(),
    )

    actions = {"worker_actions": {1: ("HARVEST", 0, 1)}, "farm_actions": []}
    next_state = step_world(state, actions)
    # The crop should be in the worker's cargo, NOT the farm shed inventory yet!
    assert next_state.farm.workers[0].carrying == ("Strawberries",)
    assert next_state.farm.inventory.get("Strawberries", 0) == 0

    # 2. DROP check (worker adjacent to central shed 4,4)
    worker_at_shed = WorkerState(
        worker_id=1, x=4, y=3, carrying=("Strawberries",), is_busy=False
    )
    farm_at_shed = FarmState(
        gold=1000,
        inventory={},
        seed_inventory={},
        workers=(worker_at_shed,),
        expansion_quadrants=1,
    )
    state_at_shed = WorldState(
        turn=2,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(),
        animals=(),
        farm=farm_at_shed,
        tilled_tiles=(),
    )

    drop_actions = {
        "worker_actions": {1: ("DROP", "Strawberries", 1)},
        "farm_actions": [],
    }
    state_after_drop = step_world(state_at_shed, drop_actions)
    # Cargo is empty, and item resides inside the farm inventory
    assert state_after_drop.farm.workers[0].carrying == ()
    assert state_after_drop.farm.inventory.get("Strawberries", 0) == 1

    # 3. PICKUP check
    pickup_actions = {
        "worker_actions": {1: ("PICKUP", "Strawberries", 1)},
        "farm_actions": [],
    }
    state_after_pickup = step_world(state_after_drop, pickup_actions)
    # Item is moved from shed back to worker cargo
    assert state_after_pickup.farm.workers[0].carrying == ("Strawberries",)
    assert state_after_pickup.farm.inventory.get("Strawberries", 0) == 0


def test_hour_23_auto_drop_and_overflow_discard():
    """Verify that turn 23 triggers auto-drop and caps shed at 100 items."""
    from src.env.state import FarmState, WorkerState, WorldState
    from src.env.transitions import step_world

    # Shed currently has 98 items
    worker = WorkerState(
        worker_id=1, x=4, y=4, carrying=("Strawberries",) * 5, is_busy=False
    )
    farm = FarmState(
        gold=1000,
        inventory={"Wheat": 98},
        seed_inventory={},
        workers=(worker,),
        expansion_quadrants=1,
    )
    # Turn 23 is Hour 23 of Day 0
    state = WorldState(
        turn=23,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(),
        animals=(),
        farm=farm,
        tilled_tiles=(),
    )

    next_state = step_world(state, {"worker_actions": {}, "farm_actions": []})
    # Cargo is empty (auto-dropped)
    assert next_state.farm.workers[0].carrying == ()
    # Total shed items capped at 100
    total_shed = sum(next_state.farm.inventory.values())
    assert total_shed == 100


def test_animal_feeding_wheat_dependent():
    """Verify that animal feeding requires carrying 1 Wheat in cargo."""
    from src.env.state import AnimalState, FarmState, WorkerState, WorldState
    from src.env.transitions import step_world

    anim = AnimalState(animal_type="Cow", hunger=60, is_fed=False, x=0, y=1)

    # 1. Feeding without carrying Wheat (should fail / no-op)
    worker_without_wheat = WorkerState(
        worker_id=1, x=0, y=0, carrying=(), is_busy=False
    )
    farm1 = FarmState(
        gold=1000,
        inventory={},
        seed_inventory={},
        workers=(worker_without_wheat,),
        expansion_quadrants=1,
    )
    state1 = WorldState(
        turn=1,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(),
        animals=(anim,),
        farm=farm1,
        tilled_tiles=(),
    )

    actions = {"worker_actions": {1: ("FEED", 0, 1)}, "farm_actions": []}
    next_state1 = step_world(state1, actions)
    # Feeding failed, hunger is unmodified (increases by 10 per turn step to 70)
    assert next_state1.animals[0].hunger == 70
    assert next_state1.animals[0].is_fed is False

    # 2. Feeding while carrying Wheat (should succeed)
    worker_with_wheat = WorkerState(
        worker_id=1, x=0, y=0, carrying=("Wheat",), is_busy=False
    )
    farm2 = FarmState(
        gold=1000,
        inventory={},
        seed_inventory={},
        workers=(worker_with_wheat,),
        expansion_quadrants=1,
    )
    state2 = WorldState(
        turn=1,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(),
        animals=(anim,),
        farm=farm2,
        tilled_tiles=(),
    )

    next_state2 = step_world(state2, actions)
    # Successfully fed! Hunger decreases (60 - 40 + 10 = 30) and Wheat is consumed
    assert next_state2.animals[0].hunger == 30
    assert (
        next_state2.animals[0].is_fed is False
    )  # is_fed gets reset to False at end of turn step
    assert next_state2.farm.workers[0].carrying == ()
