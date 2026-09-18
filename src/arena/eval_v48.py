"""Local Tournament Benchmark for Jaxa V48 Clear-Queue."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.arena.quick_h2h import run_h2h

if __name__ == "__main__":
    # Run over 5 representative evaluation seeds in both seats (10 matches total)
    seeds = [42, 100, 2026, 1234, 555]
    run_h2h("Jaxa V48 Clear-Queue", "Jaxa 2802 Elo Router", seeds)
