from pathlib import Path

import kaggle_environments

from src.agents.p3_metered_challenger import agent


def test_p3_metered_challenger_execution_step():
    obs = {
        "step": 360,
        "player": 0,
        "farms": [
            {
                "money": 10000.0,
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
                "tiles": [[None] * 10 for _ in range(10)],
                "farmer": [4, 4],
            },
            {
                "money": 10000.0,
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
                "tiles": [[None] * 10 for _ in range(10)],
                "farmer": [4, 4],
            },
        ],
        "private": {"shed": {"STRAWBERRY": 25, "WHEAT": 5}},
        "market": {
            "inventory": {},
            "prices": {"STRAWBERRY": 110, "WHEAT": 25},
        },
        "town": {"unlocked_shops": ["ICE_CREAM_SHOP"]},
    }
    act = agent(obs)
    assert "market" in act
    # Strawberry sell orders must not exceed effective cap (6)
    for o in act["market"]:
        if len(o) >= 3 and o[0] == "SELL" and o[1] == "STRAWBERRY":
            assert int(o[2]) <= 6


def test_p3_metered_challenger_full_game_simulation():
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 848617604})
    p3_path = str(Path("src/agents/p3_metered_challenger.py").resolve())
    shep_path = "competitors/notebooks/shepherd_sovereign_main.py"
    steps = env.run([p3_path, shep_path])
    assert len(steps) == 720
    assert steps[-1][0]["status"] == "DONE"
    assert steps[-1][0]["reward"] > 50000
