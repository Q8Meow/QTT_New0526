from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_retest_sample_plan_includes_no_trade_and_asof() -> None:
    assert_recovery1_valid()
    assert all(row["include_no_trade_competitor_flag"] and row["asof_lock_required_flag"] for row in rows("retest_sample_plan"))
