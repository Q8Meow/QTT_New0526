from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_evidence_reliability_shrinkage_rows_exist() -> None:
    assert_rank3_valid()
    assert all(row["shrinkage_applied_flag"] for row in rows("evidence_reliability"))
