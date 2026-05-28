def test_pr159r_source_evidence_packet_consumed(pr159r_artifacts):
    receipts = pr159r_artifacts["master"]["input_consumption_receipt"]
    assert any(
        item["path"].endswith("QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md")
        and item["consumed"]
        for item in receipts
    )
    assert any(item["artifact_role"] == "source_evidence_schema_input" for item in receipts)

