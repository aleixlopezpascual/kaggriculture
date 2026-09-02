"""Kaggriculture greedy heuristic-based rule agent with strategic target support."""

from src.agents.base import BaseAgent
from src.env.state import StrategicTarget, WorldState
from src.utils.routing import find_shortest_path, manhattan_distance


class HeuristicAgent(BaseAgent):
    """Greedy rule-based agent prioritizing critical farm duties."""

    def __init__(self, crop_to_plant: str = "Strawberries"):
        self.crop_to_plant = crop_to_plant

    def act(self, state: WorldState, target: StrategicTarget | None = None) -> dict:
        """Determines prioritized actions driven by a strategic target."""
        # 1. Fallback / default target if none is supplied
        if target is None:
            target = StrategicTarget(
                target_workers=3,
                target_cows=0,
                target_sheep=0,
                target_geese=0,
                crop_priorities={self.crop_to_plant: 10},
                budget_reserved_for_seeds=100.0,
                is_liquidating=False,
            )

        worker_actions = {}
        farm_actions = []

        # Current livestock counts
        cows = sum(1 for a in state.animals if a.animal_type == "Cow")
        sheep = sum(1 for a in state.animals if a.animal_type == "Sheep")
        geese = sum(1 for a in state.animals if a.animal_type == "Goose")

        # Current crop counts
        active_crop_counts = {}
        for c in state.crops:
            active_crop_counts[c.crop_type] = active_crop_counts.get(c.crop_type, 0) + 1

        # 2. Macro Farm Actions (Hiring, Purchases)
        gold_available = state.farm.gold

        # Scale Labor
        if (
            len(state.farm.workers) < target.target_workers
            and gold_available >= 500 + target.budget_reserved_for_seeds
        ):
            farm_actions.append("HIRE_WORKER")
            gold_available -= 500

        # Purchase Cows (Cost $500)
        if (
            cows < target.target_cows
            and gold_available >= 500 + target.budget_reserved_for_seeds
        ):
            farm_actions.append(("BUY_ANIMAL", "Cow"))
            gold_available -= 500
            cows += 1

        # Purchase Sheep (Cost $300)
        if (
            sheep < target.target_sheep
            and gold_available >= 300 + target.budget_reserved_for_seeds
        ):
            farm_actions.append(("BUY_ANIMAL", "Sheep"))
            gold_available -= 300
            sheep += 1

        # Purchase Geese (Cost $150)
        if (
            geese < target.target_geese
            and gold_available >= 150 + target.budget_reserved_for_seeds
        ):
            farm_actions.append(("BUY_ANIMAL", "Goose"))
            gold_available -= 150
            geese += 1

        # Compile sell actions for gathered inventory (Market front-running)
        sell_orders = []
        for item, qty in state.farm.inventory.items():
            if qty > 0:
                sell_orders.append(("SELL", item, qty))

        # Sort sell orders so premium goods are processed first (milk, wool, etc.)
        premium_goods = {"Milk", "Wool", "Strawberries", "Melons", "Eggs"}
        sell_orders.sort(key=lambda o: 0 if o[1] in premium_goods else 1)
        farm_actions.extend(sell_orders)

        # 3. Dynamic Task Allocation for Workers
        # Emergency tasks
        harvestable_crops = [c for c in state.crops if c.growth_stage == 3]
        hungry_animals = [a for a in state.animals if a.hunger >= 50]
        thirsty_crops = [c for c in state.crops if c.moisture <= 30]
        empty_tilled_tiles = list(state.tilled_tiles)

        # Filter out tilled tiles that already have crops
        crop_coords = {(c.x, c.y) for c in state.crops}
        empty_tilled_tiles = [
            tile for tile in empty_tilled_tiles if tile not in crop_coords
        ]

        seed_prices = {"Wheat": 5, "Carrot": 10, "Melons": 25, "Strawberries": 40}

        # Buy seeds for crop deficits
        if not target.is_liquidating:
            for crop_type, target_count in target.crop_priorities.items():
                current_planted = active_crop_counts.get(crop_type, 0)
                current_seeds = state.farm.seed_inventory.get(crop_type, 0)
                deficit = target_count - current_planted - current_seeds
                if deficit > 0:
                    cost = seed_prices.get(crop_type, 10) * deficit
                    if gold_available >= cost:
                        farm_actions.append(("BUY_SEED", crop_type, deficit))
                        gold_available -= cost
                    elif gold_available >= seed_prices.get(crop_type, 10):
                        affordable = gold_available // seed_prices.get(crop_type, 10)
                        farm_actions.append(("BUY_SEED", crop_type, affordable))
                        gold_available -= affordable * seed_prices.get(crop_type, 10)

        # Determine best crop to plant based on targets and available seeds
        best_crop_to_plant = self.crop_to_plant
        max_deficit = 0
        for crop_type, target_count in target.crop_priorities.items():
            # Only consider crops we actually have seeds for (including newly bought)
            current_planted = active_crop_counts.get(crop_type, 0)
            deficit = target_count - current_planted
            if deficit > max_deficit:
                max_deficit = deficit
                best_crop_to_plant = crop_type

        assigned_tasks = set()

        for worker in state.farm.workers:
            # 1. HARVEST (Prioritized first)
            best_harvest = None
            best_dist = float("inf")
            for c in harvestable_crops:
                if (c.x, c.y) in assigned_tasks:
                    continue
                dist = manhattan_distance(worker.x, worker.y, c.x, c.y)
                if dist < best_dist:
                    best_dist = dist
                    best_harvest = c

            if best_harvest:
                if best_dist <= 1:
                    worker_actions[worker.worker_id] = (
                        "HARVEST",
                        best_harvest.x,
                        best_harvest.y,
                    )
                else:
                    path = find_shortest_path(
                        worker.x, worker.y, best_harvest.x, best_harvest.y
                    )
                    if path:
                        worker_actions[worker.worker_id] = path[0]
                assigned_tasks.add((best_harvest.x, best_harvest.y))
                continue

            # 2. FEED ANIMALS
            best_animal = None
            best_dist = float("inf")
            for a in hungry_animals:
                if (a.x, a.y) in assigned_tasks:
                    continue
                dist = manhattan_distance(worker.x, worker.y, a.x, a.y)
                if dist < best_dist:
                    best_dist = dist
                    best_animal = a

            if best_animal:
                if best_dist <= 1:
                    worker_actions[worker.worker_id] = (
                        "FEED",
                        best_animal.x,
                        best_animal.y,
                    )
                else:
                    path = find_shortest_path(
                        worker.x, worker.y, best_animal.x, best_animal.y
                    )
                    if path:
                        worker_actions[worker.worker_id] = path[0]
                assigned_tasks.add((best_animal.x, best_animal.y))
                continue

            # 3. WATER CROPS
            best_thirsty = None
            best_dist = float("inf")
            for c in thirsty_crops:
                if (c.x, c.y) in assigned_tasks:
                    continue
                dist = manhattan_distance(worker.x, worker.y, c.x, c.y)
                if dist < best_dist:
                    best_dist = dist
                    best_thirsty = c

            if best_thirsty:
                if best_dist <= 1:
                    worker_actions[worker.worker_id] = (
                        "WATER",
                        best_thirsty.x,
                        best_thirsty.y,
                    )
                else:
                    path = find_shortest_path(
                        worker.x, worker.y, best_thirsty.x, best_thirsty.y
                    )
                    if path:
                        worker_actions[worker.worker_id] = path[0]
                assigned_tasks.add((best_thirsty.x, best_thirsty.y))
                continue

            # 4. PLANT ON EMPTY TILLED TILES (driven by target deficits)
            best_tile = None
            best_dist = float("inf")
            for tile in empty_tilled_tiles:
                if tile in assigned_tasks:
                    continue
                dist = manhattan_distance(worker.x, worker.y, tile[0], tile[1])
                if dist < best_dist:
                    best_dist = dist
                    best_tile = tile

            if best_tile and not target.is_liquidating:
                tx, ty = best_tile
                if best_dist <= 1:
                    worker_actions[worker.worker_id] = (
                        "PLANT",
                        tx,
                        ty,
                        best_crop_to_plant,
                    )
                else:
                    path = find_shortest_path(worker.x, worker.y, tx, ty)
                    if path:
                        worker_actions[worker.worker_id] = path[0]
                assigned_tasks.add((tx, ty))
                continue

            # 5. DEFAULT TILL/MOVE IDLE (till nearest untilled tile to expand)
            target_x = (worker.x + 1) % state.grid_width
            target_y = worker.y
            if (
                target_x,
                target_y,
            ) not in state.tilled_tiles and not target.is_liquidating:
                if abs(worker.x - target_x) <= 1:
                    worker_actions[worker.worker_id] = ("TILE", target_x, target_y)
                else:
                    path = find_shortest_path(worker.x, worker.y, target_x, target_y)
                    if path:
                        worker_actions[worker.worker_id] = path[0]
            else:
                worker_actions[worker.worker_id] = ("MOVE", "RIGHT")

        return {"worker_actions": worker_actions, "farm_actions": farm_actions}
