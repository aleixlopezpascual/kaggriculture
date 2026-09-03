"""Kaggriculture high-fidelity local agent benchmarking arena."""

import json
from pathlib import Path

from kaggle_environments import make

from src.agents.base import BaseAgent
from src.env.parser import parse_world_state


class LocalArena:
    """Evaluates agent performance with 100% Kaggle parity."""

    def __init__(self, agent: BaseAgent, turns: int = 720):
        self.agent = agent
        self.turns = turns

    def _wrap_agent(self, custom_agent: BaseAgent):
        """Wraps our custom BaseAgent into a Kaggle callable agent."""

        def kaggle_agent_fn(obs, config):
            try:
                # 1. Parse official Kaggle observation dict into immutable WorldState
                state = parse_world_state(obs)
                # 2. Get actions from our custom strategic planner
                joint_actions = custom_agent.act(state)
                # 3. Map actions to official schema
                farmer_action = joint_actions.get("worker_actions", {}).get(1, ["PASS"])

                hands_actions = []
                for worker_id, act in sorted(
                    joint_actions.get("worker_actions", {}).items()
                ):
                    if worker_id > 1:
                        hands_actions.append(act)

                market_actions = joint_actions.get("farm_actions", [])

                return {
                    "farmer": list(farmer_action),
                    "hands": [list(h) for h in hands_actions],
                    "market": [
                        list(m) if isinstance(m, (list, tuple)) else [m]
                        for m in market_actions
                    ],
                }
            except Exception:
                # Safe fallback to prevent crash penalty
                return {"farmer": ["PASS"], "hands": [], "market": []}

        return kaggle_agent_fn

    def run_match(self, seed: int = 42, replay_file: str | None = None) -> float:
        """Runs a complete official farming simulation match."""
        # Setup agents
        if callable(self.agent):
            player_agent = self.agent
        else:
            player_agent = self._wrap_agent(self.agent)

        def dummy_opponent(obs, config):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        # Initialize official environments engine
        env = make(
            "kaggriculture", configuration={"episodeSteps": self.turns, "seed": seed}
        )

        # Execute entire 720-step match head-to-head
        env.run([player_agent, dummy_opponent])

        if replay_file:
            path = Path(replay_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(env.render(mode="json"), f)

        # Retrieve player 0's final accumulated gold (reward)
        return float(env.state[0].reward)

    def benchmark(
        self, seeds: list[int], save_replays: bool = False
    ) -> dict[str, float | int]:
        """Runs the agent across multiple seeds and aggregates final balances."""
        results = []
        for seed in seeds:
            replay_path = f"replays/krobus_seed_{seed}.json" if save_replays else None
            results.append(self.run_match(seed, replay_file=replay_path))

        return {
            "avg_gold": sum(results) / len(results),
            "max_gold": max(results),
            "min_gold": min(results),
            "runs": len(results),
        }
