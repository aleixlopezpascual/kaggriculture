import json
from pathlib import Path

import kaggle_environments


def test_decem_tape_extraction_completeness():
    tape_path = Path(
        "docs/experiments/agent_selection/decem_evaluation/decem_tape_actions.json"
    )
    assert tape_path.is_file()

    with tape_path.open(encoding="utf-8") as fp:
        tape = json.load(fp)

    assert len(tape) == 720
    for s in tape:
        assert "farmer" in s
        assert "hands" in s
        assert "market" in s
        assert isinstance(s["farmer"], list)
        assert isinstance(s["hands"], list)
        assert isinstance(s["market"], list)


def test_decem_agent_full_game_simulation():
    decem_agent_path = str(
        Path(
            "docs/experiments/agent_selection/decem_evaluation/decem_tape_agent.py"
        ).resolve()
    )
    opp_path = str(Path("competitors/notebooks/shepherd_sovereign_main.py").resolve())

    env = kaggle_environments.make("kaggriculture", configuration={"seed": 848617604})
    steps = env.run([decem_agent_path, opp_path])

    assert len(steps) == 720
    p0, p1 = steps[-1][0], steps[-1][1]
    assert p0.status == "DONE"
    assert p1.status == "DONE"
    assert p0.reward is not None
    assert p0.reward > 0
