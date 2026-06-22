from tests.pr168_gfp2r._helpers import assert_positive_count, rows


def test_pr168_gfp2r_rank2_handoff_has_no_trade_and_candidate_only_flags() -> None:
    assert_positive_count("rank2_candidate_handoff_count")
    rank2_rows = rows("rank2_handoff")
    assert all(row["candidate_only_flag"] is True for row in rank2_rows)
    assert all(row["champion_allowed_flag"] is False for row in rank2_rows)
    assert all(row["live_candidate_allowed_flag"] is False for row in rank2_rows)
    assert all(row["no_trade_baseline_ref"] for row in rank2_rows)
