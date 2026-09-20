from src.env.state import FarmState, WorldState
from src.utils.sale_reservation import BoundedSaleReservation

def test_debt_deduction_and_suppression():
    # Setup mock state with 10 Wheat in shed
    farm = FarmState(gold=1000, inventory={"Wheat": 10}, seed_inventory={}, workers=(), expansion_quadrants=1)
    state = WorldState(turn=300, weather="Sunny", grid_width=10, grid_height=10, crops=(), animals=(), farm=farm, tilled_tiles=())
    
    # We instantiate our reserve optimizer
    reserver = BoundedSaleReservation()
    
    # Mock future actions: we have 10 Wheat ready now, but tape scheduled it for later.
    # On turn 300, parent wants no actions. But we look ahead and pull a future ("SELL", "Wheat", 10) early.
    reserver.debt_records["Wheat"] = 0
    reserver.current_shop_block = 4 # block 4 (300 // 72)
    
    # Simulate turn 300 with lookahead pulling it early
    # parent_market_actions = [] -> reserver looks ahead and pulls ("SELL", "Wheat", 10) early because we have 10 in stock
    # Let's test the process_turn with a simulated lookahead list
    mock_future_tape = [("SELL", "Wheat", 10)]
    
    actions = reserver.process_turn_with_future(state, [], mock_future_tape)
    
    # 1. We expect the sale to be pulled early
    assert ("SELL", "Wheat", 10) in actions
    # 2. We expect debt to be registered
    assert reserver.debt_records["Wheat"] == 10
    
    # 3. On a future turn, parent wants to run the scheduled ("SELL", "Wheat", 10)
    # The reserver must intercept and eat/suppress it due to debt!
    actions_future = reserver.process_turn_with_future(state, [("SELL", "Wheat", 10)], [])
    assert ("SELL", "Wheat", 10) not in actions_future
    assert reserver.debt_records["Wheat"] == 0
