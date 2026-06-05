def test_orphan_audit(summary, records):
    row = records("PR162R_B_OrphanBindingCandidateReportAudit.report.json")[0]
    assert row["orphan_binding_packet_count"] == summary["orphan_binding_packet_count"] == 0
    assert row["orphan_source_candidate_count"] == summary["orphan_source_candidate_count"] == 0
