"""
P2 Market Slot Optimizer
========================
Pure helper for deterministic, bounded permutation search over eligible SELL
order slots.

Invariants:
1. Exact market-list length is preserved.
2. Every non-SELL and blank slot remains at its exact index.
3. Every wash SELL (selling an item present in any BUY_PRODUCT order) remains
   pinned at its exact index.
4. Eligible SELL orders are permuted ONLY among the existing eligible SELL
   indices.
5. SELL multiset and quantities are strictly conserved.
6. Deterministic candidate generation and deduplication up to a strict
   evaluation budget.
7. Baseline action is retained as a no-op candidate (adopted only if
   gain > min_gain, default 0.5).
8. Stable tie-breaking: first candidate achieving superior score is kept.
9. Exceptions during scoring/optimization are safely caught, returning
   baseline orders.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from typing import Any


def find_wash_items(orders: Sequence[Any]) -> set[str]:
    """Return the set of item names present in BUY_PRODUCT orders."""
    wash: set[str] = set()
    for o in orders:
        if o and len(o) > 1 and o[0] == "BUY_PRODUCT" and isinstance(o[1], str):
            wash.add(o[1])
    return wash


def find_eligible_sell_indices(orders: Sequence[Any]) -> list[int]:
    """
    Find indices of eligible SELL orders that may be permuted.

    - Blank slots (None or empty list/tuple) are pinned / not eligible.
    - Non-SELL orders (e.g. BUY_PRODUCT, BUY_SEED, BUY_ANIMAL, BUY_LAND, HIRE)
      are pinned.
    - Wash sales (items also present in BUY_PRODUCT orders) are pinned.
    - SELL orders with valid positive quantity are eligible.
    """
    wash_items = find_wash_items(orders)
    eligible: list[int] = []
    for i, o in enumerate(orders):
        if not o or len(o) < 2:
            continue
        if o[0] == "SELL":
            item = o[1]
            if item in wash_items:
                continue
            if len(o) >= 3:
                try:
                    qty = int(o[2])
                    if qty <= 0:
                        continue
                except (ValueError, TypeError):
                    continue
            eligible.append(i)
    return eligible


def optimize_sell_slots(
    orders: Sequence[Any],
    eligible_indices: Sequence[int],
    scoring_callback: Callable[[list[Any]], float],
    budget: int = 800,
    min_gain: float = 0.5,
) -> tuple[list[Any], dict[str, Any]]:
    """
    Deterministically permute eligible SELL orders across existing eligible
    SELL indices.

    Args:
        orders: The original market orders list (may contain None, [], or
            list/tuple orders).
        eligible_indices: Indices in `orders` of eligible SELL orders.
        scoring_callback: Function evaluating an order list and returning a
            numeric score/margin.
        budget: Maximum number of candidate orderings to score beyond baseline
            (default 800).
        min_gain: Threshold of score improvement over baseline required to adopt
            a candidate (default 0.5).

    Returns:
        (best_orders, stats_dict)
        where stats_dict contains:
            'evals': int,
            'budget_hits': int,
            'changed_slots': int,
            'gain': float,
            'base_score': float,
            'best_score': float,
            'errors': int
    """
    orders_list: list[Any] = [
        list(o) if isinstance(o, (list, tuple)) else o for o in orders
    ]

    stats: dict[str, Any] = {
        "evals": 0,
        "budget_hits": 0,
        "changed_slots": 0,
        "gain": 0.0,
        "base_score": 0.0,
        "best_score": 0.0,
        "errors": 0,
    }

    if len(eligible_indices) < 2:
        return orders_list, stats

    try:
        base_score = float(scoring_callback(orders_list))
    except Exception:
        stats["errors"] = 1
        return orders_list, stats

    stats["base_score"] = base_score
    stats["best_score"] = base_score
    best = base_score
    best_orders: list[Any] | None = None

    eligible_sells = [orders_list[i] for i in eligible_indices]

    seen: set[tuple[Any, ...]] = set()
    base_key = tuple(
        tuple(o) if isinstance(o, (list, tuple)) else o for o in eligible_sells
    )
    seen.add(base_key)

    evals = 0
    budget_hits = 0
    errors = 0

    for perm in itertools.permutations(eligible_sells):
        key = tuple(tuple(o) if isinstance(o, (list, tuple)) else o for o in perm)
        if key in seen:
            continue
        seen.add(key)

        if evals >= budget:
            budget_hits = 1
            break

        cand = list(orders_list)
        for idx, sell_order in zip(eligible_indices, perm, strict=True):
            cand[idx] = sell_order

        try:
            val = float(scoring_callback(cand))
            evals += 1
        except Exception:
            errors += 1
            continue

        if val > best + min_gain:
            best = val
            best_orders = cand

    stats["evals"] = evals
    stats["budget_hits"] = budget_hits
    stats["errors"] = errors
    stats["best_score"] = best

    if best_orders is not None:
        stats["changed_slots"] = sum(
            a != b for a, b in zip(orders_list, best_orders, strict=True)
        )
        stats["gain"] = best - base_score
        return best_orders, stats

    return orders_list, stats
