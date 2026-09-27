import json
import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

import scripts.validate_replay_parity as vrp
from scripts.validate_replay_parity import (
    ReplayAgent,
    compare_states,
    load_and_validate_replay,
    validate_replay,
)


def create_synthetic_replay(
    version="0.1.0",
    module_version="1.32.7",
    episode_steps=720,
    num_steps=720,
    turns_per_day=24,
    seed=12345,
    final_reward_0=100,
    final_reward_1=50,
    status="DONE",
) -> dict[str, Any]:
    steps = []
    # Step 0: Initial state
    steps.append(
        [
            {
                "action": {},
                "reward": 0,
                "status": "ACTIVE",
                "observation": {"day": 0, "hour": 0},
            },
            {
                "action": {},
                "reward": 0,
                "status": "ACTIVE",
                "observation": {"day": 0, "hour": 0},
            },
        ]
    )

    # Steps 1 to num_steps-1
    for i in range(1, num_steps):
        day = (i - 1) // turns_per_day
        hour = (i - 1) % turns_per_day
        steps.append(
            [
                {
                    "action": {"farmer": "buy", "hands": i, "market": {}},
                    "reward": 0,
                    "status": "ACTIVE",
                    "observation": {"day": day, "hour": hour},
                },
                {
                    "action": {"farmer": "sell", "hands": i, "market": {}},
                    "reward": 0,
                    "status": "ACTIVE",
                    "observation": {"day": day, "hour": hour},
                },
            ]
        )

    # Terminal step statuses
    if num_steps > 0:
        steps[-1][0]["status"] = status
        steps[-1][1]["status"] = status
        steps[-1][0]["reward"] = final_reward_0
        steps[-1][1]["reward"] = final_reward_1

    return {
        "version": version,
        "module_version": module_version,
        "info": {
            "EpisodeId": 123,
            "TeamNames": ["Team A", "Team B"],
            "seed": seed,
        },
        "configuration": {
            "episodeSteps": episode_steps,
            "turnsPerDay": turns_per_day,
            "seed": None,
        },
        "steps": steps,
        "rewards": [final_reward_0, final_reward_1],
        "statuses": [status, status],
        "name": "kaggriculture",
    }


def test_synthetic_replay_generation():
    replay = create_synthetic_replay(num_steps=5, episode_steps=5)
    assert len(replay["steps"]) == 5
    assert replay["steps"][1][0]["action"]["hands"] == 1
    assert replay["steps"][4][0]["status"] == "DONE"
    assert replay["rewards"] == [100, 50]


def test_replay_agent_extraction():
    replay = create_synthetic_replay(num_steps=5, episode_steps=5)
    agent0 = ReplayAgent(0, replay["steps"], 24)
    agent1 = ReplayAgent(1, replay["steps"], 24)

    # Turn 0
    obs = {"day": 0, "hour": 0}
    act0 = agent0(obs, {})
    act1 = agent1(obs, {})
    assert act0 == {"farmer": "buy", "hands": 1, "market": {}}
    assert act1 == {"farmer": "sell", "hands": 1, "market": {}}
    assert agent0.call_count == 1

    # Turn 1
    obs = {"day": 0, "hour": 1}
    act0 = agent0(obs, {})
    assert act0 == {"farmer": "buy", "hands": 2, "market": {}}


def test_replay_agent_misalignment():
    replay = create_synthetic_replay(num_steps=5, episode_steps=5)
    agent0 = ReplayAgent(0, replay["steps"], 24)

    # Send wrong day/hour (skip to hour 1 instead of 0)
    obs = {"day": 0, "hour": 1}
    with pytest.raises(ValueError, match="Misalignment"):
        agent0(obs, {})


def test_replay_agent_missing_clock():
    replay = create_synthetic_replay(num_steps=5, episode_steps=5)
    agent0 = ReplayAgent(0, replay["steps"], 24)

    # Missing hour and day
    obs = {"step": 0}
    with pytest.raises(ValueError, match="Missing clock fields"):
        agent0(obs, {})


def test_module_version_vs_schema_version(tmp_path):
    # Should fail if module_version doesn't match
    replay = create_synthetic_replay(
        module_version="1.32.6",
        version="1.32.7",
        num_steps=5,
        episode_steps=5,
    )
    replay_path = tmp_path / "replay.json"
    with replay_path.open("w") as f:
        json.dump(replay, f)

    with pytest.raises(ValueError, match="differs from required 1.32.7"):
        load_and_validate_replay(replay_path)

    # Should pass if module_version is 1.32.7, even if version is 0.1.0
    replay2 = create_synthetic_replay(
        module_version="1.32.7",
        version="0.1.0",
        num_steps=5,
        episode_steps=5,
    )
    with replay_path.open("w") as f:
        json.dump(replay2, f)
    metadata = load_and_validate_replay(replay_path)
    assert metadata["engine_version"] == "1.32.7"


def test_invalid_step_count(tmp_path):
    replay = create_synthetic_replay(num_steps=4, episode_steps=5)
    replay_path = tmp_path / "replay.json"
    with replay_path.open("w") as f:
        json.dump(replay, f)

    with pytest.raises(
        ValueError,
        match=r"len\(steps\).* != configuration\.episodeSteps",
    ):
        load_and_validate_replay(replay_path)


def test_missing_seed(tmp_path):
    replay = create_synthetic_replay(num_steps=5, episode_steps=5, seed=None)
    replay_path = tmp_path / "replay.json"
    with replay_path.open("w") as f:
        json.dump(replay, f)

    with pytest.raises(ValueError, match="non-null integer info.seed"):
        load_and_validate_replay(replay_path)


def test_invalid_seats(tmp_path):
    replay = create_synthetic_replay(num_steps=5, episode_steps=5)
    # Remove one seat from a step
    replay["steps"][1] = [replay["steps"][1][0]]
    replay_path = tmp_path / "replay.json"
    with replay_path.open("w") as f:
        json.dump(replay, f)

    with pytest.raises(ValueError, match="two seats"):
        load_and_validate_replay(replay_path)


def test_invalid_action_dict(tmp_path):
    replay = create_synthetic_replay(num_steps=5, episode_steps=5)
    # Change action to a list instead of dict
    replay["steps"][1][0]["action"] = []
    replay_path = tmp_path / "replay.json"
    with replay_path.open("w") as f:
        json.dump(replay, f)

    with pytest.raises(ValueError, match="valid action dictionary"):
        load_and_validate_replay(replay_path)


def test_statuses_not_done(tmp_path):
    replay = create_synthetic_replay(num_steps=5, episode_steps=5, status="ERROR")
    replay_path = tmp_path / "replay.json"
    with replay_path.open("w") as f:
        json.dump(replay, f)

    with pytest.raises(ValueError, match="both recorded statuses to be DONE"):
        load_and_validate_replay(replay_path)


def test_comparator_exact_mismatch():
    # True exact match
    local_state = [
        {"reward": 100, "status": "DONE"},
        {"reward": 50, "status": "DONE"},
    ]
    assert compare_states(local_state, [100, 50], ["DONE", "DONE"])

    # Mismatch on reward
    assert not compare_states(local_state, [100, 51], ["DONE", "DONE"])

    # Mismatch on status
    assert not compare_states(local_state, [100, 50], ["DONE", "ERROR"])


def test_cli_exit_nonzero_on_failure(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["validate_replay_parity.py", "--replay", "nonexistent_file.json"],
    )
    with pytest.raises(SystemExit) as exc_info:
        from scripts.validate_replay_parity import main

        main()
    assert exc_info.value.code == 1


def test_validate_replay_uses_monotonic_perf_counter(tmp_path, monkeypatch):
    """Verify validate_replay uses monotonic clock and forbids wall-clock timing."""
    replay_data = create_synthetic_replay(num_steps=2, episode_steps=2)
    replay_path = tmp_path / "replay_timing.json"
    with replay_path.open("w", encoding="utf-8") as f:
        json.dump(replay_data, f)

    mock_time = MagicMock(wraps=vrp.time)
    mock_time.time.side_effect = AssertionError(
        "Forbidden wall-clock time.time() called; "
        "monotonic time.perf_counter() required"
    )
    mock_time.perf_counter.side_effect = [100.0, 104.25]
    monkeypatch.setattr(vrp, "time", mock_time)

    mock_env = MagicMock()
    mock_env.steps = [
        [{}, {}],
        [
            {"reward": 100, "status": "DONE"},
            {"reward": 50, "status": "DONE"},
        ],
    ]

    def fake_run(agents):
        obs = {"day": 0, "hour": 0}
        agents[0](obs, {})
        agents[1](obs, {})

    mock_env.run.side_effect = fake_run
    monkeypatch.setattr(
        vrp.kaggle_environments,
        "make",
        lambda *args, **kwargs: mock_env,
    )

    result = validate_replay(replay_path)

    mock_time.time.assert_not_called()
    assert mock_time.perf_counter.call_count == 2
    assert result["runtime_seconds"] == pytest.approx(4.25)
    assert result["exact_parity"] is True
