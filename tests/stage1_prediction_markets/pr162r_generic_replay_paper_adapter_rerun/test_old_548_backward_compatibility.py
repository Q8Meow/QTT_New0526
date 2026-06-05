def test_old_548_backward_compatibility(summary, records):
    rows = records("PR162R_Old548CompatibilityTrace.report.json")
    assert len(rows) == 548
    assert summary["old_548_backward_compatibility_preserved"] is True
    assert all(row["old_source_truth_status_preserved_as_candidate_flag"] for row in rows)
    assert not any(row["overwrites_pr162d_r2a_universe_flag"] for row in rows)
