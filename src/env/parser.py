"""Kaggriculture Kaggle observation parser supporting multiple schemas."""

from src.env.state import AnimalState, CropState, FarmState, WorkerState, WorldState


def parse_world_state(obs: dict) -> WorldState:
    """Parses a nested Kaggle observation dict into WorldState structure."""
    # Detect if we are parsing the official Kaggle environment or our custom mock
    is_official_kaggle = "farms" in obs

    if is_official_kaggle:
        from src.utils.market import update_market_state
        update_market_state(obs)

        player_idx = obs.get("player", 0)
        official_farm = obs["farms"][player_idx]

        # 1. Parse Hired Workers and Farmer Cargo
        workers_list = []
        private_inventories = obs.get("private", {}).get("inventories", [])

        # Farmer (ID 1)
        farmer_pos = official_farm.get("farmer", [4, 4])
        # Sometimes inventories are parsed as dict of lists or list of lists
        farmer_carrying_raw = []
        if isinstance(private_inventories, list) and len(private_inventories) > 0:
            farmer_carrying_raw = private_inventories[0]
        elif isinstance(private_inventories, dict):
            # Fallback if key-based
            farmer_carrying_raw = private_inventories.get("0", [])

        # Ensure list/tuple format
        if not isinstance(farmer_carrying_raw, (list, tuple)):
            farmer_carrying_raw = []
        farmer_carrying = tuple(str(i).capitalize() for i in farmer_carrying_raw)

        workers_list.append(
            WorkerState(
                worker_id=1,
                x=farmer_pos[0],
                y=farmer_pos[1],
                carrying=farmer_carrying,
                is_busy=False,
            )
        )

        # Hired Hands (ID 2+)
        for idx, hand_pos in enumerate(official_farm.get("hands", [])):
            hand_carrying_raw = []
            if (
                isinstance(private_inventories, list)
                and len(private_inventories) > idx + 1
            ):
                hand_carrying_raw = private_inventories[idx + 1]
            elif isinstance(private_inventories, dict):
                hand_carrying_raw = private_inventories.get(str(idx + 1), [])

            if not isinstance(hand_carrying_raw, (list, tuple)):
                hand_carrying_raw = []
            hand_carrying = tuple(str(i).capitalize() for i in hand_carrying_raw)

            workers_list.append(
                WorkerState(
                    worker_id=idx + 2,
                    x=hand_pos[0],
                    y=hand_pos[1],
                    carrying=hand_carrying,
                    is_busy=False,
                )
            )

        # 2. Parse tiles board grid for crops, animals, and tilled status
        crops_list = []
        animals_list = []
        tiles_board = official_farm.get("tiles", [])

        occupied = set()

        for y, row in enumerate(tiles_board):
            for x, cell in enumerate(row):
                if cell and isinstance(cell, dict):
                    kind = cell.get("kind")
                    if kind == "PLANT":
                        crop_type = str(cell.get("crop", "WHEAT")).capitalize()
                        yield_units = int(cell.get("yield_units", 0))
                        growth_stage = 3 if yield_units > 0 else 0
                        watered = bool(cell.get("watered_today", False))
                        crops_list.append(
                            CropState(
                                crop_type=crop_type,
                                growth_stage=growth_stage,
                                moisture=50,
                                is_watered=watered,
                                x=x,
                                y=y,
                            )
                        )
                        occupied.add((x, y))
                    elif kind == "ANIMAL":
                        animal_type = str(cell.get("animal", "COW")).capitalize()
                        hunger = int(cell.get("hunger", 0))
                        animals_list.append(
                            AnimalState(
                                animal_type=animal_type,
                                hunger=hunger,
                                is_fed=True,
                                x=x,
                                y=y,
                            )
                        )
                        occupied.add((x, y))
                    elif kind in {"COOP", "PASTURE", "WEED", "LOCKED", "SHED"}:
                        occupied.add((x, y))
                    elif kind == "TILLED":
                        occupied.add((x, y))

        # Generate tilled_tiles as all unoccupied unlocked coordinates
        unlocked_quads = official_farm.get("unlocked_quadrants", ["NW"])
        unlocked_coords = set()
        for q in unlocked_quads:
            if q == "NW":
                xs, ys = range(0, 5), range(0, 5)
            elif q == "NE":
                xs, ys = range(5, 10), range(0, 5)
            elif q == "SW":
                xs, ys = range(0, 5), range(5, 10)
            elif q == "SE":
                xs, ys = range(5, 10), range(5, 10)
            else:
                continue
            for x in xs:
                for y in ys:
                    unlocked_coords.add((x, y))

        tilled_tiles = [coord for coord in unlocked_coords if coord not in occupied]

        # 3. Assemble FarmState and WorldState
        gold = int(official_farm.get("money", 3000))
        inventory_raw = obs.get("private", {}).get("shed", {})
        inventory = {str(k).capitalize(): int(v) for k, v in inventory_raw.items()}

        seed_inventory_raw = obs.get("private", {}).get("seeds", {})
        seed_inventory = {
            str(k).capitalize(): int(v) for k, v in seed_inventory_raw.items()
        }

        farm_state = FarmState(
            gold=gold,
            inventory=inventory,
            seed_inventory=seed_inventory,
            workers=tuple(workers_list),
            expansion_quadrants=len(official_farm.get("unlocked_quadrants", ["NW"])),
        )

        return WorldState(
            turn=int(obs.get("step", 0)),
            weather=obs.get("weather", "Sunny"),
            grid_width=len(tiles_board) if tiles_board else 10,
            grid_height=len(tiles_board[0]) if tiles_board else 10,
            crops=tuple(crops_list),
            animals=tuple(animals_list),
            farm=farm_state,
            tilled_tiles=tuple(tilled_tiles),
        )

    else:
        # Fallback to Custom Local Parser format
        raw_crops = obs.get("crops", [])
        crops_list = []
        for c in raw_crops:
            crops_list.append(
                CropState(
                    crop_type=c["crop_type"],
                    growth_stage=c["growth_stage"],
                    moisture=c["moisture"],
                    is_watered=c.get("is_watered", False),
                    x=c["x"],
                    y=c["y"],
                )
            )

        raw_animals = obs.get("animals", [])
        animals_list = []
        for a in raw_animals:
            animals_list.append(
                AnimalState(
                    animal_type=a["animal_type"],
                    hunger=a["hunger"],
                    is_fed=a.get("is_fed", False),
                    x=a["x"],
                    y=a["y"],
                )
            )

        raw_farm = obs.get("farm", {})
        raw_workers = raw_farm.get("workers", [])
        workers_list = []
        for w in raw_workers:
            raw_carrying = w.get("carrying")
            if isinstance(raw_carrying, list):
                carrying_tuple = tuple(raw_carrying)
            elif isinstance(raw_carrying, str):
                carrying_tuple = (raw_carrying,)
            else:
                carrying_tuple = ()

            workers_list.append(
                WorkerState(
                    worker_id=w["worker_id"],
                    x=w["x"],
                    y=w["y"],
                    carrying=carrying_tuple,
                    is_busy=w.get("is_busy", False),
                )
            )

        farm_state = FarmState(
            gold=raw_farm.get("gold", 0),
            inventory=dict(raw_farm.get("inventory", {})),
            seed_inventory=dict(raw_farm.get("seed_inventory", {})),
            workers=tuple(workers_list),
            expansion_quadrants=raw_farm.get("expansion_quadrants", 0),
        )

        raw_tilled = obs.get("tilled_tiles", [])
        tilled_tiles = tuple((int(t[0]), int(t[1])) for t in raw_tilled)

        return WorldState(
            turn=obs.get("turn", 0),
            weather=obs.get("weather", "Sunny"),
            grid_width=obs.get("grid_width", 10),
            grid_height=obs.get("grid_height", 10),
            crops=tuple(crops_list),
            animals=tuple(animals_list),
            farm=farm_state,
            tilled_tiles=tilled_tiles,
        )
