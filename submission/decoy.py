"""Kaggriculture minimal decoy agent.
Returns PASS actions to overwrite active matchmaking slots.
"""


def agent_entrypoint(obs_json: dict) -> dict:
    # Always returns standard PASS actions to avoid executing active strategies
    return {"farmer": ["PASS"], "market": []}
