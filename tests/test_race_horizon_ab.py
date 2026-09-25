import sys
from pathlib import Path

import pytest

import scripts.run_race_horizon_ab as runner


def test_create_candidate_source_success():
    source = "def agent():\n    V9_RACE_DEFAULT = 40\n    return V9_RACE_DEFAULT\n"
    res = runner.create_candidate_source(source)
    assert res == (
        "def agent():\n    V9_RACE_DEFAULT = 41\n    return V9_RACE_DEFAULT\n"
    )
    assert source == (
        "def agent():\n    V9_RACE_DEFAULT = 40\n    return V9_RACE_DEFAULT\n"
    )


def test_create_candidate_source_absent():
    source = "def agent():\n    V9_RACE_DEFAULT = 42\n"
    with pytest.raises(runner.OverrideError):
        runner.create_candidate_source(source)


def test_create_candidate_source_duplicate():
    source = "V9_RACE_DEFAULT = 40\nV9_RACE_DEFAULT = 40\n"
    with pytest.raises(runner.OverrideError):
        runner.create_candidate_source(source)


def test_build_environment_config():
    cfg = runner.build_environment_config(seed=42)
    assert cfg.get("seed") == 42
    assert "randomSeed" not in cfg
    assert cfg.get("episodeSteps") == 720


def test_load_agent_module():
    source = "def agent():\n    return 'action'\n"
    path = Path("fake_agent.py")
    mod = runner.load_agent_module(source, path, "fake_module")
    assert hasattr(mod, "agent")
    assert callable(mod.agent)
    assert mod.agent() == "action"
    assert mod.__file__ == str(path.resolve())


def test_capture_telemetry_present():
    def fake_agent():
        pass

    fake_agent.telemetry = {"key": "value"}
    res = runner.capture_telemetry(fake_agent)
    assert res == {"key": "value"}
    assert res is not fake_agent.telemetry, "Must be a safe copy"


def test_capture_telemetry_absent():
    def fake_agent():
        pass

    res = runner.capture_telemetry(fake_agent)
    assert res == {}


def test_capture_telemetry_includes_module_reports():
    source = (
        "_V9_RACE_REPORT = {'race_errors': 0}\n\n"
        "def agent():\n"
        "    pass\n"
        "agent.telemetry = {'public': 1}\n"
    )
    unique_name = "test_capture_telemetry_includes_module_reports_sys"
    path = Path("fake_agent_reports.py")
    module = runner.load_agent_module(source, path, unique_name)
    try:
        telemetry = runner.capture_telemetry(module.agent, module)
        assert telemetry.get("public") == 1
        assert telemetry.get("_V9_RACE_REPORT") == {"race_errors": 0}
        assert runner.has_telemetry_error(telemetry) is False
    finally:
        sys.modules.pop(unique_name, None)


def test_aggregate_results_success():
    records = [
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "baseline",
            "match_points": 1.0,
            "margin": 200,
            "own_cash": 200,
        },
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "candidate",
            "match_points": 0.0,
            "margin": 0,
            "own_cash": 0,
        },
        {
            "seed": 2,
            "opponent": "botB",
            "seat": 1,
            "arm": "baseline",
            "match_points": 0.5,
            "margin": 100,
            "own_cash": 100,
        },
        {
            "seed": 2,
            "opponent": "botB",
            "seat": 1,
            "arm": "candidate",
            "match_points": 1.0,
            "margin": 150,
            "own_cash": 200,
        },
    ]
    res1 = runner.aggregate_results(records)
    res2 = runner.aggregate_results(records)

    assert (
        res1["ci_95_points"] == res2["ci_95_points"]
    ), "Bootstrap CIs must be deterministic"
    assert (
        res1["ci_95_margin"] == res2["ci_95_margin"]
    ), "Bootstrap CIs must be deterministic"
    assert res1["mean_points_delta"] == -0.25
    assert res1["mean_margin_delta"] == -75
    assert res1["mean_cash_delta"] == -50
    assert "ci_95_points" in res1
    assert "ci_95_margin" in res1

    assert res1["breakdowns"]["by_seed"][1]["matches"] == 1
    assert res1["breakdowns"]["by_seed"][1]["mean_points_delta"] == -1.0
    assert res1["breakdowns"]["by_seed"][1]["mean_margin_delta"] == -200.0
    assert res1["breakdowns"]["by_seed"][1]["mean_cash_delta"] == -200.0

    assert res1["breakdowns"]["by_opponent"]["botA"]["matches"] == 1
    assert res1["breakdowns"]["by_opponent"]["botA"]["mean_points_delta"] == -1.0
    assert res1["breakdowns"]["by_opponent"]["botA"]["mean_margin_delta"] == -200.0
    assert res1["breakdowns"]["by_opponent"]["botA"]["mean_cash_delta"] == -200.0


def test_aggregate_results_missing_arm():
    records = [
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "baseline",
            "match_points": 1.0,
            "margin": 100,
            "own_cash": 500,
        },
    ]
    with pytest.raises(runner.AggregationError):
        runner.aggregate_results(records)


def test_aggregate_results_duplicate_arm():
    records = [
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "baseline",
            "match_points": 1.0,
            "margin": 100,
            "own_cash": 500,
        },
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "baseline",
            "match_points": 1.0,
            "margin": 200,
            "own_cash": 600,
        },
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "candidate",
            "match_points": 0.5,
            "margin": 25,
            "own_cash": 450,
        },
    ]
    with pytest.raises(runner.AggregationError):
        runner.aggregate_results(records)


def test_generate_seeds():
    seeds1 = runner.generate_seeds(rng_seed=42, count=5, exclude=[10, 20])
    seeds2 = runner.generate_seeds(rng_seed=42, count=5, exclude=[10, 20])

    assert seeds1 == seeds2, "Seed generation must be deterministic"
    assert len(seeds1) == 5
    assert len(set(seeds1)) == 5, "Seeds must be unique"
    assert 10 not in seeds1
    assert 20 not in seeds1


def test_load_agent_module_registers_in_sys():
    source = "def agent():\n    return 'action'\n"
    path = Path("fake_agent_sys.py")
    module_name = "test_unique_module_name_sys_42"

    assert module_name not in sys.modules
    mod = runner.load_agent_module(source, path, module_name)
    assert sys.modules.get(module_name) is mod
    assert mod.__file__ == str(path.resolve())


def test_has_telemetry_error():
    assert runner.has_telemetry_error({"outer": {"race_errors": 1}}) is True
    assert runner.has_telemetry_error({"outer": {"race_errors": 0}}) is False
    assert runner.has_telemetry_error({"outer": {"normal_metric": 100}}) is False
    assert runner.has_telemetry_error({}) is False
    assert runner.has_telemetry_error({"race_errors": 1}) is True
    assert runner.has_telemetry_error([{"error_count": 1}]) is True
    assert runner.has_telemetry_error((False, {"exception_occurred": 1})) is True
    assert runner.has_telemetry_error({"failure_rate": 0.5}) is True
    assert runner.has_telemetry_error({"is_error": True}) is False


def test_aggregate_results_unknown_arm():
    records = [
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "baseline",
            "match_points": 1.0,
            "margin": 100,
            "own_cash": 100,
        },
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "candidate",
            "match_points": 0.0,
            "margin": 0,
            "own_cash": 0,
        },
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "unknown",
            "match_points": 0.5,
            "margin": 50,
            "own_cash": 50,
        },
    ]
    with pytest.raises(runner.AggregationError, match="Unknown arm label: unknown"):
        runner.aggregate_results(records)


def test_aggregate_results_invalid_match_points():
    records = [
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "baseline",
            "match_points": 2.0,
            "margin": 100,
            "own_cash": 100,
        },
        {
            "seed": 1,
            "opponent": "botA",
            "seat": 0,
            "arm": "candidate",
            "match_points": 0.0,
            "margin": 0,
            "own_cash": 0,
        },
    ]
    with pytest.raises(runner.AggregationError, match="Invalid match_points: 2.0"):
        runner.aggregate_results(records)
