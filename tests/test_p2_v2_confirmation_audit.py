import json
from pathlib import Path


def test_p2_v2_confirmation_audit():
    manifest_path = Path(
        "docs/experiments/agent_selection/p2_v2_market_slot_ordering/candidates.json"
    )
    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    seeds = manifest["design"]["confirmation_seeds"]
    assert len(seeds) == 8

    total_matches = 0
    exp_dir = manifest_path.parent

    for s in seeds:
        p = exp_dir / f"confirmation_seed_{s}.json"
        assert p.is_file(), f"Confirmation shard missing: {p}"
        with p.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data["seed"] == s
        assert len(data["results"]) == 30
        for r in data["results"]:
            assert r["valid_match"] is True
            assert r["agent_0"]["terminal_status"] == "DONE"
            assert r["agent_1"]["terminal_status"] == "DONE"
            assert not r["agent_0"]["error"]
            assert not r["agent_1"]["error"]
            assert r["agent_0"]["stats"]["calls"] == 719
            assert r["agent_1"]["stats"]["calls"] == 719
        total_matches += len(data["results"])

    assert total_matches == 240

    summary_path = exp_dir / "confirmation_summary.json"
    assert summary_path.is_file(), f"Summary missing: {summary_path}"
    with summary_path.open(encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["phase"] == "confirmation"
    assert summary["total_matches"] == 240
    assert len(summary["seeds_aggregated"]) == 8
