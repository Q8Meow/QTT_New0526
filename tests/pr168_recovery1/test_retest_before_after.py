from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_retest_before_after_computes_numeric_delta() -> None:
    assert_recovery1_valid()
    for row in rows("retest_before_after"):
        assert row["after_net_expected_pnl_candidate"] >= row["before_net_expected_pnl_candidate"]
        assert row["repair_delta_net_expected_pnl_candidate"] >= 0
