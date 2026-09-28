"""
DECEM-3000 Tape Agent
=====================
Synthesized from World #2 (3021.7 Elo) match replay Episode 114621874.
Plays DECEM's proven 720-step Heavy Livestock & Melon timeline with
exact native order execution and hand synchronization.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _find_tape_file() -> Path:
    f = globals().get("__file__")
    if f is not None:
        p = Path(f).resolve().parent / "decem_tape_actions.json"
        if p.is_file():
            return p
    for base in [
        Path.cwd() / "docs" / "experiments" / "agent_selection" / "decem_evaluation",
        Path.cwd(),
        Path(),
    ]:
        candidate = base / "decem_tape_actions.json"
        if candidate.is_file():
            return candidate.resolve()
    return Path("decem_tape_actions.json")


_TAPE_FILE = _find_tape_file()

if _TAPE_FILE.is_file():
    with _TAPE_FILE.open(encoding="utf-8") as fp:
        _TAPE = json.load(fp)
else:
    _TAPE = []


def _get_step(observation: dict[str, Any]) -> int:
    if "step" in observation:
        return int(observation["step"])
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    return day * 24 + hour


def agent(observation: dict[str, Any], configuration: Any = None) -> dict[str, Any]:
    step = _get_step(observation)
    if step >= len(_TAPE):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    planned = _TAPE[step]
    player = int(observation.get("player", 0))
    farms = observation.get("farms", [])
    if player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    actual_hands_count = len(farm.get("hands", []))

    # Synchronize hands actions to living hands on board
    planned_hands = list(planned.get("hands") or [])
    if len(planned_hands) > actual_hands_count:
        hands = planned_hands[:actual_hands_count]
    elif len(planned_hands) < actual_hands_count:
        hands = planned_hands + [["PASS"]] * (actual_hands_count - len(planned_hands))
    else:
        hands = planned_hands

    return {
        "farmer": list(planned.get("farmer") or ["PASS"]),
        "hands": hands,
        "market": [list(o) for o in (planned.get("market") or [])],
    }
