from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_evidence_universe_has_source_refs() -> None:
    assert_rank3_valid()
    evidence = rows("evidence_universe")
    assert evidence
    assert all(row["source_row_ref"] for row in evidence[:200])
