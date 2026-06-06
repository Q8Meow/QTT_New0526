def test_pr162e_plugin_paper_adapter_compatibility_covers_universe(records, summary):
    rows = records("PR163_PR162EPluginPaperAdapterCompatibilityUpdate.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert rows[0]["plugin_intake_status"] == "PAPER_ADAPTER_CAPTURE_COMPATIBLE_NONLIVE"
