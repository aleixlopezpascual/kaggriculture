import hashlib
import sys
import tarfile
import tempfile
from pathlib import Path

import kaggle_environments
import pytest


def test_package_components_integrity():
    pkg_dir = Path("submission/prvsiyan_v2_package")
    assert pkg_dir.is_dir()

    expected_baseline_sha256 = (
        "178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a"
    )
    expected_helper_sha256 = (
        "6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59"
    )

    actual_b = hashlib.sha256((pkg_dir / "baseline.py").read_bytes()).hexdigest()
    actual_h = hashlib.sha256((pkg_dir / "optimizer.py").read_bytes()).hexdigest()

    assert actual_b == expected_baseline_sha256
    assert actual_h == expected_helper_sha256
    assert (pkg_dir / "LICENSE.txt").is_file()
    assert (pkg_dir / "NOTICE.txt").is_file()
    assert (pkg_dir / "main.py").is_file()


def test_tarball_unpack_and_full_game_simulation():
    tar_path = Path("submission/prvsiyan_v2_submission.tar.gz")
    if not tar_path.is_file():
        pytest.skip("V2 tarball not created yet")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(tmp_path, filter="data")

        extracted_main = tmp_path / "main.py"
        assert extracted_main.is_file()

        # Run a full simulation using kaggle-environments
        env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
        opponent_path = str(
            Path("competitors/notebooks/shepherd_sovereign_main.py").resolve()
        )

        steps = env.run([str(extracted_main.resolve()), opponent_path])
        assert len(steps) == 720

        final_step = steps[-1]
        p0 = final_step[0]
        p1 = final_step[1]

        assert p0.status == "DONE"
        assert p1.status == "DONE"
        assert p0.reward is not None
        assert p1.reward is not None
        assert p0.reward > 0


def test_kaggle_exec_container_simulation():
    """Verify exact Kaggle container execution where __file__ is absent."""
    tar_path = Path("submission/prvsiyan_v2_submission.tar.gz")
    if not tar_path.is_file():
        pytest.skip("V2 tarball not created yet")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(tmp_path, filter="data")

        main_file = tmp_path / "main.py"
        code = main_file.read_text(encoding="utf-8")
        code_obj = compile(code, str(main_file), "exec")

        # Empty env as constructed by kaggle_environments.agent.get_last_callable
        env: dict[str, object] = {}
        sys.path.append(str(tmp_path))
        try:
            exec(code_obj, env)  # noqa: S102
            callables = [v for v in env.values() if callable(v)]
            assert len(callables) > 0
            agent_fn = callables[-1]
            assert callable(agent_fn)

            # Test call
            obs = {"step": 0, "player": 0, "gold": 1000, "market": {"inventory": {}}}

            class DummyConfig:
                pass

            action = agent_fn(obs, DummyConfig())
            assert isinstance(action, dict)
            assert "farmer" in action
            assert "market" in action
        finally:
            sys.path.pop()


def test_submission_v3_package_standalone():
    v3_main = Path("submission/prvsiyan_v3_package/main.py")
    if not v3_main.is_file():
        pytest.skip("V3 package not created yet")

    env = kaggle_environments.make("kaggriculture", configuration={"seed": 42})
    steps = env.run([str(v3_main.resolve()), "submission/prvsiyan_v2_package/main.py"])
    assert len(steps) == 720
    assert steps[-1][0]["status"] == "DONE"


def test_tarball_v3_unpack_and_full_game_simulation():
    tar_path = Path("submission/prvsiyan_v3_submission.tar.gz")
    if not tar_path.is_file():
        pytest.skip("V3 tarball not created yet")

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
