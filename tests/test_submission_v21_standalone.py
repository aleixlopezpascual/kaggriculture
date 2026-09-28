"""Standalone package tests for Prvsiyan V2.1 (restored v9 step-0 opening).

V2.1 is byte-identical to V2 except for main.py, which rebinds the baseline's
native ``V9_OPENING_STEP0`` constant from the shipped BUY 20 / SELL 15 back to
the BUY 10 / SELL 5 opening documented in baseline.py's own comment block.
"""

import hashlib
import importlib.util
import sys
import tarfile
import tempfile
from pathlib import Path

import kaggle_environments
import pytest

PKG_DIR = Path("submission/prvsiyan_v21_package")
EXPECTED_BASELINE_SHA256 = (
    "178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a"
)
EXPECTED_HELPER_SHA256 = (
    "6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59"
)


def _load_v21():
    spec = importlib.util.spec_from_file_location(
        "_v21_main_under_test", (PKG_DIR / "main.py").resolve()
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_components_integrity():
    assert PKG_DIR.is_dir()

    actual_b = hashlib.sha256((PKG_DIR / "baseline.py").read_bytes()).hexdigest()
    actual_h = hashlib.sha256((PKG_DIR / "optimizer.py").read_bytes()).hexdigest()

    assert actual_b == EXPECTED_BASELINE_SHA256
    assert actual_h == EXPECTED_HELPER_SHA256
    assert (PKG_DIR / "LICENSE.txt").is_file()
    assert (PKG_DIR / "NOTICE.txt").is_file()
    assert (PKG_DIR / "main.py").is_file()


def test_baseline_is_byte_identical_to_v2():
    for name in ("baseline.py", "optimizer.py"):
        v2 = (Path("submission/prvsiyan_v2_package") / name).read_bytes()
        v21 = (PKG_DIR / name).read_bytes()
        assert v2 == v21, f"{name} diverged from the frozen V2 component"


def test_opening_constant_is_restored():
    module = _load_v21()

    assert module.V21_OPENING_STEP0 == (
        ("BUY_PRODUCT", "WHEAT", 10),
        ("SELL", "WHEAT", 5),
    )
    assert module._BASELINE_MOD.V9_OPENING_STEP0 == module.V21_OPENING_STEP0


def test_opening_retains_five_wheat_feed_buffer():
    """SELL 5 (not 10) is load-bearing.

    Selling the full 10 wheat removes the day-1 feed buffer and collapses the
    agent to roughly a third of its usual terminal gold, so the invariant is
    asserted explicitly rather than left implicit in the constant.
    """
    module = _load_v21()
    bought = {
        item: qty
        for verb, item, qty in module.V21_OPENING_STEP0
        if verb == "BUY_PRODUCT"
    }
    sold = {
        item: qty for verb, item, qty in module.V21_OPENING_STEP0 if verb == "SELL"
    }

    assert bought["WHEAT"] - sold["WHEAT"] == 5


def test_opening_tape_guard_still_matches_baseline():
    """The overlay only substitutes when the route tape's opening is intact."""
    module = _load_v21()
    tape = module._BASELINE_MOD.V9_OPENING_TAPE

    assert tape[0] == (
        ("BUY_PRODUCT", "WHEAT", 13),
        ("BUY_PRODUCT", "WHEAT", 30),
        ("SELL", "WHEAT", 30),
    )
    assert tape[1] == (("SELL", "WHEAT", 13), ("BUY_PRODUCT", "WHEAT", 5))


def test_full_game_simulation_completes():
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
    opponent_path = str(
        Path("competitors/notebooks/shepherd_sovereign_main.py").resolve()
    )

    steps = env.run([str((PKG_DIR / "main.py").resolve()), opponent_path])

    assert len(steps) == 720
    assert steps[-1][0]["status"] == "DONE"
    assert steps[-1][1]["status"] == "DONE"
    assert steps[-1][0]["reward"] > 0


def test_step_zero_market_orders_use_restored_opening():
    """The emitted step-0 market tape must carry BUY 10 / SELL 5."""
    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
    opponent_path = str(
        Path("competitors/notebooks/shepherd_sovereign_main.py").resolve()
    )

    steps = env.run([str((PKG_DIR / "main.py").resolve()), opponent_path])
    # kaggle-environments records each step's action on the *following* state.
    market = steps[1][0]["action"]["market"]
    wheat = [
        (o[0], o[1], int(o[2]))
        for o in market
        if len(o) >= 3 and o[0] in ("BUY_PRODUCT", "SELL") and o[1] == "WHEAT"
    ]

    assert wheat == [("BUY_PRODUCT", "WHEAT", 10), ("SELL", "WHEAT", 5)]


def test_kaggle_exec_container_simulation():
    """Verify exact Kaggle container execution where __file__ is absent."""
    main_file = (PKG_DIR / "main.py").resolve()
    code_obj = compile(main_file.read_text(encoding="utf-8"), str(main_file), "exec")

    env: dict[str, object] = {}
    sys.path.append(str(main_file.parent))
    try:
        exec(code_obj, env)  # noqa: S102
        callables = [v for v in env.values() if callable(v)]
        assert len(callables) > 0
        agent_fn = callables[-1]

        obs = {"step": 0, "player": 0, "gold": 1000, "market": {"inventory": {}}}

        class DummyConfig:
            pass

        action = agent_fn(obs, DummyConfig())
        assert isinstance(action, dict)
        assert "farmer" in action
        assert "market" in action
    finally:
        sys.path.pop()


def test_tarball_unpack_and_full_game_simulation():
    tar_path = Path("submission/prvsiyan_v21_submission.tar.gz")
    if not tar_path.is_file():
        pytest.skip("V2.1 tarball not built yet")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(tmp_path, filter="data")

        extracted_main = tmp_path / "main.py"
        assert extracted_main.is_file()

        env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
        opponent_path = str(
            Path("competitors/notebooks/shepherd_sovereign_main.py").resolve()
        )

        steps = env.run([str(extracted_main.resolve()), opponent_path])

        assert len(steps) == 720
        assert steps[-1][0]["status"] == "DONE"
        assert steps[-1][0]["reward"] > 0
