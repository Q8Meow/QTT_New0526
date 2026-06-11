from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.enums import (
    ALLOWED_NO_ORPHAN_STATUSES,
)


def test_pr166_sm_every_row_has_upstream_downstream_and_no_orphan_status(pr166_sm_records):
    for filename, rows in pr166_sm_records.items():
        for row in rows:
            assert row["no_orphan_status"] in ALLOWED_NO_ORPHAN_STATUSES, filename
            assert row["upstream_artifact_refs"] or row["terminal_status_flag"], filename
            assert row["downstream_artifact_refs"], filename
            assert row["downstream_agent_consumers"], filename
            assert row["validator_ref"], filename
            assert row["schema_ref"], filename
            assert row["manifest_ref"] == "PR166_SM_ReportManifest.report.json"


def test_pr166_sm_orphan_audit_is_clean(pr166_sm_records):
    row = pr166_sm_records["PR166_SM_OrphanArtifactAudit.report.json"][0]
    assert row["audit_result"] == "PASS"
    assert row["orphan_rows"] == 0
    assert row["rows_without_downstream"] == 0
    assert row["rows_without_validator"] == 0
    assert row["rows_without_schema"] == 0
