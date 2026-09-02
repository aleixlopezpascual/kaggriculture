"""Kaggriculture state featurizer converting WorldState to flat 2D numpy arrays."""

import numpy as np

from src.env.state import WorldState


def featurize_state(state: WorldState) -> dict[str, np.ndarray]:
    """Converts the WorldState into a dict of flat or 2D NumPy feature matrices.

    Features generated:
    - "tilled": 2D grid where tilled cells are 1.0, others are 0.0.
    - "growth": 2D grid containing crop growth stages (0-3).
    - "moisture": 2D grid containing crop moisture levels (0-100 normalized to 0.0-1.0).
    - "workers": 2D grid containing worker locations.
    """
    w, h = state.grid_width, state.grid_height

    # Pre-allocate grids
    tilled_grid = np.zeros((h, w), dtype=np.float32)
    growth_grid = np.zeros((h, w), dtype=np.float32)
    moisture_grid = np.zeros((h, w), dtype=np.float32)
    workers_grid = np.zeros((h, w), dtype=np.float32)

    # Populate tilled tiles
    for tx, ty in state.tilled_tiles:
        if 0 <= tx < w and 0 <= ty < h:
            tilled_grid[ty, tx] = 1.0

    # Populate crop states
    for crop in state.crops:
        cx, cy = crop.x, crop.y
        if 0 <= cx < w and 0 <= cy < h:
            growth_grid[cy, cx] = float(crop.growth_stage)
            moisture_grid[cy, cx] = float(crop.moisture) / 100.0

    # Populate worker positions
    for worker in state.farm.workers:
        wx, wy = worker.x, worker.y
        if 0 <= wx < w and 0 <= wy < h:
            workers_grid[wy, wx] += 1.0

    return {
        "tilled": tilled_grid,
        "growth": growth_grid,
        "moisture": moisture_grid,
        "workers": workers_grid,
    }
