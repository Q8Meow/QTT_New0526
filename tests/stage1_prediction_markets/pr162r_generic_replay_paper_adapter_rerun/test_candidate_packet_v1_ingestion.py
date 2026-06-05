def test_candidate_packet_v1_ingestion(summary, records):
    rows = records("PR162R_CandidatePacketV1IngestionLedger.report.json")
    assert summary["candidate_packet_v1_ingested_count"] >= 6502
    assert summary["pr162d_r2a_candidate_packet_ingested_count"] >= 6502
    assert len(rows) == summary["candidate_packet_v1_ingested_count"]
    assert all(row["candidate_packet_ref"] for row in rows)
    assert all(row["generic_extension_present_flag"] for row in rows)
