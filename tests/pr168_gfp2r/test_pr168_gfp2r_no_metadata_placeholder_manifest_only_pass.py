from tests.pr168_gfp2r._helpers import assert_all_reports_have_records, record_rows


def test_pr168_gfp2r_no_metadata_placeholder_manifest_only_pass() -> None:
    assert_all_reports_have_records()
    essentiality_rows = record_rows("PR168_GFP2R_ReportEssentialityAndDeduplicationAudit")
    assert essentiality_rows
    assert all(row["essentiality_status"] == "ESSENTIAL_OPERATIONAL_CONTENT" for row in essentiality_rows)
