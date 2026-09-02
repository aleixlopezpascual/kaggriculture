"""Kaggriculture immutable game state representation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CropState:
    """State of an individual crop on the grid."""

    crop_type: str
    growth_stage: int  # 0: Seed, 1: Sprout, 2: Mature, 3: Harvestable
    moisture: int  # Moisture level (0 to 100)
    is_watered: bool
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class AnimalState:
    """State of an individual animal on the farm."""

    animal_type: str  # "Cow", "Sheep", "Chicken"
    hunger: int  # Hunger level (0 to 100)
    is_fed: bool
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class WorkerState:
    """State of an individual hired agricultural worker."""

    worker_id: int
    x: int
    y: int
    carrying: tuple[str, ...]  # Tuple of carried item names (e.g. ("WHEAT",))
    is_busy: bool


@dataclass(frozen=True, slots=True)
class FarmState:
    """State of the player's farm financial and resource accounts."""

    gold: int
    inventory: dict[str, int]  # Map of harvested item_name -> count
    seed_inventory: dict[str, int]  # Map of seed crop_name -> count
    workers: tuple[WorkerState, ...]
    expansion_quadrants: int  # Number of expanded quadrants purchased


@dataclass(frozen=True, slots=True)
class WorldState:
    """The overarching global world state of Kaggriculture."""

    turn: int  # 0 to 720
    weather: str  # "Sunny", "Rainy", "Overcast"
    grid_width: int
    grid_height: int
    crops: tuple[CropState, ...]
    animals: tuple[AnimalState, ...]
    farm: FarmState
    tilled_tiles: tuple[tuple[int, int], ...]  # List of coordinates currently tilled


@dataclass(frozen=True, slots=True)
class StrategicTarget:
    """Target resource objectives selected by the high-level MCTS Strategic Brain."""

    target_workers: int
    target_cows: int
    target_sheep: int
    target_geese: int
    crop_priorities: dict[str, int]
    budget_reserved_for_seeds: float
    is_liquidating: bool
