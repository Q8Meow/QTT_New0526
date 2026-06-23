from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_unrepaired_formulas_do_not_fabricate_mini_rp3_evidence() -> None:
    assert_rank3_valid()
    mini = rows("mini_rp3_recompute")
    assert len(mini) == 12
    assert all(row["mini_rp3_evidence_created_flag"] is False for row in mini)
