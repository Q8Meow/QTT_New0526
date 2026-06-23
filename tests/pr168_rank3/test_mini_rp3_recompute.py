from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_mini_rp3_recompute_rows_gap_not_fake() -> None:
    assert_rank3_valid()
    assert all(row["candidate_replay_pnl_or_gap"] == "NOT_COMPUTED_INPUT_GAP" for row in rows("mini_rp3_recompute"))
