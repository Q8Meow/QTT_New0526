"""Quantum constraint helpers."""

from __future__ import annotations


def default_constraint_terms(candidate_ids: list[str]) -> list[dict[str, object]]:
    selected = [f"x_{cid.lower().replace('-', '_')}_selected_binary" for cid in candidate_ids]
    return [
        {"constraint_name": "max_candidate_count_constraint", "terms": selected, "sense": "<=", "rhs": 1},
        {"constraint_name": "one_no_trade_or_candidate_constraint", "terms": [*selected, "x_no_trade_binary"], "sense": "==", "rhs": 1},
        {"constraint_name": "owner_enablement_future_live_constraint_fixed_zero", "terms": selected, "sense": "<=", "rhs": len(selected)},
        {"constraint_name": "no_stale_candidate_constraint", "terms": selected, "sense": "<=", "rhs": len(selected)},
    ]

