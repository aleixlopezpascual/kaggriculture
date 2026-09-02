from kaggle_environments import make

from src.env.parser import parse_world_state
from src.env.transitions import step_world


def test_kaggle_environments_parity_smoke():
    """Verify that we can parse the official initial state successfully."""
    env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 42})
    env.reset()

    obs = env.state[0].observation
    # Parse the official Kaggle state into our custom immutable WorldState
    state = parse_world_state(obs)

    # Basic validations
    assert state.turn == 0
    assert state.farm.gold == 3000
    assert len(state.farm.workers) == 1
    assert state.farm.workers[0].x == 4
    assert state.farm.workers[0].y == 4
    assert state.farm.workers[0].carrying == ()

    # Issue a simple local transition (e.g. MOVE TILE at 4,3)
    actions = {
        "worker_actions": {1: ("TILE", 4, 3)},
        "farm_actions": [],
    }
    next_state = step_world(state, actions)
    assert (4, 3) in next_state.tilled_tiles
