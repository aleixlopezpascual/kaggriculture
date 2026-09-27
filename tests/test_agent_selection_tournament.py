import hashlib
import json
from unittest.mock import MagicMock, patch

import pytest

import scripts.run_agent_selection_tournament as script


@pytest.fixture
def mock_manifest():
    return {
        "engine": {"version": "1.32.7"},
        "design": {"screening_seeds": [1, 2, 3], "confirmation_seeds": [4, 5, 6]},
        "candidates": [
            {
                "id": f"agent_{i}",
                "source_path": f"/dummy/path/agent_{i}.py",
                "source_sha256": f"hash_{i}",
            }
            for i in range(10)
        ],
    }


def test_engine_version_check():
    with (
        patch("importlib.metadata.version", return_value="1.0.0"),
        pytest.raises(SystemExit),
    ):
        script.check_engine_version()
    with patch("importlib.metadata.version", return_value="1.32.7"):
        script.check_engine_version()  # Should not raise


def test_screening_schedule(mock_manifest):
    candidates = mock_manifest["candidates"]
    schedule = script.generate_schedule(candidates, phase="screening", finalists=None)
    # 10 candidates -> 45 combinations * 2 seats = 90 matches
    assert len(schedule) == 90

    pair_counts = {}
    for match in schedule:
        pair = tuple(sorted([match["agent_0"], match["agent_1"]]))
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

    assert len(pair_counts) == 45
    assert all(count == 2 for count in pair_counts.values())


def test_confirmation_schedule(mock_manifest):
    candidates = mock_manifest["candidates"]
    finalists = ["agent_0", "agent_1"]
    schedule = script.generate_schedule(
        candidates, phase="confirmation", finalists=finalists
    )

    # agent_0 vs agent_1 (2 matches)
    # agent_0 vs 8 others (16 matches)
    # agent_1 vs 8 others (16 matches)
    # Total = 34 matches
    assert len(schedule) == 34

    pairs_in_schedule = {tuple(sorted([m["agent_0"], m["agent_1"]])) for m in schedule}
    assert tuple(sorted(["agent_0", "agent_1"])) in pairs_in_schedule
    for i in range(2, 10):
        assert tuple(sorted(["agent_0", f"agent_{i}"])) in pairs_in_schedule
        assert tuple(sorted(["agent_1", f"agent_{i}"])) in pairs_in_schedule


def test_hash_validation(tmp_path):
    p = tmp_path / "test.py"
    p.write_text("print('hello')", encoding="utf-8")
    h = hashlib.sha256(b"print('hello')").hexdigest()

    # Should pass
    source = script.verify_candidate(str(p), h)
    assert source == "print('hello')"

    # Should fail
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        script.verify_candidate(str(p), "wrong_hash")

    # Reject notebooks
    p_ipynb = tmp_path / "test.ipynb"
    p_ipynb.write_text("{}", encoding="utf-8")
    with pytest.raises(script.TournamentError, match="cannot be a notebook"):
        script.verify_candidate(str(p_ipynb), h)

    # Reject .txt
    p_txt = tmp_path / "test.txt"
    p_txt.write_text("print('hello')", encoding="utf-8")
    with pytest.raises(script.TournamentError):
        script.verify_candidate(str(p_txt), h)


def test_generate_schedule_invalid_phase(mock_manifest):
    with pytest.raises(script.TournamentError, match="Unknown phase"):
        script.generate_schedule(mock_manifest["candidates"], phase="invalid")


def test_generate_schedule_rejects_duplicates(mock_manifest):
    # Duplicate candidate IDs
    bad_candidates = mock_manifest["candidates"] + [mock_manifest["candidates"][0]]
    with pytest.raises(ValueError, match="Duplicate candidate IDs"):
        script.generate_schedule(bad_candidates, phase="screening")


def test_generate_schedule_rejects_duplicate_finalists(mock_manifest):
    with pytest.raises(ValueError, match="Duplicate finalists"):
        script.generate_schedule(
            mock_manifest["candidates"],
            phase="confirmation",
            finalists=["agent_0", "agent_0"],
        )


def test_generate_schedule_rejects_self_matches(mock_manifest):
    schedule = script.generate_schedule(mock_manifest["candidates"], phase="screening")
    for match in schedule:
        assert match["agent_0"] != match["agent_1"], "Self-match detected"


def test_generate_schedule_confirmation_invalid_finalists(mock_manifest):
    with pytest.raises(script.TournamentError, match="exactly two"):
        script.generate_schedule(
            mock_manifest["candidates"], phase="confirmation", finalists=["agent_0"]
        )

    with pytest.raises(script.TournamentError, match="valid candidate IDs"):
        script.generate_schedule(
            mock_manifest["candidates"],
            phase="confirmation",
            finalists=["agent_0", "agent_999"],
        )


def test_compute_agent_stats():
    callbacks = [
        {"elapsed": 0.050, "error": None},
        {"elapsed": 0.150, "error": None},
        {"elapsed": 0.020, "error": None},
    ]
    stats = script.compute_agent_stats(callbacks)
    assert stats["calls"] == 3
    assert stats["over_100ms"] == 1
    assert stats["max_ms"] == 150.0


def test_compute_agent_stats_callback_error():
    callbacks = [
        {"elapsed": 0.050, "error": None},
        {"elapsed": 0.150, "error": "Traceback..."},
        {"elapsed": 0.020, "error": None},
    ]
    stats = script.compute_agent_stats(callbacks)
    assert stats["errors"] == 1


def test_wrap_agent_monotonic_timing_success():
    dummy_agent = MagicMock(return_value="STEP_ACTION")
    wrapped, callbacks = script.wrap_agent(dummy_agent)

    def forbid_wall_clock(*args, **kwargs):
        raise AssertionError(
            "Wall-clock time.time() was called for interval measurement "
            "instead of time.perf_counter()"
        )

    with (
        patch(
            "scripts.run_agent_selection_tournament.time.perf_counter",
            side_effect=[100.0, 100.045],
        ) as mock_perf,
        patch(
            "scripts.run_agent_selection_tournament.time.time",
            side_effect=forbid_wall_clock,
        ),
    ):
        action = wrapped({"step": 1}, {"seed": 42})

    assert action == "STEP_ACTION"
    assert len(callbacks) == 1
    assert pytest.approx(callbacks[0]["elapsed"], rel=1e-6) == 0.045
    assert callbacks[0]["error"] is None
    assert mock_perf.call_count == 2


def test_wrap_agent_monotonic_timing_exception():
    def failing_agent(obs, config):
        raise RuntimeError("Agent simulation failure")

    wrapped, callbacks = script.wrap_agent(failing_agent)

    def forbid_wall_clock(*args, **kwargs):
        raise AssertionError(
            "Wall-clock time.time() was called for interval measurement "
            "instead of time.perf_counter()"
        )

    with (
        patch(
            "scripts.run_agent_selection_tournament.time.perf_counter",
            side_effect=[200.0, 200.085],
        ) as mock_perf,
        patch(
            "scripts.run_agent_selection_tournament.time.time",
            side_effect=forbid_wall_clock,
        ),
        pytest.raises(RuntimeError, match="Agent simulation failure"),
    ):
        wrapped({"step": 2}, {})

    assert len(callbacks) == 1
    assert pytest.approx(callbacks[0]["elapsed"], rel=1e-6) == 0.085
    assert "Agent simulation failure" in callbacks[0]["error"]
    assert mock_perf.call_count == 2


def test_validate_seed():
    manifest = {
        "design": {"screening_seeds": [1, 2, 3], "confirmation_seeds": [4, 5, 6]}
    }

    # Should not raise
    script.validate_seed(1, "screening", manifest)
    script.validate_seed(5, "confirmation", manifest)

    # Unplanned seed
    with pytest.raises(ValueError, match="not listed in manifest"):
        script.validate_seed(99, "screening", manifest)

    # Wrong phase
    with pytest.raises(ValueError, match="not listed in manifest"):
        script.validate_seed(4, "screening", manifest)

    # Duplicates in config
    bad_manifest = {"design": {"screening_seeds": [1, 1, 2]}}
    with pytest.raises(ValueError, match="Duplicate seeds"):
        script.validate_seed(2, "screening", bad_manifest)


@patch("scripts.run_agent_selection_tournament.load_agent")
@patch("scripts.run_agent_selection_tournament.kaggle_environments")
def test_run_match(mock_env, mock_load):
    mock_fn_0, mock_mod_0 = MagicMock(), MagicMock()
    mock_fn_1, mock_mod_1 = MagicMock(), MagicMock()

    mock_mod_0.agent_REPORT = {"test": 123}

    mock_load.side_effect = [(mock_fn_0, mock_mod_0), (mock_fn_1, mock_mod_1)]

    mock_instance = MagicMock()
    mock_env.make.return_value = mock_instance
    mock_instance.steps = [
        [{}, {}],
        [
            {"reward": 100, "status": "DONE", "info": {}},
            {"reward": 50, "status": "DONE", "info": {}},
        ],
    ]

    agent_0_info = {"id": "a0", "source": "code", "path": "path/a0.py", "hash": "h0"}
    agent_1_info = {"id": "a1", "source": "code", "path": "path/a1.py", "hash": "h1"}

    res = script.run_match(42, agent_0_info, agent_1_info)

    assert res["seed"] == 42
    assert res["valid_match"] is True
    assert res["agent_0"]["id"] == "a0"
    assert res["agent_1"]["id"] == "a1"
    assert res["agent_0"]["coins"] == 100
    assert res["agent_1"]["coins"] == 50
    assert res["agent_0"]["margin"] == 50
    assert res["agent_0"]["points"] == 1.0
    assert res["agent_1"]["points"] == 0.0
    assert res["agent_0"]["outcome"] == "win"
    assert res["agent_1"]["outcome"] == "loss"
    assert "agent_REPORT" in res["agent_0"]["telemetry"]


@patch("scripts.run_agent_selection_tournament.load_agent")
@patch("scripts.run_agent_selection_tournament.kaggle_environments")
def test_run_match_forfeit_on_error(mock_env, mock_load):
    mock_load.return_value = (MagicMock(), MagicMock())
    mock_instance = MagicMock()
    mock_env.make.return_value = mock_instance

    # 0 is DONE with 10 coins, 1 is ERROR with 10 coins
    mock_instance.steps = [
        [{}, {}],
        [
            {"reward": 10, "status": "DONE", "info": {}},
            {"reward": 10, "status": "ERROR", "info": {}},
        ],
    ]
    agent_info_0 = {"id": "a0", "source": "code", "path": "path", "hash": "h"}
    agent_info_1 = {"id": "a1", "source": "code", "path": "path", "hash": "h"}
    res = script.run_match(1, agent_info_0, agent_info_1)
    assert res["valid_match"] is True
    assert res["agent_0"]["outcome"] == "win"
    assert res["agent_1"]["outcome"] == "loss"
    assert res["agent_0"]["points"] == 1.0
    assert res["agent_1"]["points"] == 0.0


@patch("scripts.run_agent_selection_tournament.load_agent")
@patch("scripts.run_agent_selection_tournament.kaggle_environments")
def test_run_match_double_error_is_invalid(mock_env, mock_load):
    mock_load.return_value = (MagicMock(), MagicMock())
    mock_instance = MagicMock()
    mock_env.make.return_value = mock_instance

    mock_instance.steps = [
        [{}, {}],
        [
            {"reward": 10, "status": "ERROR", "info": {}},
            {"reward": 10, "status": "ERROR", "info": {}},
        ],
    ]
    agent_info_0 = {"id": "a0", "source": "code", "path": "path", "hash": "h"}
    agent_info_1 = {"id": "a1", "source": "code", "path": "path", "hash": "h"}
    res = script.run_match(1, agent_info_0, agent_info_1)
    assert res["valid_match"] is False
    assert res["agent_0"]["outcome"] == "invalid"
    assert res["agent_1"]["outcome"] == "invalid"
    assert res["agent_0"]["points"] is None
    assert res["agent_1"]["points"] is None


@patch("scripts.run_agent_selection_tournament.load_agent")
@patch("scripts.run_agent_selection_tournament.kaggle_environments")
def test_run_match_clean_tie(mock_env, mock_load):
    mock_load.return_value = (MagicMock(), MagicMock())
    mock_instance = MagicMock()
    mock_env.make.return_value = mock_instance

    mock_instance.steps = [
        [{}, {}],
        [
            {"reward": 10, "status": "DONE", "info": {}},
            {"reward": 10, "status": "DONE", "info": {}},
        ],
    ]
    agent_info_0 = {"id": "a0", "source": "code", "path": "path", "hash": "h"}
    agent_info_1 = {"id": "a1", "source": "code", "path": "path", "hash": "h"}
    res = script.run_match(1, agent_info_0, agent_info_1)
    assert res["valid_match"] is True
    assert res["agent_0"]["outcome"] == "tie"
    assert res["agent_1"]["outcome"] == "tie"
    assert res["agent_0"]["points"] == 0.5
    assert res["agent_1"]["points"] == 0.5


@patch("scripts.run_agent_selection_tournament.load_agent")
@patch("scripts.run_agent_selection_tournament.kaggle_environments")
def test_run_match_monotonic_duration(mock_env, mock_load):
    mock_fn_0, mock_mod_0 = MagicMock(), MagicMock()
    mock_fn_1, mock_mod_1 = MagicMock(), MagicMock()
    mock_load.side_effect = [(mock_fn_0, mock_mod_0), (mock_fn_1, mock_mod_1)]

    mock_instance = MagicMock()
    mock_env.make.return_value = mock_instance
    mock_instance.steps = [
        [{}, {}],
        [
            {"reward": 100, "status": "DONE", "info": {}},
            {"reward": 50, "status": "DONE", "info": {}},
        ],
    ]

    agent_0_info = {"id": "a0", "source": "code", "path": "path/a0.py", "hash": "h0"}
    agent_1_info = {"id": "a1", "source": "code", "path": "path/a1.py", "hash": "h1"}

    def forbid_wall_clock(*args, **kwargs):
        raise AssertionError(
            "Wall-clock time.time() was called for interval measurement "
            "instead of time.perf_counter()"
        )

    with (
        patch(
            "scripts.run_agent_selection_tournament.time.perf_counter",
            side_effect=[500.0, 503.25],
        ) as mock_perf,
        patch(
            "scripts.run_agent_selection_tournament.time.time",
            side_effect=forbid_wall_clock,
        ),
    ):
        res = script.run_match(42, agent_0_info, agent_1_info)

    assert res["duration_sec"] == 3.25
    assert mock_perf.call_count == 2


@patch("scripts.run_agent_selection_tournament.load_agent")
def test_run_match_monotonic_duration_on_runner_exception(mock_load):
    mock_load.side_effect = RuntimeError("Failed to load agent")

    agent_0_info = {"id": "a0", "source": "code", "path": "path/a0.py", "hash": "h0"}
    agent_1_info = {"id": "a1", "source": "code", "path": "path/a1.py", "hash": "h1"}

    def forbid_wall_clock(*args, **kwargs):
        raise AssertionError(
            "Wall-clock time.time() was called for interval measurement "
            "instead of time.perf_counter()"
        )

    with (
        patch(
            "scripts.run_agent_selection_tournament.time.perf_counter",
            side_effect=[1000.0, 1001.50],
        ) as mock_perf,
        patch(
            "scripts.run_agent_selection_tournament.time.time",
            side_effect=forbid_wall_clock,
        ),
    ):
        res = script.run_match(42, agent_0_info, agent_1_info)

    assert res["valid_match"] is False
    assert res["scoring_basis"] == "invalid"
    assert res["duration_sec"] == 1.50
    assert mock_perf.call_count == 2


def test_aggregate_results_missing_planned_seed(tmp_path):
    p1 = tmp_path / "1.json"
    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1, 2],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
        ],
    }
    p1.write_text(json.dumps(res_1))
    out = tmp_path / "out.json"
    with pytest.raises(
        ValueError,
        match=r"Not all planned seeds were provided.*Missing planned seed\(s\): \[2\]",
    ):
        script.aggregate_results([str(p1)], "screening", str(out), force=False)


def test_aggregate_results_duplicate_planned_seeds(tmp_path):
    p1 = tmp_path / "1.json"
    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1, 1],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
        ],
    }
    p1.write_text(json.dumps(res_1))
    out = tmp_path / "out.json"
    with pytest.raises(
        ValueError,
        match=r"Duplicate values found in planned_seeds",
    ):
        script.aggregate_results([str(p1)], "screening", str(out), force=False)


def test_aggregate_results(tmp_path):
    p1 = tmp_path / "1.json"

    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
        ],
    }

    p1.write_text(json.dumps(res_1))

    out = tmp_path / "out.json"
    script.aggregate_results([str(p1)], "screening", str(out), force=False)


def test_aggregate_results_pairwise_stats_and_seats(tmp_path):
    p1 = tmp_path / "1.json"

    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1.0,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0.0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "b",
                    "coins": 5,
                    "margin": -5,
                    "outcome": "loss",
                    "points": 0.0,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "a",
                    "coins": 10,
                    "margin": 5,
                    "outcome": "win",
                    "points": 1.0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
        ],
    }

    p1.write_text(json.dumps(res_1))

    out = tmp_path / "out.json"
    script.aggregate_results([str(p1)], "screening", str(out), force=False)

    out_data = json.loads(out.read_text())
    a_stats = out_data["agent_summaries"]["a"]
    assert a_stats["wins"] == 2
    assert a_stats["losses"] == 0
    assert a_stats["ties"] == 0

    assert "pairwise" in a_stats
    assert a_stats["pairwise"]["b"]["wins"] == 2
    assert a_stats["pairwise"]["b"]["losses"] == 0
    assert a_stats["pairwise"]["b"]["ties"] == 0
    assert a_stats["pairwise"]["b"]["points_rate"] == 1.0


def test_aggregate_results_missing_seat(tmp_path):
    p1 = tmp_path / "1.json"
    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            }
        ],
    }
    p1.write_text(json.dumps(res_1))

    out = tmp_path / "out.json"
    with pytest.raises(ValueError, match="Results count"):
        script.aggregate_results([str(p1)], "screening", str(out), force=False)


def test_aggregate_results_rejects_mixed_duplicate_seeds(tmp_path):
    p1 = tmp_path / "1.json"
    p2 = tmp_path / "2.json"

    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "coins",
                "agent_0": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "loss",
                    "points": 0,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "win",
                    "points": 1,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
        ],
    }
    p1.write_text(json.dumps(res_1))
    p2.write_text(json.dumps(res_1))

    out = tmp_path / "out.json"
    with pytest.raises(ValueError, match="Duplicate or mixed seeds"):
        script.aggregate_results([str(p1), str(p2)], "screening", str(out), force=False)


def test_aggregate_results_confirmation_bootstrap(tmp_path):
    p_files = []
    for seed in range(10):
        a_points, b_points = (1.0, 0.0) if seed < 7 else (0.0, 1.0)
        a_coins, b_coins = (10.0, 0.0) if seed < 7 else (0.0, 10.0)
        a_margin, b_margin = (10.0, -10.0) if seed < 7 else (-10.0, 10.0)
        res = {
            "phase": "confirmation",
            "finalists": ["a", "b"],
            "manifest_hash": "abc",
            "engine_version": "1.32.7",
            "seed": seed,
            "candidate_ids": ["a", "b"],
            "planned_seeds": list(range(10)),
            "smoke_test": False,
            "planned_games": 2,
            "completed_games": 2,
            "results": [
                {
                    "seed": seed,
                    "valid_match": True,
                    "scoring_basis": "coins",
                    "agent_0": {
                        "id": "a",
                        "coins": a_coins,
                        "margin": a_margin,
                        "outcome": "win" if a_points else "loss",
                        "points": a_points,
                        "terminal_status": "DONE",
                        "error": "",
                    },
                    "agent_1": {
                        "id": "b",
                        "coins": b_coins,
                        "margin": b_margin,
                        "outcome": "loss" if a_points else "win",
                        "points": b_points,
                        "terminal_status": "DONE",
                        "error": "",
                    },
                },
                {
                    "seed": seed,
                    "valid_match": True,
                    "scoring_basis": "coins",
                    "agent_0": {
                        "id": "b",
                        "coins": b_coins,
                        "margin": b_margin,
                        "outcome": "loss" if a_points else "win",
                        "points": b_points,
                        "terminal_status": "DONE",
                        "error": "",
                    },
                    "agent_1": {
                        "id": "a",
                        "coins": a_coins,
                        "margin": a_margin,
                        "outcome": "win" if a_points else "loss",
                        "points": a_points,
                        "terminal_status": "DONE",
                        "error": "",
                    },
                },
            ],
        }
        p = tmp_path / f"{seed}.json"
        p.write_text(json.dumps(res))
        p_files.append(str(p))

    out = tmp_path / "out.json"
    script.aggregate_results(p_files, "confirmation", str(out), force=False)

    out_data = json.loads(out.read_text())
    assert "confirmation_stats" in out_data
    conf_stats = out_data["confirmation_stats"]
    assert "point_rate_diff" in conf_stats
    assert "bootstrap_95_ci" in conf_stats

    ci = conf_stats["bootstrap_95_ci"]
    assert len(ci) == 2
    assert ci[0] <= conf_stats["point_rate_diff"] <= ci[1]


def test_aggregate_results_invalid_match_wrong_scoring_basis(tmp_path):
    p1 = tmp_path / "1.json"
    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": False,
                "scoring_basis": "some_other_value",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "invalid",
                    "points": None,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "invalid",
                    "points": None,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
            {
                "seed": 1,
                "valid_match": False,
                "scoring_basis": "some_other_value",
                "agent_0": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "invalid",
                    "points": None,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "invalid",
                    "points": None,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
        ],
    }
    p1.write_text(json.dumps(res_1))

    out = tmp_path / "out.json"
    with pytest.raises(ValueError):
        script.aggregate_results([str(p1)], "screening", str(out), force=False)


def test_aggregate_results_forfeit_logic(tmp_path):
    p1 = tmp_path / "1.json"
    res_1 = {
        "phase": "screening",
        "manifest_hash": "abc",
        "engine_version": "1.32.7",
        "seed": 1,
        "candidate_ids": ["a", "b"],
        "planned_seeds": [1],
        "smoke_test": False,
        "planned_games": 2,
        "completed_games": 2,
        "results": [
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "forfeit",
                "agent_0": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "loss",
                    "points": 0.0,
                    "terminal_status": "ERROR",
                    "error": "Some trace",
                },
                "agent_1": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "win",
                    "points": 1.0,
                    "terminal_status": "DONE",
                    "error": "",
                },
            },
            {
                "seed": 1,
                "valid_match": True,
                "scoring_basis": "forfeit",
                "agent_0": {
                    "id": "b",
                    "coins": 0,
                    "margin": -10,
                    "outcome": "win",
                    "points": 1.0,
                    "terminal_status": "DONE",
                    "error": "",
                },
                "agent_1": {
                    "id": "a",
                    "coins": 10,
                    "margin": 10,
                    "outcome": "loss",
                    "points": 0.0,
                    "terminal_status": "ERROR",
                    "error": "Timeout",
                },
            },
        ],
    }
    p1.write_text(json.dumps(res_1))

    out = tmp_path / "out.json"
    # Should not raise
    script.aggregate_results([str(p1)], "screening", str(out), force=False)
