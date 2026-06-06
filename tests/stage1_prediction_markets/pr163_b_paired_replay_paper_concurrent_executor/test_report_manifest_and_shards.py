from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor import paths as p


def test_report_manifest_lists_every_report_and_shards(records, report):
    rows = records("PR163_B_ReportManifest.report.json")
    assert {row["report_filename"] for row in rows} == set(p.REPORT_FILENAMES)
    replay_manifest = next(row for row in rows if row["report_filename"] == "PR163_B_ReplayLaneExecutionTraceRegistry.report.json")
    replay_root = report("PR163_B_ReplayLaneExecutionTraceRegistry.report.json")
    assert replay_manifest["sharded_flag"] is True
    assert replay_manifest["shard_paths"] == replay_root["shard_files"]
