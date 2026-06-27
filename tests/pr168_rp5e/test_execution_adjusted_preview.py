from ._helpers import read_jsonl


def test_execution_adjusted_preview_does_not_compute_cash_or_expected_pnl() -> None:
    rows = read_jsonl("exec_prev.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["no_cash_pnl_computed_flag"] is True
        assert row["net_expected_pnl_computed_flag"] is False
        assert row["future_rp5g_required_flag"] is True
        assert row["preview_only_score_authority"] is True
