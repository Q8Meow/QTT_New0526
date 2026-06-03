from __future__ import annotations


def test_pr162d_r1_no_hallucinated_source_records(records, summary):
    audit = records("PR162D_R1_NoHallucinatedSourceAudit.report.json")[0]
    assert audit["hallucinated_source_record_count"] == 0
    assert audit["source_locator_missing_count"] == 0
    assert summary["hallucinated_source_record_count"] == 0
