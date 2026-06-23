from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_source_contradiction_audit_has_major_families() -> None:
    assert_recovery1_valid()
    rows = report("PR168_RECOVERY1_SourceContradictionAudit.report.json")["records"]["rows"]
    assert len(rows) >= 4
    assert all(not row["contradiction_found_flag"] for row in rows)
