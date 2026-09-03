"""Kaggriculture Dynamic Escalation Agent."""

from src.agents.heuristic import HeuristicAgent
from src.env.state import StrategicTarget, WorldState
from src.utils.routing import find_shortest_path, manhattan_distance


class EscalationAgent(HeuristicAgent):
    """Dynamic Escalation Agent with Target Persistence and Seed Inventory guards.

    Caps labor count at 3 highly-efficient workers, dynamically scales crop volume based on gold,
    and uses persisted targeting to ensure workers committed to tasks do not thrash. Uses strict
    seed inventory checks to prevent infinite planting loops when seeds are out.
    """

    def __init__(self, crop_to_plant: str = "Strawberry"):
        super().__init__(crop_to_plant=crop_to_plant)
        # Map worker_id -> (tx, ty, task_type)
        self.worker_targets = {}

    def act(self, state: WorldState, target: StrategicTarget | None = None) -> dict:
        # 1. Determine dynamic Strategic Target based on active gold
        if target is None:
            gold = state.farm.gold
            t_workers = 3

            if gold < 3000:
                crop_count = 10
                budget_seeds = 100.0
            elif gold < 6000:
                crop_count = 14
                budget_seeds = 200.0
            elif gold < 10000:
                crop_count = 18
                budget_seeds = 300.0
            else:
                crop_count = 22
                budget_seeds = 400.0

            # End-game liquidation: stop buying seeds after Turn 660 to ensure cashout before Turn 720
            is_liq = state.turn >= 660
            if is_liq:
                crop_count = 0
                budget_seeds = 0.0

            target = StrategicTarget(
                target_workers=t_workers,
                target_cows=0,
                target_sheep=0,
                target_geese=0,
                crop_priorities={self.crop_to_plant: crop_count},
                budget_reserved_for_seeds=budget_seeds,
                is_liquidating=is_liq,
            )

        # 2. Extract state variables
        gold_available = state.farm.gold
        active_crop_counts = {}
        for c in state.crops:
            active_crop_counts[c.crop_type] = active_crop_counts.get(c.crop_type, 0) + 1

        # 3. Macro Farm Actions (Hiring, Purchases)
        farm_actions = []

        # HIRE
        if (
            len(state.farm.workers) < target.target_workers
            and gold_available >= 500 + target.budget_reserved_for_seeds
        ):
            farm_actions.append("HIRE_WORKER")
            gold_available -= 500

        # Buy seeds for crop deficits
        if not target.is_liquidating and state.turn < 710:
            for crop_type, target_count in target.crop_priorities.items():
                current_planted = active_crop_counts.get(crop_type, 0)
                current_seeds = state.farm.seed_inventory.get(crop_type, 0)
                deficit = target_count - current_planted - current_seeds
                if deficit > 0:
                    seed_prices = {"Wheat": 10, "Carrot": 20, "Tomato": 50, "Strawberry": 100, "Melon": 80}
                    cost = seed_prices.get(crop_type, 10) * deficit
                    if gold_available >= cost:
                        farm_actions.append(("BUY_SEED", crop_type, deficit))
                        gold_available -= cost

        # SELL
        sell_orders = []
        for item, qty in state.farm.inventory.items():
            if qty > 0:
                sell_orders.append(("SELL", item, qty))
        from src.utils.market import rank_sell_orders
        sell_orders = rank_sell_orders(sell_orders)
        farm_actions.extend(sell_orders)

        # 4. Stabilized Task Allocation for Workers
        harvestable_crops = [c for c in state.crops if c.growth_stage == 3]
        thirsty_crops = [c for c in state.crops if c.moisture <= 30 or not c.is_watered]
        empty_tilled_tiles = list(state.tilled_tiles)
        crop_coords = {(c.x, c.y) for c in state.crops}
        empty_tilled_tiles = [
            tile for tile in empty_tilled_tiles if tile not in crop_coords
        ]

        assigned_tasks = set()
        worker_actions = {}

        # First pass: validate and execute persisted targets
        for worker in state.farm.workers:
            wid = worker.worker_id
            if wid in self.worker_targets:
                tx, ty, task_type = self.worker_targets[wid]

                # Validate target
                valid = False
                if task_type == "HARVEST":
                    valid = any(c.x == tx and c.y == ty and c.growth_stage == 3 for c in state.crops)
                elif task_type == "WATER":
                    valid = any(c.x == tx and c.y == ty and (c.moisture <= 30 or not c.is_watered) for c in state.crops)
                elif task_type == "PLANT":
                    # Must actually have seeds to plant!
                    has_seeds = state.farm.seed_inventory.get(self.crop_to_plant, 0) > 0
                    valid = (tx, ty) in empty_tilled_tiles and has_seeds and not target.is_liquidating and state.turn < 715

                if valid:
                    # Re-assign same target
                    assigned_tasks.add((tx, ty))
                    dist = manhattan_distance(worker.x, worker.y, tx, ty)
                    if dist <= 1:
                        if task_type == "HARVEST":
                            worker_actions[wid] = ("HARVEST", tx, ty)
                        elif task_type == "WATER":
                            worker_actions[wid] = ("WATER", tx, ty)
                        elif task_type == "PLANT":
                            best_crop = self.crop_to_plant
                            max_deficit = 0
                            for crop_type, target_count in target.crop_priorities.items():
                                current_planted = active_crop_counts.get(crop_type, 0)
                                deficit = target_count - current_planted
                                if deficit > max_deficit:
                                    max_deficit = deficit
                                    best_crop = crop_type
                            worker_actions[wid] = ("PLANT", tx, ty, best_crop)
                    else:
                        path = find_shortest_path(worker.x, worker.y, tx, ty)
                        if path:
                            worker_actions[wid] = path[0]
                else:
                    # Target is no longer valid, discard it
                    if wid in self.worker_targets:
                        del self.worker_targets[wid]

        # Second pass: allocate new targets for idle workers
        for worker in state.farm.workers:
            wid = worker.worker_id
            if wid in worker_actions:
                continue  # Already has a validated persisted target

            # Priority 1: HARVEST mature crops
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
                tx, ty = best_harvest.x, best_harvest.y
                self.worker_targets[wid] = (tx, ty, "HARVEST")
                assigned_tasks.add((tx, ty))

                if best_dist <= 1:
                    worker_actions[wid] = ("HARVEST", tx, ty)
                else:
                    path = find_shortest_path(worker.x, worker.y, tx, ty)
                    if path:
                        worker_actions[wid] = path[0]
                continue

            # Priority 2: WATER thirsty crops
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
                tx, ty = best_thirsty.x, best_thirsty.y
                self.worker_targets[wid] = (tx, ty, "WATER")
                assigned_tasks.add((tx, ty))

                if best_dist <= 1:
                    worker_actions[wid] = ("WATER", tx, ty)
                else:
                    path = find_shortest_path(worker.x, worker.y, tx, ty)
                    if path:
                        worker_actions[wid] = path[0]
                continue

            # Priority 3: PLANT empty tilled tiles
            has_seeds = state.farm.seed_inventory.get(self.crop_to_plant, 0) > 0
            if has_seeds and not target.is_liquidating and state.turn < 715:
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
                    self.worker_targets[wid] = (tx, ty, "PLANT")
                    assigned_tasks.add((tx, ty))

                    # Determine best crop
                    best_crop = self.crop_to_plant
                    max_deficit = 0
                    for crop_type, target_count in target.crop_priorities.items():
                        current_planted = active_crop_counts.get(crop_type, 0)
                        deficit = target_count - current_planted
                        if deficit > max_deficit:
                            max_deficit = deficit
                            best_crop = crop_type

                    if best_dist <= 1:
                        worker_actions[wid] = ("PLANT", tx, ty, best_crop)
                    else:
                        path = find_shortest_path(worker.x, worker.y, tx, ty)
                        if path:
                            worker_actions[wid] = path[0]
                    continue

            # Priority 4: Default Idle Movement (move right)
            worker_actions[wid] = ("MOVE", "RIGHT")

        return {"worker_actions": worker_actions, "farm_actions": farm_actions}
