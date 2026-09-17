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


def test_price_impact_seller_ranking():
    """Verify that rank_sell_orders correctly ranks orders dynamically based on price impact."""
    from src.utils.market import rank_sell_orders, update_market_state

    # 1. Setup a mocked observation with low inventory for strawberries (volatile) vs high for wheat
    obs = {
        "market": {
            "inventory": {
                "STRAWBERRY": 500,
                "WHEAT": 9900,
            },
            # Do not mock prices; let the pricing curves compute them dynamically
        },
        "town": {
            "unlocked_shops": ["BAKERY"]
        }
    }
    # Update cache
    update_market_state(obs)

    # 2. Test ranking of strawberries (highly volatile, high impact) vs wheat (stable, low impact)
    orders = [
        ("SELL", "Wheat", 100),
        ("SELL", "Strawberry", 20),
    ]
    ranked = rank_sell_orders(orders)

    # Strawberry should be ranked first (index 0) due to massive price impact score
    assert ranked[0][1] == "Strawberry"
    assert ranked[1][1] == "Wheat"


def test_escalation_agent_wheat_flip():
    """Verify that EscalationAgent executes the Turn 0/1/2 Wheat Flip microstructure market attack."""
    from src.agents.escalation import EscalationAgent
    from src.env.state import FarmState, WorkerState, WorldState

    farmer = WorkerState(worker_id=1, x=4, y=4, carrying=(), is_busy=False)
    farm = FarmState(gold=3000, inventory={"Wheat": 30}, seed_inventory={}, workers=(farmer,), expansion_quadrants=1)
    
    agent = EscalationAgent()

    # Turn 0
    state_0 = WorldState(turn=0, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(), farm=farm, tilled_tiles=())
    actions_0 = agent.act(state_0)
    assert actions_0["farm_actions"] == [("BUY_PRODUCT", "Wheat", 7), ("SELL", "Wheat", 2)]

    # Turn 1
    state_1 = WorldState(turn=1, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(), farm=farm, tilled_tiles=())
    actions_1 = agent.act(state_1)
    assert actions_1["farm_actions"] == [("BUY_PRODUCT", "Wheat", 30)]

    # Turn 2
    state_2 = WorldState(turn=2, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(), farm=farm, tilled_tiles=())
    actions_2 = agent.act(state_2)
    assert any(act[0] == "SELL" and act[1] == "Wheat" for act in actions_2["farm_actions"])


def test_escalation_agent_terminal_boost():
    """Verify that EscalationAgent correctly commands Drop and Harvest under Terminal Boost."""
    from src.agents.escalation import EscalationAgent
    from src.env.state import CropState, FarmState, WorkerState, WorldState

    # Worker carrying crop, located adjacent to the shed (4, 4)
    worker = WorkerState(worker_id=1, x=4, y=3, carrying=("WHEAT",), is_busy=False)
    # A mature crop on the grid
    crop = CropState(crop_type="Wheat", growth_stage=3, moisture=50, is_watered=True, x=2, y=2)
    farm = FarmState(gold=1000, inventory={}, seed_inventory={}, workers=(worker,), expansion_quadrants=1)
    
    agent = EscalationAgent()

    # Turn 715 (>= 713)
    state = WorldState(turn=715, weather="Sunny", grid_width=10, grid_height=10, crops=(crop,), animals=(), farm=farm, tilled_tiles=())
    actions = agent.act(state)

    # Worker has cargo, should move towards central shed (4, 4) -> (4, 3) to (4, 4) is Down
    assert actions["worker_actions"][1] in [("MOVE", "DOWN")]


def test_escalation_agent_livestock_feeding_and_pickup():
    """Verify that EscalationAgent routes workers to pickup Wheat and feed hungry animals."""
    from dataclasses import replace
    from src.agents.escalation import EscalationAgent
    from src.env.state import AnimalState, FarmState, WorkerState, WorldState, StrategicTarget

    # Worker has no feed, adjacent to central shed (4, 4)
    worker = WorkerState(worker_id=1, x=4, y=3, carrying=(), is_busy=False)
    # Shed contains Wheat
    farm = FarmState(gold=1000, inventory={"Wheat": 5}, seed_inventory={}, workers=(worker,), expansion_quadrants=1)
    # A hungry Cow at (0, 0)
    cow = AnimalState(animal_type="Cow", hunger=80, is_fed=False, x=0, y=0)
    state = WorldState(turn=10, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(cow,), farm=farm, tilled_tiles=())
    
    agent = EscalationAgent()
    target = StrategicTarget(target_workers=1, target_cows=1, target_sheep=0, target_geese=0, crop_priorities={}, budget_reserved_for_seeds=0.0, is_liquidating=False)
    
    # Pass 1: Worker should PICKUP Wheat from the adjacent shed
    actions = agent.act(state, target=target)
    assert actions["worker_actions"][1] == ("PICKUP", "Wheat", 1)

    # Pass 2: Worker has Wheat in bag, should path towards hungry Cow at (0,0)
    worker_with_wheat = WorkerState(worker_id=1, x=4, y=3, carrying=("Wheat",), is_busy=False)
    state_with_wheat = WorldState(
        turn=11, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(cow,),
        farm=replace(farm, workers=(worker_with_wheat,), inventory={"Wheat": 4}), tilled_tiles=()
    )
    actions_with_wheat = agent.act(state_with_wheat, target=target)
    # Path towards (0,0) from (4,3) -> West
    assert actions_with_wheat["worker_actions"][1] in [("MOVE", "LEFT"), ("MOVE", "WEST")]


def test_escalation_agent_multi_hire():
    """Verify that EscalationAgent can queue multiple hires in a single turn at start of day."""
    from src.agents.escalation import EscalationAgent
    from src.env.state import FarmState, WorkerState, WorldState, StrategicTarget

    farmer = WorkerState(worker_id=1, x=4, y=4, carrying=(), is_busy=False)
    farm = FarmState(gold=3000, inventory={}, seed_inventory={}, workers=(farmer,), expansion_quadrants=1)
    # Use Turn 10 to bypass the Turn 0/1/2 wheat microstructure overrides
    state = WorldState(turn=10, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(), farm=farm, tilled_tiles=())
    
    agent = EscalationAgent()
    target = StrategicTarget(target_workers=3, target_cows=0, target_sheep=0, target_geese=0, crop_priorities={}, budget_reserved_for_seeds=0.0, is_liquidating=False)
    
    actions = agent.act(state, target=target)
    # Should contain exactly 2 HIRE_WORKER commands to reach the target of 3 workers
    assert actions["farm_actions"].count("HIRE_WORKER") == 2


