def test_row_binding_resolution_matrix(summary, records):
    rows = records("PR162R_B_RowBindingResolutionMatrix.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"] == 6502
    assert all(row["replay_binding_refs"] and row["paper_binding_refs"] for row in rows)
