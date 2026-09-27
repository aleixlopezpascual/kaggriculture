"""
Unit tests for P2 Market Slot Optimizer
=======================================
Verifies invariants required for the P2 Prvsiyan SELL-slot challenger:
1. Non-SELL and blank slot preservation
2. SELL multiset/quantity conservation
3. Wash-sell exclusion / pinning
4. Deterministic budget cap and deduplication
5. No-op when no positive improvement
6. Selection of a known better candidate
7. Safe exception handling
"""

import collections

from scripts.p2_market_slot_optimizer import (
    find_eligible_sell_indices,
    find_wash_items,
    optimize_sell_slots,
)


def test_wash_sell_exclusion():
    """Verify wash sales (item bought via BUY_PRODUCT) are excluded."""
    orders = [
        ["BUY_PRODUCT", "FERTILIZER", 2],
        ["SELL", "FERTILIZER", 5],  # Wash sell -> pinned
        ["SELL", "WHEAT", 10],  # Eligible
        ["BUY_PRODUCT", "WHEAT", 1],  # Wash item -> makes WHEAT wash too!
        ["SELL", "MELON", 3],  # Eligible
    ]
    wash_items = find_wash_items(orders)
    assert wash_items == {"FERTILIZER", "WHEAT"}

    eligible = find_eligible_sell_indices(orders)
    # Only index 4 ("SELL", "MELON", 3) is non-wash SELL
    assert eligible == [4]


def test_non_sell_and_blank_slot_preservation():
    """Verify non-SELL orders and blank slots remain at original indices."""
    orders = [
        None,
        [],
        ["BUY_SEED", "CARROT", 3],
        ["SELL", "MELON", 5],  # Eligible (idx 3)
        ["HIRE"],
        ["BUY_LAND"],
        ["BUY_PRODUCT", "WHEAT", 2],
        ["SELL", "WHEAT", 4],  # Wash sell -> pinned (idx 7)
        ["SELL", "CARROT", 8],  # Eligible (idx 8)
        None,
    ]
    eligible = find_eligible_sell_indices(orders)
    assert eligible == [3, 8]

    # Scoring callback that strongly prefers swapping MELON and CARROT
    def scoring_callback(cand):
        # Prefer CARROT at index 3, MELON at index 8
        if cand[3] == ["SELL", "CARROT", 8] and cand[8] == ["SELL", "MELON", 5]:
            return 10.0
        return 0.0

    best_orders, stats = optimize_sell_slots(orders, eligible, scoring_callback)

    assert stats["gain"] == 10.0
    assert stats["changed_slots"] == 2
    assert len(best_orders) == len(orders)

    # All non-eligible slots must be preserved exactly
    assert best_orders[0] is None
    assert best_orders[1] == []
    assert best_orders[2] == ["BUY_SEED", "CARROT", 3]
    assert best_orders[4] == ["HIRE"]
    assert best_orders[5] == ["BUY_LAND"]
    assert best_orders[6] == ["BUY_PRODUCT", "WHEAT", 2]
    assert best_orders[7] == ["SELL", "WHEAT", 4]  # Wash sell pinned
    assert best_orders[9] is None

    # Swapped positions
    assert best_orders[3] == ["SELL", "CARROT", 8]
    assert best_orders[8] == ["SELL", "MELON", 5]


def test_sell_multiset_and_quantity_conservation():
    """Verify multiset of SELL items and quantities is conserved."""
    orders = [
        ["SELL", "TOMATO", 12],
        ["SELL", "MELON", 7],
        ["BUY_SEED", "TOMATO", 1],
        ["SELL", "CARROT", 20],
        ["SELL", "STRAWBERRY", 4],
    ]
    eligible = find_eligible_sell_indices(orders)
    assert eligible == [0, 1, 3, 4]

    # Scoring callback that prefers reverse order
    def scoring_callback(cand):
        sells = [cand[i][1] for i in eligible]
        if sells == ["STRAWBERRY", "CARROT", "MELON", "TOMATO"]:
            return 50.0
        return 1.0

    best_orders, stats = optimize_sell_slots(orders, eligible, scoring_callback)
    assert stats["gain"] == 49.0

    orig_sells = collections.Counter(tuple(orders[i]) for i in eligible)
    cand_sells = collections.Counter(tuple(best_orders[i]) for i in eligible)
    assert orig_sells == cand_sells


def test_deterministic_budget_cap_and_deduplication():
    """Verify deduplication skips redundant permutations and budget caps."""
    # 1. Identical orders deduplication:
    # All 3 eligible sells are identical -> 3! = 6 permutations, but only 1
    # unique ordering.
    orders_dup = [
        ["SELL", "MELON", 5],
        ["SELL", "MELON", 5],
        ["SELL", "MELON", 5],
    ]
    eligible_dup = find_eligible_sell_indices(orders_dup)
    assert len(eligible_dup) == 3

    eval_calls = 0

    def counting_callback(cand):
        nonlocal eval_calls
        eval_calls += 1
        return 0.0

    best_orders, stats = optimize_sell_slots(
        orders_dup, eligible_dup, counting_callback, budget=100
    )
    # The base_score is evaluated once, and 0 candidate permutations are
    # scored because all are identical to base!
    assert stats["evals"] == 0
    assert stats["budget_hits"] == 0
    assert eval_calls == 1  # only base_score

    # 2. Strict budget cap on large search space:
    # 6 distinct items -> 6! = 720 permutations (719 non-base)
    distinct_items = [
        "WHEAT",
        "CARROT",
        "TOMATO",
        "STRAWBERRY",
        "MELON",
        "EGG",
    ]
    orders_large = [["SELL", item, i + 1] for i, item in enumerate(distinct_items)]
    eligible_large = find_eligible_sell_indices(orders_large)

    eval_count = 0

    def budget_callback(cand):
        nonlocal eval_count
        eval_count += 1
        return float(eval_count)

    budget_limit = 45
    best_orders, stats = optimize_sell_slots(
        orders_large, eligible_large, budget_callback, budget=budget_limit
    )
    assert stats["evals"] == budget_limit
    assert stats["budget_hits"] == 1
    # Total calls = 1 (base_score) + budget_limit (candidates)
    assert eval_count == 1 + budget_limit

    # 3. Determinism check: running twice yields identical evaluation count
    # and ordering
    run1_evals = []
    run2_evals = []

    def cb1(cand):
        run1_evals.append([list(c) for c in cand])
        return 0.0

    def cb2(cand):
        run2_evals.append([list(c) for c in cand])
        return 0.0

    optimize_sell_slots(orders_large, eligible_large, cb1, budget=20)
    optimize_sell_slots(orders_large, eligible_large, cb2, budget=20)

    assert len(run1_evals) == len(run2_evals) == 21  # 1 base + 20 cands
    assert run1_evals == run2_evals


def test_no_op_when_no_positive_improvement():
    """Verify no candidate is adopted if gain is <= 0.5 or non-positive."""
    orders = [
        ["SELL", "WHEAT", 10],
        ["SELL", "CARROT", 5],
        ["SELL", "TOMATO", 3],
    ]
    eligible = find_eligible_sell_indices(orders)

    # 1. All candidates give negative or zero gain
    def zero_gain_callback(cand):
        return 100.0  # Identical score to base

    best_orders, stats = optimize_sell_slots(orders, eligible, zero_gain_callback)
    assert best_orders == orders
    assert stats["gain"] == 0.0
    assert stats["changed_slots"] == 0

    # 2. Candidate gives +0.4 gain (below the 0.5 threshold)
    def small_gain_callback(cand):
        if cand[0][1] == "CARROT":
            return 100.4  # +0.4 improvement
        return 100.0

    best_orders, stats = optimize_sell_slots(
        orders, eligible, small_gain_callback, min_gain=0.5
    )
    assert best_orders == orders
    assert stats["gain"] == 0.0
    assert stats["changed_slots"] == 0


def test_selection_of_known_better_candidate_and_stable_tie_breaking():
    """Verify candidate with gain > 0.5 is selected with stable tie-breaking."""
    orders = [
        ["SELL", "A", 1],
        ["SELL", "B", 2],
        ["SELL", "C", 3],
    ]
    eligible = [0, 1, 2]

    # Two permutations (B, A, C) and (C, A, B) both yield +5.0 gain.
    # Deterministic permutations:
    # 0: (A, B, C) - base
    # 1: (A, C, B) -> +1.0
    # 2: (B, A, C) -> +5.0  (first encounter of +5.0)
    # 3: (B, C, A) -> +2.0
    # 4: (C, A, B) -> +5.0  (tie with +5.0, should NOT displace #2)
    # 5: (C, B, A) -> +0.0
    def tie_callback(cand):
        items = tuple(c[1] for c in cand)
        scores = {
            ("A", "B", "C"): 10.0,
            ("A", "C", "B"): 11.0,
            ("B", "A", "C"): 15.0,
            ("B", "C", "A"): 12.0,
            ("C", "A", "B"): 15.0,
            ("C", "B", "A"): 10.0,
        }
        return scores.get(items, 10.0)

    best_orders, stats = optimize_sell_slots(orders, eligible, tie_callback)
    assert stats["gain"] == 5.0
    assert stats["changed_slots"] == 2
    # First candidate with score 15.0 was ("B", "A", "C")
    assert [c[1] for c in best_orders] == ["B", "A", "C"]


def test_safe_exception_handling():
    """Verify exceptions in callback are caught safely without altering orders."""
    orders = [
        ["SELL", "A", 1],
        ["SELL", "B", 2],
    ]
    eligible = [0, 1]

    # Base score raises
    def crash_callback(cand):
        raise RuntimeError("Simulator crashed")

    best_orders, stats = optimize_sell_slots(orders, eligible, crash_callback)
    assert best_orders == orders
    assert stats["errors"] == 1
    assert stats["changed_slots"] == 0

    # Candidate evaluation raises
    call_count = 0

    def cand_crash_callback(cand):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise ValueError("Candidate invalid")
        return 10.0

    best_orders2, stats2 = optimize_sell_slots(orders, eligible, cand_crash_callback)
    assert best_orders2 == orders
    assert stats2["errors"] == 1
    assert stats2["changed_slots"] == 0


def test_p2_manifest_integrity():
    """Verify P2 manifest resolves candidates, helper, and disjoint seeds."""
    import hashlib
    import json
    import random
    from pathlib import Path

    p2_manifest_path = Path(
        "docs/experiments/agent_selection/p2_market_slot_ordering/candidates.json"
    )
    assert p2_manifest_path.exists(), "P2 candidates.json must exist"

    p1_manifest_path = Path(
        "docs/experiments/agent_selection/p1_refresh_2026-09-25/candidates.json"
    )
    assert p1_manifest_path.exists(), "P1 candidates.json must exist"

    p2_manifest = json.loads(p2_manifest_path.read_text(encoding="utf-8"))
    p1_manifest = json.loads(p1_manifest_path.read_text(encoding="utf-8"))

    # Snapshot timestamp must not be present (no new Kaggle snapshot fetched)
    assert (
        "snapshot_timestamp" not in p2_manifest
    ), "P2 manifest must not invent a snapshot_timestamp"

    # Check engine
    assert p2_manifest["engine"]["version"] == "1.32.7"

    # Check candidates count
    p2_candidates = p2_manifest["candidates"]
    assert len(p2_candidates) == 9

    # Check seeds disjointness and generation
    p2_screening_seeds = p2_manifest["design"]["screening_seeds"]
    p2_confirmation_seeds = p2_manifest["design"]["confirmation_seeds"]
    assert p2_screening_seeds == [453711617, 239535007, 924705151, 647805795]
    assert p2_confirmation_seeds == [
        225915100,
        563508405,
        707885790,
        895731764,
        955397235,
        812292840,
        758639642,
        352111692,
    ]

    # Verify RNG seed generation field and stream
    assert p2_manifest["design"]["seed_generation_rng_seed"] == 20260925
    assert "screening_rng_seed" not in p2_manifest["design"]
    assert "confirmation_rng_seed" not in p2_manifest["design"]

    rng = random.Random(20260925)
    expected_stream_seeds = [
        rng.randrange(100_000_000, 1_000_000_000) for _ in range(12)
    ]
    assert p2_screening_seeds + p2_confirmation_seeds == expected_stream_seeds

    assert p2_manifest["design"]["seed_disjointness_note"] == (
        "Screening and confirmation seeds are disjoint from P1 screening "
        "and confirmation seeds."
    )

    assert p2_manifest["design"]["confirmation_finalists"] == [
        "prvsiyan_moon_counts_melons",
        "prvsiyan_global_sell_slot_challenger",
    ]
    assert p2_manifest["design"]["finalist_selection_rule"] == (
        "Predeclared baseline-vs-challenger confirmation regardless of screening "
        "rank, and screening is exploratory."
    )

    p1_screening_seeds = set(p1_manifest["design"]["screening_seeds"])
    p1_confirmation_seeds = set(p1_manifest["design"]["confirmation_seeds"])
    all_p1_seeds = p1_screening_seeds | p1_confirmation_seeds

    all_p2_seeds = set(p2_screening_seeds) | set(p2_confirmation_seeds)
    assert len(all_p2_seeds) == 12, "All 12 P2 seeds must be unique"
    assert not (all_p2_seeds & all_p1_seeds), "P2 seeds must be disjoint from P1 seeds"

    # Verify 8 reused candidates match P1 hashes exactly and resolve to valid files
    p1_cand_map = {c["id"]: c for c in p1_manifest["candidates"]}
    p2_cand_map = {c["id"]: c for c in p2_candidates}

    assert "prvsiyan_global_sell_slot_challenger" in p2_cand_map
    assert "prvsiyan_moon_counts_melons" in p2_cand_map

    for cand_id, p1_cand in p1_cand_map.items():
        assert cand_id in p2_cand_map, f"P1 candidate {cand_id} must be in P2"
        p2_cand = p2_cand_map[cand_id]
        assert (
            p2_cand["source_sha256"] == p1_cand["source_sha256"]
        ), f"Hash mismatch for reused candidate {cand_id}"
        # Check path resolution relative to P2 manifest parent
        raw_path = Path(p2_cand["source_path"])
        resolved_path = (p2_manifest_path.parent / raw_path).resolve()
        assert (
            resolved_path.exists()
        ), f"Source path for {cand_id} does not resolve: {resolved_path}"
        # Verify SHA-256 on disk
        disk_hash = hashlib.sha256(resolved_path.read_bytes()).hexdigest()
        assert (
            disk_hash == p1_cand["source_sha256"]
        ), f"On-disk SHA-256 mismatch for {cand_id}"

    # Check challenger path resolution and helper verification
    challenger = p2_cand_map["prvsiyan_global_sell_slot_challenger"]
    challenger_resolved = (
        p2_manifest_path.parent / Path(challenger["source_path"])
    ).resolve()
    assert (
        challenger_resolved.exists()
    ), f"Challenger file must exist: {challenger_resolved}"

    assert "helper_path" in challenger
    assert "helper_sha256" in challenger
    helper_resolved = (
        p2_manifest_path.parent / Path(challenger["helper_path"])
    ).resolve()
    assert helper_resolved.exists(), f"Helper path does not resolve: {helper_resolved}"
    helper_disk_hash = hashlib.sha256(helper_resolved.read_bytes()).hexdigest()
    assert helper_disk_hash == challenger["helper_sha256"]
    assert (
        helper_disk_hash
        == "1b97d5cc9fff730b9c0e529e48018891536c516b8425ffc9b2e8ffc2038de94a"
    )


def test_p2_challenger_wrapper_telemetry_and_execution():
    """Verify challenger wrapper loads baseline, exposes telemetry, and runs."""
    import importlib.util
    import sys
    from pathlib import Path

    wrapper_path = Path(
        "docs/experiments/agent_selection/p2_market_slot_ordering"
        "/sources/prvsiyan_global_sell_slot_challenger/main.py"
    ).resolve()
    assert wrapper_path.exists()

    module_name = "test_p2_challenger_wrapper_mod"
    spec = importlib.util.spec_from_file_location(module_name, str(wrapper_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)

    agent_fn = getattr(mod, "agent", None)
    assert callable(agent_fn)
    assert callable(getattr(mod, "kaggle_submission_agent", None))

    # Verify telemetry attributes
    assert hasattr(agent_fn, "telemetry")
    assert isinstance(agent_fn.telemetry, dict)
    assert "p2_calls" in agent_fn.telemetry
    assert "p2_eligible_turns" in agent_fn.telemetry
    assert "p2_evals" in agent_fn.telemetry
    assert "p2_budget_hits" in agent_fn.telemetry
    assert "p2_changed_turns" in agent_fn.telemetry
    assert "p2_changed_slots" in agent_fn.telemetry
    assert "p2_model_gain" in agent_fn.telemetry
    assert "p2_errors" in agent_fn.telemetry
    assert hasattr(mod, "_P2_REPORT")

    # Step 0 dummy observation
    dummy_obs = {
        "step": 0,
        "player": 0,
        "farms": [
            {
                "unlocked_quadrants": 1,
                "money": 1000,
                "tiles": [[{} for _ in range(10)] for _ in range(10)],
            },
            {
                "unlocked_quadrants": 1,
                "money": 1000,
                "tiles": [[{} for _ in range(10)] for _ in range(10)],
            },
        ],
        "market": {
            "inventory": {
                "WHEAT": 10000,
                "CARROT": 10000,
                "TOMATO": 10000,
                "STRAWBERRY": 10000,
                "MELON": 10000,
                "EGG": 10000,
                "MILK": 10000,
                "WOOL": 10000,
                "FERTILIZER": 10000,
            },
            "params": {},
        },
    }
    dummy_conf = {
        "boardSize": 10,
        "turnsPerDay": 24,
        "shedCapacity": 100,
        "maxMarketOrdersPerTurn": 10,
    }

    action = agent_fn(dummy_obs, dummy_conf)
    assert isinstance(action, dict)
    assert agent_fn.telemetry["p2_calls"] == 1
    # Step 0 is not eligible (step < 216)
    assert agent_fn.telemetry["p2_eligible_turns"] == 0
    assert agent_fn.telemetry["p2_errors"] == 0


def test_p2_wrapper_exposes_baseline_reports_telemetry():
    """Verify wrapper merges baseline reports/stats dicts into telemetry."""
    import importlib.util
    import sys
    from pathlib import Path

    from scripts.run_agent_selection_tournament import capture_telemetry

    wrapper_path = Path(
        "docs/experiments/agent_selection/p2_market_slot_ordering"
        "/sources/prvsiyan_global_sell_slot_challenger/main.py"
    ).resolve()
    assert wrapper_path.exists()

    module_name = "test_p2_baseline_reports_mod"
    spec = importlib.util.spec_from_file_location(module_name, str(wrapper_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)

    # Initial telemetry exposed on agent before any call
    assert isinstance(mod.agent.telemetry, dict)
    # Check that baseline module reports exist as keys in agent.telemetry
    expected_reports = [
        "_V219_REPORT",
        "_V233_REPORT",
        "_R37_STATS",
        "_R46_REPORT",
        "_R51_INPUT_REPORT",
    ]
    for rep in expected_reports:
        assert (
            rep in mod.agent.telemetry
        ), f"Baseline report {rep} missing from agent.telemetry"
        assert isinstance(mod.agent.telemetry[rep], dict)
        assert mod.agent.telemetry[rep] is getattr(mod._BASELINE_MOD, rep)

    # Check that policy fields like failed-purchase/shortfall counters exist
    assert "sheep_purchase_shortfalls" in mod.agent.telemetry["_V233_REPORT"]
    assert "hire_shortfalls" in mod.agent.telemetry["_V219_REPORT"]

    # Execute dummy step 0
    dummy_obs = {
        "step": 0,
        "player": 0,
        "farms": [
            {
                "unlocked_quadrants": 1,
                "money": 1000,
                "tiles": [[{} for _ in range(10)] for _ in range(10)],
            },
            {
                "unlocked_quadrants": 1,
                "money": 1000,
                "tiles": [[{} for _ in range(10)] for _ in range(10)],
            },
        ],
        "market": {
            "inventory": {
                "WHEAT": 10000,
                "CARROT": 10000,
                "TOMATO": 10000,
                "STRAWBERRY": 10000,
                "MELON": 10000,
                "EGG": 10000,
                "MILK": 10000,
                "WOOL": 10000,
                "FERTILIZER": 10000,
            },
            "params": {},
        },
    }
    dummy_conf = {
        "boardSize": 10,
        "turnsPerDay": 24,
        "shedCapacity": 100,
        "maxMarketOrdersPerTurn": 10,
    }
    mod.agent(dummy_obs, dummy_conf)

    # After callback, verify baseline reports remain present as references
    for rep in expected_reports:
        assert (
            rep in mod.agent.telemetry
        ), f"Baseline report {rep} missing after callback"
        assert isinstance(mod.agent.telemetry[rep], dict)
        assert mod.agent.telemetry[rep] is getattr(mod._BASELINE_MOD, rep)

    # Verify capture_telemetry from runner captures reports and P2 telemetry
    captured = capture_telemetry(mod.agent, mod)
    for rep in expected_reports:
        assert rep in captured, f"capture_telemetry missed {rep}"
    assert "p2_calls" in captured


def test_p2_wrapper_distinct_baseline_instances_and_state_dicts():
    """Verify distinct wrapper imports create distinct modules and state dicts."""
    import importlib.util
    import sys
    from pathlib import Path

    wrapper_path = Path(
        "docs/experiments/agent_selection/p2_market_slot_ordering"
        "/sources/prvsiyan_global_sell_slot_challenger/main.py"
    ).resolve()
    assert wrapper_path.exists()

    name_1 = "test_p2_challenger_isolated_inst_1"
    name_2 = "test_p2_challenger_isolated_inst_2"

    try:
        spec_1 = importlib.util.spec_from_file_location(name_1, str(wrapper_path))
        assert spec_1 is not None and spec_1.loader is not None
        mod_1 = importlib.util.module_from_spec(spec_1)
        sys.modules[name_1] = mod_1
        spec_1.loader.exec_module(mod_1)

        spec_2 = importlib.util.spec_from_file_location(name_2, str(wrapper_path))
        assert spec_2 is not None and spec_2.loader is not None
        mod_2 = importlib.util.module_from_spec(spec_2)
        sys.modules[name_2] = mod_2
        spec_2.loader.exec_module(mod_2)

        # Baseline modules must be distinct objects
        assert mod_1._BASELINE_MOD is not mod_2._BASELINE_MOD
        assert mod_1._BASELINE_MOD.__name__ != mod_2._BASELINE_MOD.__name__
        assert name_1 in mod_1._BASELINE_MOD.__name__
        assert name_2 in mod_2._BASELINE_MOD.__name__

        # Baseline agents must be distinct callables
        assert mod_1._BASE_AGENT is not mod_2._BASE_AGENT

        # Baseline mutable state dicts must be distinct objects
        assert mod_1._RACE_STATE is not mod_2._RACE_STATE
        assert mod_1._BASELINE_MOD._V219_STATES is not mod_2._BASELINE_MOD._V219_STATES
        assert mod_1._BASELINE_MOD._V233_STATES is not mod_2._BASELINE_MOD._V233_STATES
        assert mod_1._BASELINE_MOD._V231_STATES is not mod_2._BASELINE_MOD._V231_STATES

        # Mutating state in mod_1 must not affect mod_2
        mod_1._RACE_STATE["mutation_test"] = 999
        assert "mutation_test" not in mod_2._RACE_STATE

        mod_1._BASELINE_MOD._V219_STATES["player_0"] = {"committed": True}
        assert "player_0" not in mod_2._BASELINE_MOD._V219_STATES

    finally:
        sys.modules.pop(name_1, None)
        sys.modules.pop(name_2, None)
        sys.modules.pop(f"{name_1}._prvsiyan_moon_counts_melons_frozen_baseline", None)
        sys.modules.pop(f"{name_2}._prvsiyan_moon_counts_melons_frozen_baseline", None)


def test_challenger_source_sha256_rejection_and_validation():
    """Verify placeholder hashes are rejected and validate challenger SHA."""
    import hashlib
    import json
    from pathlib import Path

    import pytest

    from scripts.run_agent_selection_tournament import verify_candidate

    p2_manifest_path = Path(
        "docs/experiments/agent_selection/p2_market_slot_ordering/candidates.json"
    )
    p2_manifest = json.loads(p2_manifest_path.read_text(encoding="utf-8"))
    challenger = next(
        c
        for c in p2_manifest["candidates"]
        if c["id"] == "prvsiyan_global_sell_slot_challenger"
    )
    challenger_path = (
        p2_manifest_path.parent / Path(challenger["source_path"])
    ).resolve()
    assert challenger_path.exists()

    # 1. Candidate verification must explicitly reject placeholder hashes
    placeholder_val = "PLACEHOLDER_PENDING_COMPUTATION_NO_SHELL_TOOL"
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        verify_candidate(str(challenger_path), placeholder_val)

    # 2. Check rejection logic on arbitrary placeholder strings
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        verify_candidate(str(challenger_path), "PLACEHOLDER")

    # 3. Check whether manifest's configured hash is a placeholder or concrete
    configured_sha = challenger["source_sha256"]
    is_placeholder = configured_sha.startswith("PLACEHOLDER")
    if is_placeholder:
        assert configured_sha == "PLACEHOLDER_PENDING_COMPUTATION_NO_SHELL_TOOL"
        # Must be rejected by verify_candidate
        with pytest.raises(ValueError, match="SHA256 mismatch"):
            verify_candidate(str(challenger_path), configured_sha)
    else:
        # When concrete SHA is set, it must match disk exactly
        actual_sha = hashlib.sha256(challenger_path.read_bytes()).hexdigest()
        assert configured_sha == actual_sha, (
            f"Configured SHA {configured_sha} does not match "
            f"actual on-disk SHA {actual_sha}"
        )
        assert len(configured_sha) == 64
        # verify_candidate must succeed
        loaded_code = verify_candidate(str(challenger_path), configured_sha)
        assert len(loaded_code) > 0


def test_p2_wrapper_resolve_helper_path_fallback(tmp_path, monkeypatch):
    """Verify _resolve_helper_path falls back to __file__ ancestry."""
    import importlib.util
    import sys
    from pathlib import Path

    wrapper_path = Path(
        "docs/experiments/agent_selection/p2_market_slot_ordering"
        "/sources/prvsiyan_global_sell_slot_challenger/main.py"
    ).resolve()
    assert wrapper_path.exists()

    module_name = "test_p2_helper_path_fallback_mod"
    spec = importlib.util.spec_from_file_location(module_name, str(wrapper_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)

        # 1. Change cwd to a temporary empty directory
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)

        # 2. Make _WORKSPACE_ROOT point to a nonexistent temp root
        fake_root = tmp_path / "nonexistent_workspace"
        monkeypatch.setattr(mod, "_WORKSPACE_ROOT", fake_root)

        # 3. Assert _resolve_helper_path() still resolves the repository's
        # scripts/p2_market_slot_optimizer.py via __file__ ancestry
        resolved = mod._resolve_helper_path()
        expected = wrapper_path.parents[6] / "scripts" / "p2_market_slot_optimizer.py"
        assert resolved == expected
        assert resolved.exists()
    finally:
        sys.modules.pop(module_name, None)
        sys.modules.pop(
            f"{module_name}._prvsiyan_moon_counts_melons_frozen_baseline", None
        )
