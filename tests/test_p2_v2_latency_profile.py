import json
from pathlib import Path


def test_p2_v2_profile_shards_validity():
    profile_dir = Path("docs/experiments/agent_selection/p2_v2_market_slot_ordering")
    seeds = [838084248, 690003990]

    for s in seeds:
        shard_path = profile_dir / f"profile_monotonic_seed_{s}.json"
        assert shard_path.is_file(), f"Profile shard missing: {shard_path}"
        with shard_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert data["seed"] == s
        assert data["phase"] == "confirmation"
        assert len(data["results"]) == 30

        for r in data["results"]:
            assert r["valid_match"] is True
            assert r["agent_0"]["terminal_status"] == "DONE"
            assert r["agent_1"]["terminal_status"] == "DONE"
            assert not r["agent_0"]["error"]
            assert not r["agent_1"]["error"]
            assert r["agent_0"]["stats"]["calls"] == 719
            assert r["agent_1"]["stats"]["calls"] == 719
