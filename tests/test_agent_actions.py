"""Unit tests for Kaggriculture agent decision-making and actions."""

from src.agents.heuristic import HeuristicAgent
from src.env.state import CropState, FarmState, WorkerState, WorldState
from src.utils.market import sort_market_commands


def test_heuristic_agent_harvest_priority():
    """Verify that HeuristicAgent prioritizes harvesting mature crops."""
    harvestable_crop = CropState(
        crop_type="Strawberries",
        growth_stage=3,  # Mature / Harvestable
        moisture=50,
        is_watered=True,
        x=0,
        y=1,
    )
    worker = WorkerState(
        worker_id=1,
        x=0,
        y=0,
        carrying=(),
        is_busy=False,
    )
    farm = FarmState(
        gold=3000,
        inventory={"Wheat": 0, "Strawberries": 0},
        seed_inventory={},
        workers=(worker,),
        expansion_quadrants=1,
    )
    state = WorldState(
        turn=10,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(harvestable_crop,),
        animals=(),
        farm=farm,
        tilled_tiles=(),
    )

    agent = HeuristicAgent(crop_to_plant="Strawberries")
    joint_actions = agent.act(state)

    # Worker at (0, 0) is adjacent to crop at (0, 1). It should harvest it.
    assert 1 in joint_actions["worker_actions"]
    assert joint_actions["worker_actions"][1] == ("HARVEST", 0, 1)


def test_market_orders_priority_sorting():
    """Verify that premium commodities are sorted first in market queues."""
    orders = [
        {"action": "SELL", "item": "Wheat", "quantity": 10},
        {"action": "SELL", "item": "Milk", "quantity": 5},
        {"action": "SELL", "item": "Melons", "quantity": 2},
        {"action": "SELL", "item": "Wool", "quantity": 1},
    ]
    # Premium goods (Milk, Melons, Wool) should sort before Wheat
    sorted_orders = sort_market_commands(orders)
    assert sorted_orders[0]["item"] in ["Milk", "Wool", "Melons"]
    assert sorted_orders[-1]["item"] == "Wheat"


def test_heuristic_drives_cow_target():
    """Verify that HeuristicAgent purchases a COW if below target."""
    from src.env.state import StrategicTarget

    farmer = WorkerState(
        worker_id=1,
        x=0,
        y=0,
        carrying=(),
        is_busy=False,
    )
    farm = FarmState(
        gold=1000,
        inventory={"Wheat": 0},
        seed_inventory={},
        workers=(farmer,),
        expansion_quadrants=1,
    )
    state = WorldState(
        turn=10,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(),
        animals=(),
        farm=farm,
        tilled_tiles=(),
    )
    target = StrategicTarget(
        target_workers=1,
        target_cows=1,
        target_sheep=0,
        target_geese=0,
        crop_priorities={},
        budget_reserved_for_seeds=50.0,
        is_liquidating=False,
    )
    agent = HeuristicAgent()
    joint_actions = agent.act(state, target=target)

    # Since cow count is 0 and target_cows is 1, and we have enough money,
    # the agent should trigger a "BUY_ANIMAL" or "BUY_COW" market/farm action.
    assert ("BUY_ANIMAL", "Cow") in joint_actions["farm_actions"]


def test_mcts_caches_and_selects_target():
    """Verify that MCTSAgent selects and caches a StrategicTarget at Turn 0."""
    from src.agents.mcts import MCTSAgent

    farmer = WorkerState(
        worker_id=1,
        x=0,
        y=0,
        carrying=(),
        is_busy=False,
    )
    farm = FarmState(
        gold=1000,
        inventory={"Wheat": 0},
        seed_inventory={},
        workers=(farmer,),
        expansion_quadrants=1,
    )
    state = WorldState(
        turn=0,
        weather="Sunny",
        grid_width=5,
        grid_height=5,
        crops=(),
        animals=(),
        farm=farm,
        tilled_tiles=(),
    )
    agent = MCTSAgent(num_simulations=5)
    assert agent.active_target is None

    # Calling act() should run strategic planning and cache an active_target
    _ = agent.act(state)
    assert agent.active_target is not None
