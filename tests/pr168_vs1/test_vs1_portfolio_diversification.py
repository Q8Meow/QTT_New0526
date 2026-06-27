from __future__ import annotations

from ._helpers import d, rows


def test_vs1_portfolio_conflict_receipts_apply_marginal_utility_penalty():
    receipts = rows("portfolio_diversification_receipts.jsonl")
    conflict = [row for row in receipts if row["fixture_id"].startswith("VS1_FIXTURE_0005")]

    assert conflict
    assert any(d(row["portfolio_penalty_cash"]) > 0 for row in conflict)
    assert any(d(row["marginal_utility_cash"]) <= 0 for row in conflict)
    assert any(row["portfolio_gate_passed"] is False for row in conflict)
