def test_replay_binding_fanout(summary, records):
    rows = records("PR162R_B_ReplayBindingFanoutMatrix.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["binding_refs"] for row in rows)
