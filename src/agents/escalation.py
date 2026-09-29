"""Kaggriculture Dynamic Escalation Agent."""

from src.agents.heuristic import HeuristicAgent
from src.env.state import StrategicTarget, WorldState
from src.utils.routing import find_shortest_path, manhattan_distance
from src.utils.sale_reservation import BoundedSaleReservation


def get_fibonacci_wage(n: int) -> int:
    """Returns the n-th Fibonacci number (daily wage for hand n)."""
    if n <= 0:
        return 0
    if n in (1, 2):
        return 1
    a, b = 1, 1
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


class EscalationAgent(HeuristicAgent):
    """Dynamic Escalation Agent with Target Persistence, Seed Inventory guards,
    and Drop-off routing.

    Scales crop volume based on gold, uses exact Fibonacci curves for labor scaling,
    executes animal purchases at correct official costs, and uses persisted
    targeting to ensure workers do not thrash. Integrates mid-day cargo drop-off
    routing to maximize cash flow.
    """

    def __init__(self, crop_to_plant: str = "Strawberry"):
        super().__init__(crop_to_plant=crop_to_plant)
        # Map worker_id -> (tx, ty, task_type)
        self.worker_targets = {}
        self.reserver = BoundedSaleReservation()

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

            # End-game liquidation: stop buying seeds after Turn 660 to ensure
            # cashout before Turn 720
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

        cows = sum(1 for a in state.animals if a.animal_type == "Cow")
        sheep = sum(1 for a in state.animals if a.animal_type == "Sheep")
        geese = sum(1 for a in state.animals if a.animal_type == "Goose")

        # 3. Macro Farm Actions (Hiring, Purchases)
        farm_actions = []

        # HIRE (Loop to support multiple hires per turn under proper wage budget)
        current_hands = len(state.farm.workers) - 1
        max_workers = 1 + (state.farm.expansion_quadrants * 2)
        target_workers = min(target.target_workers, max_workers)

        while (
            len(state.farm.workers) + farm_actions.count("HIRE_WORKER") < target_workers
            and gold_available
            >= get_fibonacci_wage(current_hands + farm_actions.count("HIRE_WORKER") + 1)
            + target.budget_reserved_for_seeds
        ):
            wage = get_fibonacci_wage(
                current_hands + farm_actions.count("HIRE_WORKER") + 1
            )
            farm_actions.append("HIRE_WORKER")
            gold_available -= wage

        # Purchase Cows (Official cost $400)
        if (
            cows < target.target_cows
            and gold_available >= 400 + target.budget_reserved_for_seeds
        ):
            farm_actions.append(("BUY_ANIMAL", "Cow"))
            gold_available -= 400
            cows += 1

        # Purchase Sheep (Official cost $500)
        if (
            sheep < target.target_sheep
            and gold_available >= 500 + target.budget_reserved_for_seeds
        ):
            farm_actions.append(("BUY_ANIMAL", "Sheep"))
            gold_available -= 500
            sheep += 1

        # Purchase Geese (Official cost $300)
        if (
            geese < target.target_geese
            and gold_available >= 300 + target.budget_reserved_for_seeds
        ):
            farm_actions.append(("BUY_ANIMAL", "Goose"))
            gold_available -= 300
            geese += 1

        # Buy seeds for crop deficits
        if not target.is_liquidating and state.turn < 710:
            for crop_type, target_count in target.crop_priorities.items():
                current_planted = active_crop_counts.get(crop_type, 0)
                current_seeds = state.farm.seed_inventory.get(crop_type, 0)
                deficit = target_count - current_planted - current_seeds
                if deficit > 0:
                    seed_prices = {
                        "Wheat": 10,
                        "Carrot": 20,
                        "Tomato": 50,
                        "Strawberry": 100,
                        "Melon": 80,
                    }
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

        # OVERRIDE FOR MICROSTRUCTURE WHEAT FLIP (Turns 0, 1, 2)
        if state.turn == 0:
            farm_actions = [("BUY_PRODUCT", "Wheat", 7), ("SELL", "Wheat", 2)]
        elif state.turn == 1:
            farm_actions = [("BUY_PRODUCT", "Wheat", 30)]
        elif state.turn == 2:
            # Sell the resold wheat + any other inventory
            has_wheat_sale = any(
                act[0] == "SELL" and act[1] == "Wheat" for act in farm_actions
            )
            if not has_wheat_sale and state.farm.inventory.get("Wheat", 0) > 0:
                farm_actions.append(
                    ("SELL", "Wheat", state.farm.inventory.get("Wheat", 0))
                )
            # Re-rank to maintain pricing optimality
            sell_orders = [act for act in farm_actions if act[0] == "SELL"]
            other_acts = [act for act in farm_actions if act[0] != "SELL"]
            from src.utils.market import rank_sell_orders

            sell_orders = rank_sell_orders(sell_orders)
            farm_actions = other_acts + sell_orders

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
                    valid = any(
                        c.x == tx and c.y == ty and c.growth_stage == 3
                        for c in state.crops
                    )
                elif task_type == "WATER":
                    valid = any(
                        c.x == tx
                        and c.y == ty
                        and (c.moisture <= 30 or not c.is_watered)
                        for c in state.crops
                    )
                elif task_type == "PLANT":
                    # Must actually have seeds to plant!
                    has_seeds = state.farm.seed_inventory.get(self.crop_to_plant, 0) > 0
                    valid = (
                        (tx, ty) in empty_tilled_tiles
                        and has_seeds
                        and not target.is_liquidating
                        and state.turn < 715
                    )
                elif task_type == "DROP":
                    # Valid if still carrying items
                    valid = len(worker.carrying) > 0
                elif task_type == "PICKUP":
                    # Valid if we don't have Wheat, and shed has Wheat
                    valid = (
                        "Wheat" not in worker.carrying
                        and state.farm.inventory.get("Wheat", 0) > 0
                    )
                elif task_type == "FEED":
                    # Valid if we have Wheat, and animal at (tx, ty) exists
                    # and is hungry
                    valid = "Wheat" in worker.carrying and any(
                        a.x == tx and a.y == ty and a.hunger >= 50
                        for a in state.animals
                    )

                if valid:
                    # Re-assign same target
                    if task_type in ("HARVEST", "WATER", "PLANT", "FEED"):
                        assigned_tasks.add((tx, ty))

                    if task_type == "DROP":
                        if abs(worker.x - 4) + abs(worker.y - 4) <= 1:
                            worker_actions[wid] = (
                                "DROP",
                                worker.carrying[0],
                                len(worker.carrying),
                            )
                        else:
                            path = find_shortest_path(worker.x, worker.y, 4, 4)
                            if path:
                                worker_actions[wid] = path[0]
                    elif task_type == "PICKUP":
                        if abs(worker.x - 4) + abs(worker.y - 4) <= 1:
                            worker_actions[wid] = ("PICKUP", "Wheat", 1)
                        else:
                            path = find_shortest_path(worker.x, worker.y, 4, 4)
                            if path:
                                worker_actions[wid] = path[0]
                    else:
                        dist = manhattan_distance(worker.x, worker.y, tx, ty)
                        if dist <= 1:
                            if task_type == "HARVEST":
                                worker_actions[wid] = ("HARVEST", tx, ty)
                            elif task_type == "WATER":
                                worker_actions[wid] = ("WATER", tx, ty)
                            elif task_type == "FEED":
                                worker_actions[wid] = ("FEED", tx, ty)
                            elif task_type == "PLANT":
                                best_crop = self.crop_to_plant
                                max_deficit = 0
                                for (
                                    crop_type,
                                    target_count,
                                ) in target.crop_priorities.items():
                                    current_planted = active_crop_counts.get(
                                        crop_type, 0
                                    )
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

            # Priority 2: FEED hungry animals (requires Wheat)
            hungry_animals = [a for a in state.animals if a.hunger >= 50]
            if hungry_animals:
                if "Wheat" in worker.carrying:
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
                        tx, ty = best_animal.x, best_animal.y
                        self.worker_targets[wid] = (tx, ty, "FEED")
                        assigned_tasks.add((tx, ty))

                        if best_dist <= 1:
                            worker_actions[wid] = ("FEED", tx, ty)
                        else:
                            path = find_shortest_path(worker.x, worker.y, tx, ty)
                            if path:
                                worker_actions[wid] = path[0]
                        continue
                else:
                    # No Wheat in hand: go pickup from central shed if available
                    if state.farm.inventory.get("Wheat", 0) > 0:
                        self.worker_targets[wid] = (4, 4, "PICKUP")
                        if abs(worker.x - 4) + abs(worker.y - 4) <= 1:
                            worker_actions[wid] = ("PICKUP", "Wheat", 1)
                        else:
                            path = find_shortest_path(worker.x, worker.y, 4, 4)
                            if path:
                                worker_actions[wid] = path[0]
                            else:
                                worker_actions[wid] = ("MOVE", "RIGHT")
                        continue

            # Priority 3: WATER thirsty crops
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

            # Priority 4: PLANT empty tilled tiles
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

            # Priority 5: DROP cargo to central shed if carrying items
            if len(worker.carrying) > 0:
                self.worker_targets[wid] = (4, 4, "DROP")
                if abs(worker.x - 4) + abs(worker.y - 4) <= 1:
                    worker_actions[wid] = (
                        "DROP",
                        worker.carrying[0],
                        len(worker.carrying),
                    )
                else:
                    path = find_shortest_path(worker.x, worker.y, 4, 4)
                    if path:
                        worker_actions[wid] = path[0]
                    else:
                        worker_actions[wid] = ("MOVE", "RIGHT")
                continue

            # Priority 6: Default Idle Movement (move right)
            worker_actions[wid] = ("MOVE", "RIGHT")

        # === TERMINAL BOOST FOR FINAL 7 STEPS ===
        if state.turn >= 713:
            worker_actions = {}
            # Clear targets
            self.worker_targets.clear()

            for worker in state.farm.workers:
                wid = worker.worker_id

                if len(worker.carrying) > 0:
                    # Standing on shed (4, 4)?
                    if worker.x == 4 and worker.y == 4:
                        worker_actions[wid] = ("DROP", 4, 4)
                    else:
                        path = find_shortest_path(worker.x, worker.y, 4, 4)
                        if path:
                            worker_actions[wid] = path[0]
                        else:
                            worker_actions[wid] = ("MOVE", "RIGHT")
                else:
                    # Idle -> prioritizes immediate harvesting of mature crops
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
                        assigned_tasks.add((best_harvest.x, best_harvest.y))
                        if best_dist <= 1:
                            worker_actions[wid] = (
                                "HARVEST",
                                best_harvest.x,
                                best_harvest.y,
                            )
                        else:
                            path = find_shortest_path(
                                worker.x, worker.y, best_harvest.x, best_harvest.y
                            )
                            if path:
                                worker_actions[wid] = path[0]
                            else:
                                worker_actions[wid] = ("MOVE", "RIGHT")
                    else:
                        # No mature crops -> cluster at central shed (4,4)
                        if worker.x == 4 and worker.y == 4:
                            worker_actions[wid] = ("PASS",)
                        else:
                            path = find_shortest_path(worker.x, worker.y, 4, 4)
                            if path:
                                worker_actions[wid] = path[0]
                            else:
                                worker_actions[wid] = ("PASS",)

            # No purchases/hiring in terminal steps, only sales
            farm_actions = [
                act
                for act in farm_actions
                if isinstance(act, tuple) and len(act) == 3 and act[0] == "SELL"
            ]

        # Wrap farm_actions with BoundedSaleReservation
        future_tape = []
        for item, qty in state.farm.inventory.items():
            if qty > 0:
                # Mock a future scheduled sale of these items
                future_tape.append(("SELL", item, qty))

        farm_actions = self.reserver.process_turn_with_future(
            state, farm_actions, future_tape
        )

        return {"worker_actions": worker_actions, "farm_actions": farm_actions}
