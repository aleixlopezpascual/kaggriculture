"""Kaggriculture match state serialization and replay logging."""

import json
from pathlib import Path

from src.env.state import WorldState


class ReplayLogger:
    """Serializes match progression history in Krobus JSON formats."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.steps = []

    def _state_to_kaggle_dict(self, state: WorldState) -> dict:
        """Serializes WorldState into the raw Kaggle JSON format expected by Krobus."""
        tiles = [None] * 100
        for x, y in state.tilled_tiles:
            tiles[y * state.grid_width + x] = {"kind": "TILLED"}

        for c in state.crops:
            tiles[c.y * state.grid_width + c.x] = {
                "kind": "PLANT",
                "crop": c.crop_type.upper(),
                "planted_day": 0,
                "watered_today": c.is_watered,
                "consecutive_unwatered": 0,
                "yield_units": 1,
            }

        for a in state.animals:
            tiles[a.y * state.grid_width + a.x] = {
                "kind": "ANIMAL",
                "animal": a.animal_type.upper(),
                "hunger": a.hunger,
                "consecutive_unfed": 0,
            }

        farmer_bag = []
        if state.farm.workers and state.farm.workers[0].carrying:
            farmer_bag.append(state.farm.workers[0].carrying.upper())

        worker_ids = [w.worker_id for w in state.farm.workers]

        return {
            "player": 0,
            "day": state.turn // 24,
            "hour": state.turn % 24,
            "farms": [
                {
                    "money": state.farm.gold,
                    "farmer": worker_ids,
                    "tiles": tiles,
                },
                {"money": 1000, "farmer": [], "tiles": []},  # Dummy opponent
            ],
            "market": {
                "inventories": {},
                "prices": {},
            },
            "private": {
                "shed": state.farm.inventory,
                "seeds": {},
                "inventories": [farmer_bag] + [[] for _ in range(len(worker_ids) - 1)],
            },
        }

    def log_turn(self, state: WorldState, actions: dict) -> None:
        """Appends a Krobus-compatible step containing observation and action."""
        step_data = {
            "observation": self._state_to_kaggle_dict(state),
            "action": actions,
        }
        self.steps.append(step_data)

    def save_replay(self) -> None:
        """Writes the accumulated steps array to disk in Krobus format."""
        path = Path(self.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump({"steps": self.steps}, f, separators=(",", ":"))
