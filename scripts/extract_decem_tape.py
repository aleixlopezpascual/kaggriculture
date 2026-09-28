#!/usr/bin/env python3
"""Extract full 720-turn action tape from DECEM (World #2) replay."""

import json
from pathlib import Path


def extract_decem_tape(replay_path: Path | str, output_path: Path | str) -> list[dict]:
    replay_path = Path(replay_path).resolve()
    output_path = Path(output_path).resolve()

    with replay_path.open(encoding="utf-8") as fp:
        rep = json.load(fp)

    steps = rep["steps"]
    info = rep.get("info", {})
    teams = info.get("TeamNames", ["P0", "P1"])
    decem_seat = 1 if "DECEM" in teams[1] else 0

    tape = []
    for s in steps:
        act = s[decem_seat].get("action") or {
            "farmer": ["PASS"],
            "hands": [],
            "market": [],
        }
        # Deepcopy / clean order formats
        cleaned_act = {
            "farmer": list(act.get("farmer") or ["PASS"]),
            "hands": [list(h) for h in (act.get("hands") or [])],
            "market": [list(o) for o in (act.get("market") or [])],
        }
        tape.append(cleaned_act)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(tape, fp, indent=2)

    print(f"Extracted {len(tape)} steps from DECEM into {output_path}")
    return tape


if __name__ == "__main__":
    rep = Path("replays/episode-114621874-replay.json")
    out = Path(
        "docs/experiments/agent_selection/decem_evaluation/decem_tape_actions.json"
    )
    extract_decem_tape(rep, out)
