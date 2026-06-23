from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_pareto_frontier_rows_exist() -> None:
    assert_rank3_valid()
    assert any(row["pareto_frontier_flag"] for row in rows("pareto_frontier"))
