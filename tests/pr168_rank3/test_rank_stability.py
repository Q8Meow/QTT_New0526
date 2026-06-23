from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_rank_stability_stress_rows_exist() -> None:
    assert_rank3_valid()
    assert len(rows("rank_stability_stress")) == 35
