from __future__ import annotations


def test_pr162d_r1_no_orphan_external_candidates(records, summary):
    audit = records("PR162D_R1_NoOrphanExternalCandidateAudit.report.json")[0]
    assert audit["orphan_external_candidate_count"] == 0
    assert audit["unrouted_external_candidate_count"] == 0
    assert summary["orphan_external_candidate_count"] == 0
