from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_batch_assembly_blocks_raw_top_n() -> None:
    assert_rank3_valid()
    assert all(row["raw_top_n_selection_blocked_flag"] for row in rows("candidate_batch"))
