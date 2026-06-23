from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_marginal_utility_rows_exist() -> None:
    assert_rank3_valid()
    assert all("marginal_utility_score" in row for row in rows("marginal_utility"))
