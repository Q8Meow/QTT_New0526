from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_scenario_rank_uses_scenario_ladder() -> None:
    assert_rank3_valid()
    assert all(row["scenario_count"] > 1 for row in rows("scenario_rank"))
