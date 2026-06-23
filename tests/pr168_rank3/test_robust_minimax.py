from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_robust_minimax_rows_exist() -> None:
    assert_rank3_valid()
    assert len(rows("robust_minimax")) == 35
