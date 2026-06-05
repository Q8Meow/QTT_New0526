def test_downstream_pr163_pr164_pr165_handoff(summary, records):
    pr163 = records("PR162R_PR163PaperAdapterHandoffSeed.report.json")
    pr164 = records("PR162R_PR164ReviewProvenanceHandoffSeed.report.json")
    pr165 = records("PR162R_PR165ScoringRankingHandoffSeed.report.json")
    assert len(pr163) == summary["pr163_handoff_seed_count"]
    assert len(pr164) == summary["pr164_handoff_seed_count"]
    assert len(pr165) == summary["pr165_handoff_seed_count"]
    assert pr163 and pr164 and pr165
    assert all(row["result_packet_created_count"] == 0 for row in pr163[:25])
