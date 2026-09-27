from pathlib import Path

from scripts.analyze_p2_v2_confirmation import compute_whole_seed_bootstrap


def test_bootstrap_reproducibility():
    summary_path = Path(
        "docs/experiments/agent_selection/p2_v2_market_slot_ordering/confirmation_summary.json"
    )
    assert summary_path.is_file()

    results = compute_whole_seed_bootstrap(summary_path, n_resamples=1000, rng_seed=42)
    assert "mean_delta" in results
    assert "ci_lower" in results
    assert "ci_upper" in results
    assert "h2h_v2_points_rate" in results
    assert "decision" in results
    assert results["ci_lower"] <= results["mean_delta"] <= results["ci_upper"]
