from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_no_trade_competitor_for_every_ranked_stack() -> None:
    assert_rank3_valid()
    no_trade = rows("no_trade_competition")
    assert len(no_trade) == 35
    assert all(row["no_trade_wins_flag_non_proof"] is True for row in no_trade)
