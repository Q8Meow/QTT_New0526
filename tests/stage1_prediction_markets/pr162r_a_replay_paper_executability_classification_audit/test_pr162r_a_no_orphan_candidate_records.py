from __future__ import annotations


def test_pr162r_a_no_orphan_candidate_records(summary, records):
    audit = records("PR162R_A_NoOrphanCandidateAudit.report.json")[0]
    assert summary["orphan_candidate_count"] == 0
    assert audit["orphan_candidate_count"] == 0
    assert audit["classified_unique_candidate_count"] == summary["candidate_source_count"]
