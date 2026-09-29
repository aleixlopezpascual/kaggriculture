"""Diagnostic Match Player for EscalationAgent."""

import sys
from pathlib import Path

from kaggle_environments import make

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.arena.run_tournament import get_agent_callable
from src.env.parser import parse_world_state


def run_diagnostic():
    agent_fn = get_agent_callable("Heuristic v2 (Escalation)")

    def dummy_opponent(obs, config):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.reset()

    print("Starting Diagnostic Match Execution...")

    # Run the environment turn-by-turn to inspect
    for step in range(720):
        # Retrieve observations before agent acts
        obs = env.state[0].observation
        state = parse_world_state(obs)

        # Call agent
        actions = agent_fn(obs, env.configuration)

        # Log specific milestones
        if step in [0, 1, 2, 3, 10, 24, 48, 100, 200, 300, 500, 600, 715]:
            print(f"\n--- TURN {step} ---")
            print(f"Gold: {state.farm.gold}")
            print(
                f"Workers: {len(state.farm.workers)} | "
                f"Positions: {[(w.x, w.y) for w in state.farm.workers]}"
            )
            print(f"Worker Carrying: {[ w.carrying for w in state.farm.workers ]}")
            print(f"Shed Inventory: {state.farm.inventory}")
            print(f"Seed Inventory: {state.farm.seed_inventory}")
            print(
                f"Crops Planted: {len(state.crops)} | "
                f"Types: {[c.crop_type for c in state.crops[:5]]}..."
            )
            print(f"Agent Actions returned to Kaggle: {actions}")

        # Run step in environment
        env.step([actions, dummy_opponent(env.state[1].observation, env.configuration)])

    print("\n--- FINAL TURN 720 ---")
    final_gold = env.state[0].reward
    print(f"Final Gold: {final_gold}")


if __name__ == "__main__":
    run_diagnostic()
