# Claude Code Terminal Cheat-Sheet: Kaggriculture

This sheet contains common commands for developing, linting, testing, and bundling in the Kaggriculture workspace.

---

## 🛠️ Linting & Formatting

Run Black to auto-format code:
```bash
black .
```

Verify Ruff formatting and check for errors:
```bash
ruff check .
```

Auto-apply Ruff fixes:
```bash
ruff check . --fix
```

---

## 🧪 Testing

Run all unit tests:
```bash
pytest
```

Run a specific test file:
```bash
pytest tests/test_env_transitions.py -v
```

Run tests matching a specific pattern:
```bash
pytest -k "watering"
```

---

## 🚀 Running Matches & Compilation

Compile the modular workspace into a unified `submission/submission.py`:
```bash
python submission/compile_submission.py
```

Run a local evaluation run over multiple seeds (e.g., evaluating HeuristicAgent):
```bash
python -c "
from src.agents.heuristic import HeuristicAgent
from src.arena.evaluator import LocalArena
agent = HeuristicAgent()
arena = LocalArena(agent)
print(arena.benchmark(seeds=[42, 100, 2026]))
"
```
