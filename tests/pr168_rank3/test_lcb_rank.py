from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_lcb_unknowns_are_gap_penalized() -> None:
    assert_rank3_valid()
    assert all(row["LCB_unknown_gap_routed_flag"] is True for row in rows("lcb_rank"))
