def test_paper_adapter_input_packets(summary, records):
    rows = records("PR162R_PaperAdapterInputPacketRegistry.report.json")
    assert len(rows) == summary["paper_adapter_input_packet_count"]
    assert rows
    for row in rows[:25]:
        assert row["candidate_packet_ref"]
        assert row["formulation_ref"]
        assert row["computability_route"]
        assert row["agent_refs"]
        assert row["paper_adapter_status"] == "PAPER_INPUT_FILL_REQUIRED"
        assert row["live_order_authority"] is False
