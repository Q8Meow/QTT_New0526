def test_large_report_sharding(summary, report):
    stress_root = report("PR163_B_ReplayPaperScenarioStressCandidateRegistry.report.json")
    assert stress_root["records"] == []
    assert stress_root["shard_count"] > 1
    assert summary["largest_root_report_size_bytes"] < 10 * 1024 * 1024
    assert summary["largest_shard_size_bytes"] < 25 * 1024 * 1024
