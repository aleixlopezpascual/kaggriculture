import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import scripts.run_agent_selection_tournament as script


def test_relative_path_resolution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Create a mock manifest file in a non-CWD directory
    manifest_dir = tmp_path / "docs" / "experiments" / "agent_selection"
    manifest_dir.mkdir(parents=True)
    manifest_rel_path = (
        Path("docs") / "experiments" / "agent_selection" / "candidates.json"
    )
    manifest_path = manifest_dir / "candidates.json"

    # Create a mock source relative to manifest
    rel_source_dir = manifest_dir / "sources" / "test_agent"
    rel_source_dir.mkdir(parents=True)
    rel_source_path = rel_source_dir / "main.py"
    rel_source_content = "def agent(obs, conf): pass\n"
    rel_source_path.write_text(rel_source_content, encoding="utf-8")
    rel_source_hash = hashlib.sha256(rel_source_content.encode("utf-8")).hexdigest()

    # Also create a mock source with an absolute path
    abs_source_dir = tmp_path / "absolute" / "test_agent"
    abs_source_dir.mkdir(parents=True)
    abs_source_path = abs_source_dir / "main.py"
    abs_source_content = "def agent2(obs, conf): pass\n"
    abs_source_path.write_text(abs_source_content, encoding="utf-8")
    abs_source_hash = hashlib.sha256(abs_source_content.encode("utf-8")).hexdigest()

    manifest_data = {
        "engine": {"version": "1.32.7"},
        "design": {"screening_seeds": [1]},
        "candidates": [
            {
                "id": "rel_agent",
                "source_path": "sources/test_agent/main.py",
                "source_sha256": rel_source_hash,
            },
            {
                "id": "abs_agent",
                "source_path": str(abs_source_path),
                "source_sha256": abs_source_hash,
            },
        ],
    }
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    args = argparse.Namespace(
        manifest=str(manifest_rel_path),
        phase="screening",
        seed=1,
        candidate_ids=None,
        finalists=None,
        output=None,
        force=False,
    )

    with (
        patch("scripts.run_agent_selection_tournament.check_engine_version"),
        patch(
            "scripts.run_agent_selection_tournament.run_match", return_value={}
        ) as mock_run_match,
        patch("sys.exit") as mock_exit,
    ):
        script.run_tournament(args)

        mock_exit.assert_not_called()
        assert mock_run_match.call_count == 2

        # Verify candidate paths were resolved correctly and passed to run_match
        expected_rel_path = str(rel_source_path.resolve())
        expected_abs_path = str(abs_source_path)

        for call in mock_run_match.call_args_list:
            _, agent_0, agent_1 = call.args
            for agent in (agent_0, agent_1):
                if agent["id"] == "rel_agent":
                    assert agent["path"] == expected_rel_path
                elif agent["id"] == "abs_agent":
                    assert agent["path"] == expected_abs_path
