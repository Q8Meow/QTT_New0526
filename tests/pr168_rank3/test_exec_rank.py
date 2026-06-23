from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_execution_adjusted_rank_is_numeric_non_proof() -> None:
    assert_rank3_valid()
    assert all(isinstance(row["rank3_execution_adjusted_utility_non_proof"], float) for row in rows("execution_adjusted_rank"))
