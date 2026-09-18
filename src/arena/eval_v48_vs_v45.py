"""Compare Jaxa V48 Clear-Queue vs a standard public baseline like EXP-173 v45 Fusion Router."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.arena.quick_h2h import run_h2h

if __name__ == "__main__":
    seeds = [42, 100, 2026]
    run_h2h("Jaxa V48 Clear-Queue", "EXP-173 v45 Fusion Router", seeds)
