from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_no_trade_tournament_wins_current_candidates() -> None:
    assert_rank3_valid()
    assert all(row["no_trade_tournament_winner"] == "NO_TRADE" for row in rows("tournament_rank"))
