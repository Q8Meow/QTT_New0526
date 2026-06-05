def test_downstream_pr163_pr164_pr165_handoff(summary, records):
    assert len(records("PR162R_B_PR163PaperAdapterHandoffUpdate.report.json")) == summary["pr163_handoff_update_rows"]
    assert len(records("PR162R_B_PR164ReviewProvenanceHandoffUpdate.report.json")) == summary["pr164_handoff_update_rows"]
    assert len(records("PR162R_B_PR165ScoringRankingHandoffUpdate.report.json")) == summary["pr165_handoff_update_rows"]
