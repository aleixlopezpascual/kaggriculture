#!/usr/bin/env python3
"""DECEM World #2 (3021.7 Elo) Replay Playbook Analyzer.

Extracts the full 720-turn strategic timeline from the live match replay
between Aleix López (Seat 0) and DECEM (Seat 1) in Episode 114621874.
"""

import json
from collections import Counter
from pathlib import Path
from typing import Any


def analyze_decem_match(replay_path: Path | str) -> dict[str, Any]:
    replay_path = Path(replay_path).resolve()
    with replay_path.open(encoding="utf-8") as f:
        rep = json.load(f)

    steps = rep["steps"]
    info = rep.get("info", {})
    teams = info.get("TeamNames", ["P0", "P1"])
    decem_seat = 1 if "DECEM" in teams[1] else 0
    our_seat = 1 - decem_seat

    daily_summary = []
    milestones = {
        "quadrant_unlocks": [],
        "hiring_schedule": [],
        "animal_purchases": [],
        "seed_purchases": Counter(),
        "crop_plantings": Counter(),
        "total_sales_revenue": Counter(),
        "total_units_sold": Counter(),
        "endgame_triggers": {},
    }

    last_fed_step = -1
    last_water_step = -1
    last_plant_step = -1

    for step_num, step_data in enumerate(steps):
        day = step_num // 24
        hour = step_num % 24

        d_step = step_data[decem_seat]
        d_obs = d_step["observation"]
        d_farm = d_obs["farms"][decem_seat]
        d_private = d_obs.get("private", {})
        d_act = d_step.get("action") or {}

        # Track actions
        farmer_act = d_act.get("farmer") or []
        hands_act = d_act.get("hands") or []
        mkt_act = d_act.get("market") or []

        all_worker_cmds = [farmer_act] + hands_act
        for cmd in all_worker_cmds:
            if not cmd:
                continue
            op = cmd[0]
            if op == "FEED":
                last_fed_step = step_num
            elif op == "WATER":
                last_water_step = step_num
            elif op == "PLANT":
                last_plant_step = step_num
                crop = cmd[1] if len(cmd) > 1 else "UNKNOWN"
                milestones["crop_plantings"][crop] += 1

        # Track market actions
        for order in mkt_act:
            if not order:
                continue
            op = order[0]
            if op == "HIRE":
                milestones["hiring_schedule"].append((step_num, day, hour))
            elif op == "BUY_LAND":
                quads = len(d_farm.get("unlocked_quadrants", [0])) + 1
                milestones["quadrant_unlocks"].append((step_num, day, hour, quads))
            elif op == "BUY_ANIMAL":
                animal = order[1] if len(order) > 1 else ""
                qty = int(order[2]) if len(order) > 2 else 1
                milestones["animal_purchases"].append(
                    (step_num, day, hour, animal, qty)
                )
            elif op == "BUY_SEED":
                seed = order[1] if len(order) > 1 else ""
                qty = int(order[2]) if len(order) > 2 else 1
                milestones["seed_purchases"][seed] += qty
            elif op == "SELL":
                item = order[1] if len(order) > 1 else ""
                qty = int(order[2]) if len(order) > 2 else 1
                price = d_obs["market"]["prices"].get(item, 0)
                milestones["total_sales_revenue"][item] += qty * price
                milestones["total_units_sold"][item] += qty

        # Capture daily snapshot at dawn (hour 0)
        if hour == 0:
            tiles = d_farm["tiles"]
            animals = Counter()
            crops = Counter()
            for row in tiles:
                for tile in row:
                    if isinstance(tile, dict):
                        if tile.get("animal"):
                            animals[tile["animal"]] += 1
                        if tile.get("crop"):
                            crops[tile["crop"]] += 1

            our_farm = d_obs["farms"][our_seat]
            daily_summary.append(
                {
                    "day": day,
                    "step": step_num,
                    "decem_cash": d_farm["money"],
                    "our_cash": our_farm["money"],
                    "margin": our_farm["money"] - d_farm["money"],
                    "decem_hands": len(d_farm.get("hands", [])),
                    "decem_quads": len(d_farm.get("unlocked_quadrants", [0])),
                    "animals": dict(animals),
                    "crops": dict(crops),
                    "shed": {
                        k: v for k, v in d_private.get("shed", {}).items() if v > 0
                    },
                }
            )

    milestones["endgame_triggers"]["last_plant_step"] = last_plant_step
    milestones["endgame_triggers"]["last_water_step"] = last_water_step
    milestones["endgame_triggers"]["last_feed_step"] = last_fed_step

    final_0 = steps[-1][0]["reward"]
    final_1 = steps[-1][1]["reward"]

    return {
        "teams": teams,
        "decem_seat": decem_seat,
        "final_rewards": {
            teams[0]: final_0,
            teams[1]: final_1,
        },
        "daily_summary": daily_summary,
        "milestones": milestones,
    }


def format_markdown_playbook(analysis: dict[str, Any]) -> str:
    m = analysis["milestones"]
    teams = analysis["teams"]
    rewards = analysis["final_rewards"]
    margin = rewards[teams[1]] - rewards[teams[0]]

    md = [
        "# DECEM (World #2 · 3021.7 Elo) Playbook & Replay Deconstruction",
        "",
        "## Match Context",
        "- **Episode ID:** `114621874`",
        f"- **Player 0 (Seat 0):** `{teams[0]}` — "
        f"Final Gold: **${rewards[teams[0]]:,.0f}**",
        f"- **Player 1 (Seat 1):** `{teams[1]}` (World #2) — "
        f"Final Gold: **${rewards[teams[1]]:,.0f}**",
        f"- **Margin:** DECEM won by **+${margin:,.0f} gold**.",
        "",
        "---",
        "",
        "## 1. Executive Strategy Summary",
        "DECEM's strategy is an ultra-refined **Heavy Livestock + Melon Engine**:",
        "1. **Day 0 Dual-Species Kickstart:** On Turn 1 & 2, DECEM deploys "
        "**2 Cows + 3 Sheep + 5 Hands** immediately, buying 5 Wheat to feed them.",
        "2. **Dedicated Livestock Master:** The Farmer is never assigned to crops. "
        "The Farmer's sole lifetime job is **care, feeding, and fertilizer**.",
        "3. **Fertilizer Accelerated Melons:** Fertilizer collected on Turn 25 "
        "is placed on Melon fields, cutting growth time in half for early cash.",
        "4. **Fibonacci-Throttled Hiring:** DECEM caps hiring at **5 hands Day 0** "
        "and **3 hands Day 1**, avoiding the prohibitive $6,000+ wage spike.",
        "5. **Continuous Compounding:** Milk ($160) and Wool ($200) provide an "
        "unstoppable cash flow funding steady land expansion.",
        "",
        "---",
        "",
        "## 2. Key Strategic Milestones",
        "",
        "### Land Expansion Timeline",
    ]
    for step_num, day, hour, quads in m["quadrant_unlocks"]:
        md.append(
            f"- **Day {day:2d} (Step {step_num:3d}, Hour {hour:2d}):** "
            f"Unlocked **Quadrant {quads}**"
        )
    md.extend(["", "### Animal Acquisition Schedule"])
    for step_num, day, hour, animal, qty in m["animal_purchases"]:
        md.append(
            f"- **Day {day:2d} (Step {step_num:3d}, Hour {hour:2d}):** "
            f"Bought **{qty}x {animal}**"
        )
    md.extend(["", "### Total Lifetime Seed Purchases"])
    for seed, qty in m["seed_purchases"].most_common():
        md.append(f"- **{seed:12s}:** {qty:3d} seeds")

    md.extend(["", "### Total Production Sales & Revenue"])
    for item, rev in m["total_sales_revenue"].most_common():
        units = m["total_units_sold"][item]
        avg_price = rev / units if units else 0
        md.append(
            f"- **{item:12s}:** {units:4d} units sold → "
            f"**${rev:8,.0f}** (avg quote ${avg_price:.1f})"
        )

    last_p = m["endgame_triggers"]["last_plant_step"]
    last_w = m["endgame_triggers"]["last_water_step"]
    last_f = m["endgame_triggers"]["last_feed_step"]
    md.extend(
        [
            "",
            "### Endgame Liquidation Triggers",
            f"- **Last Crop Planted:** Step `{last_p}` (Day {last_p//24})",
            f"- **Last Crop Watered:** Step `{last_w}` (Day {last_w//24})",
            f"- **Last Livestock Fed:** Step `{last_f}` (Day {last_f//24})",
            "",
            "---",
            "",
            "## 3. Day-by-Day Progression Table",
            "",
            "| Day | Step | DECEM Cash | Our Cash | Margin | Hands | Quads | "
            "Animals on Board | Active Crops |",
            "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|",
        ]
    )
    for d in analysis["daily_summary"]:
        anim_str = (
            ", ".join(f"{k}:{v}" for k, v in d["animals"].items())
            if d["animals"]
            else "None"
        )
        crop_str = (
            ", ".join(f"{k}:{v}" for k, v in d["crops"].items())
            if d["crops"]
            else "None"
        )
        margin_str = f"{d['margin']:+,.0f}"
        md.append(
            f"| {d['day']:2d} | {d['step']:3d} | ${d['decem_cash']:8,.0f} | "
            f"${d['our_cash']:8,.0f} | {margin_str:>10s} | {d['decem_hands']:2d} | "
            f"{d['decem_quads']:1d} | {anim_str} | {crop_str} |"
        )
    md.append("")
    return "\n".join(md)


if __name__ == "__main__":
    rep_file = (
        Path(__file__).parent.parent / "replays" / "episode-114621874-replay.json"
    )
    results = analyze_decem_match(rep_file)
    playbook_md = format_markdown_playbook(results)
    out_file = Path(__file__).parent.parent / "docs" / "decem_world_2_playbook.md"
    out_file.write_text(playbook_md, encoding="utf-8")
    print(f"Successfully generated DECEM Playbook at: {out_file}")
