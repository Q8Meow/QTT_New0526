from src.qtt.stage1_prediction_markets.pr163_generic_paper_adapter_capture_framework import paths as p


def test_report_manifest_lists_every_report(records):
    rows = records("PR163_ReportManifest.report.json")
    assert {row["report_filename"] for row in rows} == set(p.REPORT_FILENAMES)
    assert len(rows) == len(p.REPORT_FILENAMES)
