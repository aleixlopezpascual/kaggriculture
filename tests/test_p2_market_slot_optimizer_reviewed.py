import importlib
import importlib.util
import itertools
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

V1_HELPER_PATH = Path("scripts/p2_market_slot_optimizer.py")
V2_HELPER_PATH = Path("scripts/p2_market_slot_optimizer_reviewed.py")
V2_CHALLENGER_PATH = Path(
    "docs/experiments/agent_selection/p2_market_slot_ordering/"
    "sources/prvsiyan_global_sell_slot_challenger_reviewed/main.py"
)


def load_v1_helper():
    import scripts.p2_market_slot_optimizer as v1

    return v1


def load_v2_helper():
    import scripts.p2_market_slot_optimizer_reviewed as v2

    return v2


def test_missing_quantity_v1():
    """V1 wrongly accepts SELL orders missing a quantity."""
    v1 = load_v1_helper()
    orders = [["SELL", "WHEAT"]]
    indices = v1.find_eligible_sell_indices(orders)
    assert indices == [0], "V1 mistakenly accepts missing quantity"


def test_many_identical_orders_v1():
    """V1 calls itertools.permutations which hangs on many identical elements."""
    v1 = load_v1_helper()
    orders = [["SELL", "WHEAT", 10]] * 10
    indices = list(range(10))

    def scoring_callback(cand):
        return 1.0

    def fail_immediately(*args, **kwargs):
        raise RuntimeError("V1 correctly hit the monkeypatch without hanging")

    with (
        patch("itertools.permutations", side_effect=fail_immediately),
        pytest.raises(RuntimeError, match="monkeypatch"),
    ):
        v1.optimize_sell_slots(orders, indices, scoring_callback, budget=800)


def test_import_shadowing_v1():
    """V1 uses standard import which can be shadowed."""
    fake_mod = types.ModuleType("scripts.p2_market_slot_optimizer")
    fake_mod.fake_marker = True

    orig_mod = sys.modules.get("scripts.p2_market_slot_optimizer")
    sys.modules["scripts.p2_market_slot_optimizer"] = fake_mod

    try:
        with pytest.raises(ImportError):
            importlib.import_module(
                "docs.experiments.agent_selection.p2_market_slot_ordering."
                "sources.prvsiyan_global_sell_slot_challenger.main"
            )
    finally:
        if orig_mod is not None:
            sys.modules["scripts.p2_market_slot_optimizer"] = orig_mod
        else:
            sys.modules.pop("scripts.p2_market_slot_optimizer", None)

        v1_mod_name = (
            "docs.experiments.agent_selection.p2_market_slot_ordering."
            "sources.prvsiyan_global_sell_slot_challenger.main"
        )
        if v1_mod_name in sys.modules:
            del sys.modules[v1_mod_name]


def test_missing_quantity_v2():
    """V2 strictly requires a positive quantity for SELL orders."""
    v2 = load_v2_helper()
    orders = [
        ["SELL", "WHEAT"],
        ["SELL", "CORN", 0],
        ["SELL", "OATS", -5],
        ["SELL", "POTATO", "invalid"],
    ]
    indices = v2.find_eligible_sell_indices(orders)
    assert indices == [], "V2 incorrectly accepted invalid SELL quantities"

    valid_orders = [["SELL", "WHEAT", 10]]
    indices = v2.find_eligible_sell_indices(valid_orders)
    assert indices == [0], "V2 rejected valid SELL quantity"


def test_many_identical_orders_v2():
    """V2 distinct_permutations does not loop excessively over identical elements."""
    v2 = load_v2_helper()
    orders = [["SELL", "WHEAT", 10]] * 10
    indices = list(range(10))

    eval_count = 0

    def scoring_callback(cand):
        nonlocal eval_count
        eval_count += 1
        return 1.0

    with patch("itertools.permutations") as mock_perm:
        _, stats = v2.optimize_sell_slots(orders, indices, scoring_callback, budget=800)
        assert not mock_perm.called, "V2 still calls itertools.permutations!"

    assert stats["evals"] == 0, (
        "V2 evaluated duplicates unnecessarily. "
        "With 10 identical, base is skipped, 0 evals remain."
    )
    assert stats["budget_hits"] == 0, "V2 hit budget on identical items"


def test_unique_permutation_order_equivalence_v2():
    """
    V2 distinct_permutations must preserve the exact first-occurrence order
    of itertools.permutations.
    """
    v2 = load_v2_helper()
    items = ["A", "B", "A"]

    # First occurrences from itertools.permutations
    seen = set()
    itertools_order = []
    for p in itertools.permutations(items):
        if p not in seen:
            seen.add(p)
            itertools_order.append(p)

    # From distinct_permutations
    v2_order = list(v2.distinct_permutations(items))
    assert (
        v2_order == itertools_order
    ), "V2 order does not match itertools first-occurrence order"


def test_budget_and_tie_determinism_v2():
    """
    V2 must respect the budget, return the best score, and use stable
    tie-breaking.
    """
    v2 = load_v2_helper()
    orders = [["SELL", f"ITEM_{i}", 1] for i in range(5)]
    indices = list(range(5))

    eval_count = 0

    def scoring_callback(cand):
        nonlocal eval_count
        eval_count += 1
        if eval_count == 1:
            return 1.0
        if eval_count == 2:
            return 2.0
        if eval_count == 3:
            return 2.0  # tie
        return 0.5

    res, stats = v2.optimize_sell_slots(orders, indices, scoring_callback, budget=2)

    assert stats["evals"] == 2
    assert stats["budget_hits"] == 1

    perm_gen = v2.distinct_permutations([orders[i] for i in indices])
    _ = next(perm_gen)  # Base
    second_perm = next(perm_gen)  # Eval 1

    expected_orders = list(orders)
    for idx_in_subset, orig_idx in enumerate(indices):
        expected_orders[orig_idx] = second_perm[idx_in_subset]

    assert res == expected_orders, "V2 did not retain the first tied best candidate"


def test_import_shadowing_v2():
    """V2 Challenger directly executes the helper, ignoring sys.modules shadowing."""
    fake_mod = types.ModuleType("scripts.p2_market_slot_optimizer_reviewed")
    fake_mod.fake_marker = True

    orig_mod = sys.modules.get("scripts.p2_market_slot_optimizer_reviewed")
    sys.modules["scripts.p2_market_slot_optimizer_reviewed"] = fake_mod

    unique_mod_name = "test_v2_challenger_unique"
    spec = importlib.util.spec_from_file_location(
        unique_mod_name, str(V2_CHALLENGER_PATH.resolve())
    )
    v2_challenger = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(v2_challenger)

        assert hasattr(
            fake_mod, "fake_marker"
        ), "Fake module was overwritten or removed"
        assert not hasattr(
            v2_challenger._HELPER_MOD, "fake_marker"
        ), "V2 loaded fake module instead of executing bytes"
        assert v2_challenger._HELPER_MOD.__file__ == str(
            V2_HELPER_PATH.resolve()
        ), "V2 helper module __file__ mismatch"
        assert callable(
            v2_challenger.find_eligible_sell_indices
        ), "Helper function missing from verified module namespace"
        assert callable(
            v2_challenger.optimize_sell_slots
        ), "Helper function missing from verified module namespace"

        mod_name = v2_challenger._HELPER_MOD.__name__
        assert mod_name.endswith("_p2_market_slot_optimizer_reviewed_frozen")
    finally:
        if orig_mod is not None:
            sys.modules["scripts.p2_market_slot_optimizer_reviewed"] = orig_mod
        else:
            sys.modules.pop("scripts.p2_market_slot_optimizer_reviewed", None)

        to_del = [k for k in sys.modules if k.startswith(unique_mod_name)]
        for k in to_del:
            del sys.modules[k]


def test_non_integral_quantities_v2():
    """V2 strictly requires a positive integer, rejecting floats, bools, strings."""
    v2 = load_v2_helper()

    orders = [
        ["SELL", "WHEAT", 1.5],
        ["SELL", "CORN", True],
        ["SELL", "OATS", "2"],
    ]
    indices = v2.find_eligible_sell_indices(orders)
    assert indices == [], "V2 incorrectly accepted non-integral SELL quantities"

    valid_orders = [["SELL", "WHEAT", 2]]
    indices = v2.find_eligible_sell_indices(valid_orders)
    assert indices == [0], "V2 rejected valid positive integer SELL quantity"


def test_candidate_scorer_exceptions_consume_budget_v2():
    """
    With baseline scorer returning normally but every candidate scorer raising,
    attempts beyond baseline consume `budget` and set `evals`, `errors`,
    and `budget_hits` consistently (e.g. budget=2 => exactly 2 failed candidate
    attempts then stop).
    """
    v2 = load_v2_helper()
    orders = [["SELL", f"ITEM_{i}", 1] for i in range(4)]
    indices = list(range(4))

    eval_count = 0

    def scoring_callback(cand):
        nonlocal eval_count
        eval_count += 1
        if eval_count == 1:
            return 1.0  # baseline
        raise RuntimeError("Candidate error")

    res, stats = v2.optimize_sell_slots(orders, indices, scoring_callback, budget=2)

    assert eval_count == 3  # 1 baseline + 2 candidates
    assert stats["evals"] == 2
    assert stats["errors"] == 2
    assert stats["budget_hits"] == 1


def test_sys_path_and_modules_shadowing_v2(tmp_path, monkeypatch):
    """
    Load the V2 wrapper with both a fake sys.modules helper and a higher-priority
    temporary sys.path shadow, proving canonical verified helper bytes are still used.
    """
    shadow_dir = tmp_path / "scripts"
    shadow_dir.mkdir()
    (shadow_dir / "__init__.py").touch()
    shadow_file = shadow_dir / "p2_market_slot_optimizer_reviewed.py"
    shadow_file.write_text("fake_marker_path = True\n")

    monkeypatch.delitem(
        sys.modules, "scripts.p2_market_slot_optimizer_reviewed", raising=False
    )
    monkeypatch.delitem(sys.modules, "scripts", raising=False)

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()

    # Prove the shadow works for standard imports
    shadow_check = importlib.import_module("scripts.p2_market_slot_optimizer_reviewed")
    assert hasattr(shadow_check, "fake_marker_path"), "Standard import didn't shadow!"
    assert shadow_check.__file__ == str(shadow_file), "Did not resolve to the fake file"

    # Restore the sys.modules fake for the dual-test
    fake_mod = types.ModuleType("scripts.p2_market_slot_optimizer_reviewed")
    fake_mod.fake_marker = True
    monkeypatch.setitem(
        sys.modules, "scripts.p2_market_slot_optimizer_reviewed", fake_mod
    )

    unique_mod_name = "test_v2_challenger_path_shadow"
    spec = importlib.util.spec_from_file_location(
        unique_mod_name, str(V2_CHALLENGER_PATH.resolve())
    )
    v2_challenger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v2_challenger)

    assert hasattr(fake_mod, "fake_marker"), "sys.modules fake was modified"
    assert not hasattr(
        v2_challenger._HELPER_MOD, "fake_marker"
    ), "Loaded from sys.modules"
    assert not hasattr(
        v2_challenger._HELPER_MOD, "fake_marker_path"
    ), "Loaded from sys.path shadow"

    assert v2_challenger._HELPER_MOD.__file__ == str(
        V2_HELPER_PATH.resolve()
    ), "Did not load canonical path"


def test_module_namespace_cleanup_v2():
    """
    Demonstrate helper/baseline nested entries do not remain in sys.modules
    after the wrapper module is loaded and its functions remain callable.
    """
    unique_mod_name = "test_v2_challenger_cleanup"
    spec = importlib.util.spec_from_file_location(
        unique_mod_name, str(V2_CHALLENGER_PATH.resolve())
    )
    v2_challenger = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v2_challenger)

    mod_name = v2_challenger._HELPER_MOD.__name__
    assert mod_name not in sys.modules, f"{mod_name} remains in sys.modules"

    baseline_mod_name = v2_challenger._BASELINE_MOD.__name__
    assert (
        baseline_mod_name not in sys.modules
    ), f"{baseline_mod_name} remains in sys.modules"

    assert callable(v2_challenger.find_eligible_sell_indices)
    assert callable(v2_challenger.optimize_sell_slots)
    assert callable(v2_challenger._BASE_AGENT)

    orders = [["SELL", "WHEAT", 1]]
    indices = v2_challenger.find_eligible_sell_indices(orders)
    assert indices == [0]
