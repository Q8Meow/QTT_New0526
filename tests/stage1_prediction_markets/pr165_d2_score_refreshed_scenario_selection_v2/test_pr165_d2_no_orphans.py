from __future__ import annotations


def test_no_orphan_audit_and_rows_are_connected(pr165_d2_records, pr165_d2_summary):
    assert pr165_d2_summary["orphan_rows"] == 0
    audit = pr165_d2_records["PR165_D2_OrphanArtifactAudit.report.json"][0]
    assert audit["no_orphan_audit_result"] == "PASS"
    for rows in pr165_d2_records.values():
        assert all("ORPHAN" not in row["no_orphan_status"] for row in rows)
