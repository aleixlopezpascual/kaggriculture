from submission.decoy import agent_entrypoint


def test_decoy_agent_returns_valid_pass_structure():
    mock_obs = {"turn": 0, "weather": "Sunny"}
    actions = agent_entrypoint(mock_obs)
    assert isinstance(actions, dict)
    assert actions["farmer"] == ["PASS"]
    assert actions["market"] == []
