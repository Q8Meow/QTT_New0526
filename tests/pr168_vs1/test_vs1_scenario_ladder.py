from __future__ import annotations

from ._helpers import d, rows


def test_vs1_scenario_ladder_materializes_tail_penalties_and_gate_results():
    ladders = rows("scenario_ladder_receipts.jsonl")

    assert ladders
    assert any(row["scenario_gate_passed"] is False for row in ladders)
    for row in ladders:
        scenario_values = [
            d(row[name])
            for name in (
                "base_case_pnl_cash",
                "wider_spread_pnl_cash",
                "lower_fill_pnl_cash",
                "latency_decay_pnl_cash",
                "adverse_probability_shift_pnl_cash",
                "thin_book_pnl_cash",
                "crowded_book_pnl_cash",
                "portfolio_conflict_pnl_cash",
            )
        ]
        assert d(row["worst_case_pnl_cash"]) == min(scenario_values)
