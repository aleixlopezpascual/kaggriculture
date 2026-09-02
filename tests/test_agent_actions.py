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
        carrying=None,
        is_busy=False,
    )
    farm = FarmState(
        gold=3000,
        inventory={"Wheat": 0, "Strawberries": 0},
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
