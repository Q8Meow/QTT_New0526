from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation import paths as p
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_no_dead_end_files_or_reports():
    manifest = load_records("PR163_C_ReportManifest.report.json")
    assert {row["report_filename"] for row in manifest} == set(p.REPORT_FILENAMES)
    assert all(row["downstream_consumer"] for row in manifest)
    assert summary()["dead_end_file_count"] == 0
