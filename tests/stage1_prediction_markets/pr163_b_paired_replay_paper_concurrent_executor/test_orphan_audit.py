def test_orphan_audit_has_zero_counts(records, summary):
    row = records("PR163_B_OrphanReplayPaperArtifactAudit.report.json")[0]
    for key, value in row.items():
        if key.startswith("orphan_") and not key.endswith("_ref"):
            assert value == 0
    assert all(value == 0 for value in summary["orphan_counts"].values())
