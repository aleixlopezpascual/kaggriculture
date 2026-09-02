"""Kaggriculture pure, stateless transition functions."""

import random
from dataclasses import replace
from src.env.state import CropState, AnimalState, WorkerState, FarmState, WorldState


def step_crop(crop: CropState, watered: bool, weather: str) -> CropState:
    """Updates the state of a single crop based on watering and weather.

    Decay rules:
    - Sunny: -10 moisture
    - Rainy: +15 moisture
    - Overcast: -5 moisture

    Watering adds +30 moisture (capped at 100).
    Optimal moisture range is 20 to 90. If optimal, and either watered or
    rainy weather, growth stage advances.
    """
    # Calculate new moisture
    decay = 0
    if weather == "Sunny":
        decay = -10
    elif weather == "Rainy":
        decay = 15
    elif weather == "Overcast":
        decay = -5

    new_moisture = crop.moisture + decay
    if watered:
        new_moisture += 30

    new_moisture = max(0, min(100, new_moisture))

    # Growth stage progression
    new_growth = crop.growth_stage
    is_optimal = 20 <= new_moisture <= 90
    has_water_source = watered or weather == "Rainy" or crop.is_watered

    if is_optimal and has_water_source and crop.growth_stage < 3:
        new_growth += 1

    return CropState(
        crop_type=crop.crop_type,
        growth_stage=new_growth,
        moisture=new_moisture,
        is_watered=watered or (weather == "Rainy"),
        x=crop.x,
        y=crop.y,
    )


def get_fibonacci_number(n: int) -> int:
    """Returns the n-th Fibonacci number (1-indexed: 1, 1, 2, 3, 5, 8...)."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 1, 1
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def step_world(state: WorldState, joint_actions: dict) -> WorldState:
    """Executes tilling, planting, harvesting, watering, caring, and hiring actions.

    Joint actions format:
    {
        "worker_actions": {
            worker_id: ("TILE", x, y) | ("PLANT", x, y, crop_type) |
                       ("WATER", x, y) | ("HARVEST", x, y) |
                       ("FEED", x, y) | ("MOVE", direction)
        },
        "farm_actions": ["HIRE_WORKER", "BUY_EXPANSION"]
    }
    """
    # Update weather
    next_weather = random.choice(["Sunny", "Rainy", "Overcast"]) if state.turn % 5 == 0 else state.weather

    # Current state views
    tilled = set(state.tilled_tiles)
    crops_map = {(c.x, c.y): c for c in state.crops}
    animals_map = {(a.x, a.y): a for a in state.animals}
    workers_list = list(state.farm.workers)
    gold = state.farm.gold
    inventory = dict(state.farm.inventory)
    expansion = state.farm.expansion_quadrants

    worker_actions = joint_actions.get("worker_actions", {})
    farm_actions = joint_actions.get("farm_actions", [])

    # Process Farm-level actions
    for action in farm_actions:
        if action == "HIRE_WORKER":
            next_worker_idx = len(workers_list) + 1
            cost = 100 * get_fibonacci_number(next_worker_idx)
            if gold >= cost:
                gold -= cost
                new_worker = WorkerState(
                    worker_id=next_worker_idx,
                    x=0,
                    y=0,
                    carrying=None,
                    is_busy=False,
                )
                workers_list.append(new_worker)
        elif action == "BUY_EXPANSION":
            cost = 1000 * (2**expansion)
            if gold >= cost:
                gold -= cost
                expansion += 1

    # Process Worker-level actions and update coordinates/state
    updated_workers = []
    for w in workers_list:
        act = worker_actions.get(w.worker_id)
        if not act:
            updated_workers.append(w)
            continue

        act_type = act[0]

        if act_type == "MOVE":
            direction = act[1]
            nx, ny = w.x, w.y
            if direction == "UP" and w.y > 0:
                ny -= 1
            elif direction == "DOWN" and w.y < state.grid_height - 1:
                ny += 1
            elif direction == "LEFT" and w.x > 0:
                nx -= 1
            elif direction == "RIGHT" and w.x < state.grid_width - 1:
                nx += 1
            updated_workers.append(
                WorkerState(
                    worker_id=w.worker_id,
                    x=nx,
                    y=ny,
                    carrying=w.carrying,
                    is_busy=w.is_busy,
                )
            )

        elif act_type == "TILE":
            tx, ty = act[1], act[2]
            # Must be adjacent to worker to tile (Manhattan distance <= 1)
            if abs(w.x - tx) + abs(w.y - ty) <= 1:
                tilled.add((tx, ty))
            updated_workers.append(w)

        elif act_type == "PLANT":
            tx, ty, c_type = act[1], act[2], act[3]
            if abs(w.x - tx) + abs(w.y - ty) <= 1:
                if (tx, ty) in tilled and (tx, ty) not in crops_map:
                    # Remove from tilled, add to crops
                    tilled.discard((tx, ty))
                    crops_map[(tx, ty)] = CropState(
                        crop_type=c_type,
                        growth_stage=0,
                        moisture=50,
                        is_watered=False,
                        x=tx,
                        y=ty,
                    )
            updated_workers.append(w)

        elif act_type == "WATER":
            tx, ty = act[1], act[2]
            if abs(w.x - tx) + abs(w.y - ty) <= 1:
                if (tx, ty) in crops_map:
                    crops_map[(tx, ty)] = step_crop(
                        crops_map[(tx, ty)], watered=True, weather=state.weather
                    )
            updated_workers.append(w)

        elif act_type == "HARVEST":
            tx, ty = act[1], act[2]
            if abs(w.x - tx) + abs(w.y - ty) <= 1:
                if (tx, ty) in crops_map:
                    crop = crops_map[(tx, ty)]
                    if crop.growth_stage == 3:  # Harvestable
                        inventory[crop.crop_type] = (
                            inventory.get(crop.crop_type, 0) + 1
                        )
                        del crops_map[(tx, ty)]
                        tilled.add((tx, ty))  # Returns to tilled state
            updated_workers.append(w)

        elif act_type == "FEED":
            ax, ay = act[1], act[2]
            if abs(w.x - ax) + abs(w.y - ay) <= 1:
                if (ax, ay) in animals_map:
                    anim = animals_map[(ax, ay)]
                    animals_map[(ax, ay)] = AnimalState(
                        animal_type=anim.animal_type,
                        hunger=max(0, anim.hunger - 40),
                        is_fed=True,
                        x=anim.x,
                        y=anim.y,
                    )
            updated_workers.append(w)
        else:
            updated_workers.append(w)

    # Step crops that were not explicitly watered this turn
    for (cx, cy), crop in crops_map.items():
        # Check if this crop was watered via worker water actions
        watered_by_action = False
        for act in worker_actions.values():
            if act[0] == "WATER" and act[1] == cx and act[2] == cy:
                watered_by_action = True
                break
        if not watered_by_action:
            crops_map[(cx, cy)] = step_crop(crop, watered=False, weather=state.weather)

    # Step animal states (hunger increase)
    for (ax, ay), anim in animals_map.items():
        new_hunger = min(100, anim.hunger + 10)
        animals_map[(ax, ay)] = AnimalState(
            animal_type=anim.animal_type,
            hunger=new_hunger,
            is_fed=False,
            x=anim.x,
            y=anim.y,
        )

    return WorldState(
        turn=state.turn + 1,
        weather=next_weather,
        grid_width=state.grid_width,
        grid_height=state.grid_height,
        crops=tuple(crops_map.values()),
        animals=tuple(animals_map.values()),
        farm=FarmState(
            gold=gold,
            inventory=inventory,
            workers=tuple(updated_workers),
            expansion_quadrants=expansion,
        ),
        tilled_tiles=tuple(sorted(list(tilled))),
    )
