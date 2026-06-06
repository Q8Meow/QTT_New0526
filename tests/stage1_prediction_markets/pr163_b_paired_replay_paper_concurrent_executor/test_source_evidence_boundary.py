def test_source_evidence_boundary_does_not_accept_sources(records, summary):
    row = records("PR163_B_SourceEvidenceBoundaryAudit.report.json")[0]
    assert row["source_evidence_boundary_violation_count"] == 0
    assert row["source_acceptance_count"] == 0
    assert row["connector_binding_count"] == 0
    assert summary["source_evidence_boundary_violation_count"] == 0
