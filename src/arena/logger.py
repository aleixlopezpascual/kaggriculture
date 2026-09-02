"""Kaggriculture match state serialization and replay logging."""

import json
from pathlib import Path

from src.env.state import WorldState


class ReplayLogger:
    """Serializes match progression history in standard JSON formats."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.history = []

    def log_turn(self, state: WorldState, actions: dict) -> None:
        """Appends a serializable snapshot of the current state and actions."""
        snapshot = {
            "turn": state.turn,
            "weather": state.weather,
            "gold": state.farm.gold,
            "crops": [
                {
                    "type": c.crop_type,
                    "stage": c.growth_stage,
                    "moisture": c.moisture,
                    "x": c.x,
                    "y": c.y,
                }
                for c in state.crops
            ],
            "animals": [
                {
                    "type": a.animal_type,
                    "hunger": a.hunger,
                    "x": a.x,
                    "y": a.y,
                }
                for a in state.animals
            ],
            "workers": [
                {
                    "id": w.worker_id,
                    "x": w.x,
                    "y": w.y,
                    "carrying": w.carrying,
                }
                for w in state.farm.workers
            ],
            "actions": actions,
        }
        self.history.append(snapshot)

    def save_replay(self) -> None:
        """Writes the accumulated history array to disk."""
        with Path(self.output_path).open("w", encoding="utf-8") as f:
            json.dump({"replay": self.history}, f, indent=2)
