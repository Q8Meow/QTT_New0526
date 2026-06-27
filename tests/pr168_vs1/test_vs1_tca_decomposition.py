from __future__ import annotations

from ._helpers import d, rows


def test_vs1_tca_decomposition_sums_all_required_components():
    required = (
        "fees_cash",
        "spread_cost_cash",
        "slippage_cash",
        "queue_fill_shortfall_cash",
        "cancel_replace_cost_cash",
        "latency_penalty_cash",
        "capital_lock_cost_cash",
        "capacity_cost_cash",
        "crowding_cost_cash",
    )

    for row in rows("tca_breakdown_receipts.jsonl"):
        total = sum(d(row[name]) for name in required)
        assert total == d(row["tca_total_cash"])
