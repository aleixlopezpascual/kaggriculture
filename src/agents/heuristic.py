"""Kaggriculture greedy heuristic-based rule agent."""

from src.agents.base import BaseAgent
from src.env.state import WorldState
from src.utils.routing import find_shortest_path, manhattan_distance


class HeuristicAgent(BaseAgent):
    """Greedy rule-based agent prioritizing critical farm duties."""

    def __init__(self, crop_to_plant: str = "Strawberries"):
        self.crop_to_plant = crop_to_plant

    def act(self, state: WorldState) -> dict:
        """Determines prioritized actions for each worker."""
        worker_actions = {}
        farm_actions = []

        # Find critical tasks on the grid
        harvestable_crops = [c for c in state.crops if c.growth_stage == 3]
        hungry_animals = [a for a in state.animals if a.hunger >= 50]
        thirsty_crops = [c for c in state.crops if c.moisture <= 30]
        empty_tilled_tiles = list(state.tilled_tiles)

        # Filter out tilled tiles that already have crops
        crop_coords = {(c.x, c.y) for c in state.crops}
        empty_tilled_tiles = [
            tile for tile in empty_tilled_tiles if tile not in crop_coords
        ]

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

            # 4. PLANT ON EMPTY TILLED TILES
            best_tile = None
            best_dist = float("inf")
            for tile in empty_tilled_tiles:
                if tile in assigned_tasks:
                    continue
                dist = manhattan_distance(worker.x, worker.y, tile[0], tile[1])
                if dist < best_dist:
                    best_dist = dist
                    best_tile = tile

            if best_tile:
                tx, ty = best_tile
                if best_dist <= 1:
                    worker_actions[worker.worker_id] = (
                        "PLANT",
                        tx,
                        ty,
                        self.crop_to_plant,
                    )
                else:
                    path = find_shortest_path(worker.x, worker.y, tx, ty)
                    if path:
                        worker_actions[worker.worker_id] = path[0]
                assigned_tasks.add((tx, ty))
                continue

            # 5. DEFAULT TILL/MOVE IDLE
            # If nothing else, till nearest untilled tile or move randomly
            target_x = (worker.x + 1) % state.grid_width
            target_y = worker.y
            if (target_x, target_y) not in state.tilled_tiles:
                if abs(worker.x - target_x) <= 1:
                    worker_actions[worker.worker_id] = ("TILE", target_x, target_y)
                else:
                    path = find_shortest_path(worker.x, worker.y, target_x, target_y)
                    if path:
                        worker_actions[worker.worker_id] = path[0]
            else:
                worker_actions[worker.worker_id] = ("MOVE", "RIGHT")

        # Farm action: Hire worker if we can afford and have few workers
        if len(state.farm.workers) < 3 and state.farm.gold >= 500:
            farm_actions.append("HIRE_WORKER")

        return {"worker_actions": worker_actions, "farm_actions": farm_actions}
