def test_paper_adapter_input_registry_covers_universe(records, summary):
    rows = records("PR163_PaperAdapterInputRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert rows[0]["schema_version"] == "PaperAdapterInputV1"
    assert rows[0]["paper_binding_refs"]
