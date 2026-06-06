def test_paper_market_state_normalization_is_fixture_bound(records, summary):
    rows = records("PR163_PaperMarketStateNormalizationRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert rows[0]["truth_status"] == "SYNTHETIC_OR_CANDIDATE_PAPER_CAPTURE"
    assert rows[0]["best_bid"] < rows[0]["best_ask"]
