import json
import random
from pathlib import Path


def test_p2_v2_manifest_integrity():
    manifest_dir = Path("docs/experiments/agent_selection/p2_v2_market_slot_ordering")
    manifest_path = manifest_dir / "candidates.json"
    assert manifest_path.is_file(), f"Manifest file missing: {manifest_path}"

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["schema_version"] == 1
    assert manifest["engine"]["version"] == "1.32.7"

    # Check confirmation finalists
    finalists = manifest["design"]["confirmation_finalists"]
    assert finalists == [
        "prvsiyan_moon_counts_melons",
        "prvsiyan_global_sell_slot_challenger_reviewed",
    ]

    # Check seeds
    conf_seeds = manifest["design"]["confirmation_seeds"]
    assert len(conf_seeds) == 8
    assert len(set(conf_seeds)) == 8

    # Check disjointness against prior seeds
    p1_seeds = {
        256507559,
        336278987,
        522388730,
        972925858,
        300914001,
        590003991,
        738084249,
        739524397,
        811995954,
        846313352,
        896328793,
        966857091,
    }
    p2_seeds = {
        453711617,
        239535007,
        924705151,
        647805795,
        225915100,
        563508405,
        707885790,
        895731764,
        955397235,
        812292840,
        758639642,
        352111692,
    }
    prior_seeds = p1_seeds | p2_seeds
    assert not (
        set(conf_seeds) & prior_seeds
    ), "Confirmation seeds must be disjoint from prior seeds!"

    # Check RNG reproducibility
    rng_seed = manifest["design"]["seed_generation_rng_seed"]
    assert rng_seed == 20260928
    rng = random.Random(rng_seed)
    expected_seeds = []
    while len(expected_seeds) < 8:
        s = rng.randrange(100_000_000, 1_000_000_000)
        if s not in prior_seeds and s not in expected_seeds:
            expected_seeds.append(s)
    assert conf_seeds == expected_seeds

    # Verify candidate files and SHA256 digests exist
    candidates = {c["id"]: c for c in manifest["candidates"]}
    assert "prvsiyan_moon_counts_melons" in candidates
    assert "prvsiyan_global_sell_slot_challenger_reviewed" in candidates

    import hashlib

    for cid, c in candidates.items():
        rel_path = manifest_path.parent / c["source_path"]
        assert rel_path.is_file(), f"Missing source for candidate {cid}: {rel_path}"
        actual_hash = hashlib.sha256(rel_path.read_bytes()).hexdigest()
        assert actual_hash == c["source_sha256"], f"Hash mismatch for candidate {cid}"
        if "helper_path" in c:
            h_path = manifest_path.parent / c["helper_path"]
            assert h_path.is_file(), f"Missing helper for {cid}: {h_path}"
            assert hashlib.sha256(h_path.read_bytes()).hexdigest() == c["helper_sha256"]
