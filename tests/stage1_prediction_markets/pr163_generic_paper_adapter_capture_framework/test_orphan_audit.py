def test_orphan_audit_has_zero_orphans(records):
    row = records("PR163_OrphanPaperAdapterArtifactAudit.report.json")[0]
    for key, value in row.items():
        if key.startswith("orphan_") and key != "orphan_audit_ref":
            assert value == 0
