def test_orphan_audit(summary, records):
    row = records("PR162R_OrphanCandidateReportAudit.report.json")[0]
    assert row["orphan_candidate_count"] == 0
    assert row["orphan_generated_report_count"] == 0
    assert row["orphan_qku_count"] == 0
    assert row["orphan_handoff_count"] == 0
    assert summary["orphan_candidate_count"] == 0
