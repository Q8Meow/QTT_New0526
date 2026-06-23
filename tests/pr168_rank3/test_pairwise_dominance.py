from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_pairwise_dominance_rows_compare_nearby_and_notrade() -> None:
    assert_rank3_valid()
    assert all(row["nearby_alternative_stack_id"] and row["no_trade_dominates_pair_flag"] for row in rows("pairwise_dominance"))
