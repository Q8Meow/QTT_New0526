def test_quantum_hot_path_exclusion_is_batch_only(records, summary):
    rows = records("PR163_PaperHotPathExclusionMatrix.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["quantum_backend_in_hot_path"] is False for row in rows[:100])
    assert all(row["llm_in_hot_path"] is False for row in rows[:100])
