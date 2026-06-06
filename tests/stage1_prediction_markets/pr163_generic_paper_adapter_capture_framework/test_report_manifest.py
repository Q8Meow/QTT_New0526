from src.qtt.stage1_prediction_markets.pr163_generic_paper_adapter_capture_framework import paths as p


def test_report_manifest_lists_every_report(records):
    rows = records("PR163_ReportManifest.report.json")
    assert {row["report_filename"] for row in rows} == set(p.REPORT_FILENAMES)
    assert len(rows) == len(p.REPORT_FILENAMES)


def test_transition_registry_manifest_records_shards(records, report):
    manifest_row = next(
        row
        for row in records("PR163_ReportManifest.report.json")
        if row["report_filename"] == "PR163_PaperOrderStateTransitionRegistry.report.json"
    )
    root = report("PR163_PaperOrderStateTransitionRegistry.report.json")
    assert root["records"] == []
    assert root["total_row_count"] == 38102
    assert root["sharded_flag"] is True
    assert manifest_row["row_count"] == 38102
    assert manifest_row["sharded_flag"] is True
    assert manifest_row["shard_paths"] == root["shard_files"]
