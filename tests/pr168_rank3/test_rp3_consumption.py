from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_rp3_consumption_preserves_47_formulas_and_35_rankable() -> None:
    assert_rank3_valid()
    consumption = rows("rp3_consumption")
    assert len(consumption) == 47
    assert sum(row["rank3_rankable_flag"] for row in consumption) == 35
