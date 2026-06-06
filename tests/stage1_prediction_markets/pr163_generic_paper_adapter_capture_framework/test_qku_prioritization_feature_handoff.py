def test_qku_prioritization_handoff_has_features_but_no_rank(records, summary):
    rows = records("PR163_PaperQKUPrioritizationFeatureHandoffRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    row = rows[0]
    assert "expected_value_ref_or_value" in row
    assert row["no_score_created"] is True
    assert row["no_rank_created"] is True
    assert row["no_promotion_created"] is True
