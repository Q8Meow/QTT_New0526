from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_prior_fake_neutral_zero_notrade_is_unproven_without_accepted_data() -> None:
    rows = load("PR168_GFP2_FakeNeutralZeroNoTradeReopenQueue.report.json")
    assert rows
    assert all(row["real_market_data_used_flag"] is False for row in rows[:1000])
