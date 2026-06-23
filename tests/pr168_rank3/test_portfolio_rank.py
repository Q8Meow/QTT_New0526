from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_portfolio_rank_rows_have_marginal_utility() -> None:
    assert_rank3_valid()
    assert all("portfolio_marginal_utility" in row for row in rows("portfolio_rank"))
