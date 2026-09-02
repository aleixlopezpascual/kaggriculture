"""Kaggriculture local agent benchmarking arena."""

import random
from dataclasses import replace
from src.agents.base import BaseAgent
from src.env.state import FarmState, WorkerState, WorldState
from src.env.transitions import step_world


class LocalArena:
    """Evaluates agent performance under local simulation parameters."""

    def __init__(self, agent: BaseAgent, turns: int = 720):
        self.agent = agent
        self.turns = turns

    def create_initial_state(self, seed: int = 42) -> WorldState:
        """Generates a consistent deterministic initial state."""
        random.seed(seed)
        # Starting with $3000, 1 farmer worker at (0, 0)
        initial_worker = WorkerState(
            worker_id=1,
            x=0,
            y=0,
            carrying=None,
            is_busy=False,
        )
        initial_farm = FarmState(
            gold=3000,
            inventory={"Wheat": 0, "Strawberries": 0},
            workers=(initial_worker,),
            expansion_quadrants=1,
        )
        return WorldState(
            turn=0,
            weather="Sunny",
            grid_width=5,
            grid_height=5,
            crops=(),
            animals=(),
            farm=initial_farm,
            tilled_tiles=(),
        )

    def run_match(self, seed: int = 42) -> float:
        """Runs a complete local farming run and returns terminal gold."""
        state = self.create_initial_state(seed)

        for _ in range(self.turns):
            if state.turn >= self.turns:
                break
            # Query agent for actions based on the current state
            joint_actions = self.agent.act(state)

            # Apply pure environment transition step
            state = step_world(state, joint_actions)

            # Standard incremental turn ticking
            state = replace(state, turn=state.turn + 1)

        return state.farm.gold

    def benchmark(self, seeds: list[int]) -> dict[str, float]:
        """Runs the agent across multiple seeds and aggregates final balances."""
        results = []
        for seed in seeds:
            results.append(self.run_match(seed))

        return {
            "avg_gold": sum(results) / len(results),
            "max_gold": max(results),
            "min_gold": min(results),
            "runs": len(results),
        }
