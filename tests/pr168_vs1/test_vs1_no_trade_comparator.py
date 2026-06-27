from __future__ import annotations

from ._helpers import d, rows


def test_vs1_no_trade_comparator_can_win_without_banning_or_mutating_qkus():
    comparators = rows("no_trade_comparator_receipts.jsonl")
    negative = [row for row in comparators if row["fixture_id"].startswith("VS1_FIXTURE_0002")]

    assert negative
    assert any(row["no_trade_wins_flag"] is True for row in negative)
    for row in comparators:
        assert d(row["no_trade_expected_pnl_cash"]) == 0
        assert row["global_formula_ban_flag"] is False
        assert row["global_qku_ban_flag"] is False
        assert row["formula_mutation_flag"] is False
        assert row["qku_deletion_flag"] is False
