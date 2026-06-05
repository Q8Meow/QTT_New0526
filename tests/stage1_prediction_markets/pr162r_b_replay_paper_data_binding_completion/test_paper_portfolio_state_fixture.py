def test_paper_portfolio_state_fixture(summary, records):
    rows = records("PR162R_B_PaperPortfolioStateFixtureRegistry.report.json")
    assert len(rows) == summary["paper_portfolio_fixture_count"] > 0
