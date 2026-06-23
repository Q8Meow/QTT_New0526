from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_source_recency_audit_remains_candidate_only() -> None:
    assert_recovery1_valid()
    rows = report("PR168_RECOVERY1_SourceRecencyAudit.report.json")["records"]["rows"]
    assert rows
    assert all(row["accepted_truth_flag"] is False for row in rows)
