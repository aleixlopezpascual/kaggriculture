"""Kaggriculture Kaggle observation dictionary/array parser."""

from src.env.state import AnimalState, CropState, FarmState, WorkerState, WorldState


def parse_world_state(obs: dict) -> WorldState:
    """Parses a nested Kaggle observation dict into the WorldState domain structure."""
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
        workers_list.append(
            WorkerState(
                worker_id=w["worker_id"],
                x=w["x"],
                y=w["y"],
                carrying=w.get("carrying"),
                is_busy=w.get("is_busy", False),
            )
        )

    farm_state = FarmState(
        gold=raw_farm.get("gold", 0),
        inventory=dict(raw_farm.get("inventory", {})),
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
