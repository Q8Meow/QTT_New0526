def test_pr164_handoff_covers_universe(records, summary):
    rows = records("PR163_PR164ReviewProvenanceHandoff.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["target_pr"] == "PR164" for row in rows[:100])
