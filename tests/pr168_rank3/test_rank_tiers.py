from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_rank_tiers_do_not_create_live_or_champion() -> None:
    assert_rank3_valid()
    assert all(row["champion_allowed_flag"] is False and row["live_candidate_allowed_flag"] is False for row in rows("rank_tier"))
