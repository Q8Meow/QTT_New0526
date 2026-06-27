from __future__ import annotations

from ._helpers import d, rows


def test_vs1_expected_cash_pnl_uses_execution_and_risk_adjusted_formula():
    pnl_rows = rows("expected_cash_pnl_receipts.jsonl")

    for row in pnl_rows:
        adjusted = d(row["fill_adjusted_gross_edge_cash"]) - d(row["tca_total_cash"])
        risk = (
            d(row["capacity_penalty_cash"])
            + d(row["crowding_penalty_cash"])
            + d(row["portfolio_penalty_cash"])
            + d(row["uncertainty_penalty_cash"])
            + d(row["overfit_fdr_penalty_cash"])
            + d(row["scenario_tail_penalty_cash"])
        )
        assert adjusted == d(row["execution_adjusted_expected_pnl_cash"])
        assert risk == d(row["risk_penalty_total_cash"])
        assert d(row["net_expected_pnl_cash"]) - d(row["lcb_uncertainty_buffer_cash"]) == d(row["lower_confidence_bound_pnl_cash"])
