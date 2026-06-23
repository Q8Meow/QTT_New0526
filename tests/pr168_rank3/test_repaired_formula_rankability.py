from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_repaired_formulas_rankable_only_with_evidence() -> None:
    assert_rank3_valid()
    rankability = rows("repaired_formula_rank_eligibility")
    assert len(rankability) == 12
    assert all(row["rankable_flag"] is False for row in rankability)
