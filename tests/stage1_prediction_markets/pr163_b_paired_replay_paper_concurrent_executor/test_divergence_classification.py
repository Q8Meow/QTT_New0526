def test_divergence_classification_contains_pass_reject_and_cost_classes(records, summary):
    rows = records("PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    counts = summary["divergence_counts_by_class"]
    for required in ("PAPER_PASS_REPLAY_PASS", "PAPER_PASS_REPLAY_REJECT", "PAPER_REJECT_REPLAY_PASS", "PAPER_REJECT_REPLAY_REJECT", "FEE_DIVERGENCE"):
        assert counts[required] > 0
