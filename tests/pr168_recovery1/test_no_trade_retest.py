from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_no_trade_remains_permanent_competitor() -> None:
    assert_recovery1_valid()
    assert all(row["no_trade_is_permanent_competitor_flag"] for row in rows("no_trade_retest"))
