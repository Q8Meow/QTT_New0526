from tests.pr168_gfp2r._helpers import record_rows


def test_pr168_gfp2r_report_essentiality_and_deduplication_audit_exists() -> None:
    rows = record_rows("PR168_GFP2R_ReportEssentialityAndDeduplicationAudit")
    assert rows
    assert all(row["deduplication_decision"] == "KEEP_SEPARATE_DOWNSTREAM_CONTRACT" for row in rows)
