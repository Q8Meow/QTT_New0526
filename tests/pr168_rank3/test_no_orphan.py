from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_all_rank3_shard_rows_have_no_orphan_status() -> None:
    assert_rank3_valid()
    for key in ("feature_matrix", "no_trade_competition", "repair_route", "q_rank", "downstream_handoff"):
        assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in rows(key))
