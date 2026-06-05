def test_paper_synthetic_fill_model(summary, records):
    rows = records("PR162R_B_PaperSyntheticFillModelRegistry.report.json")
    assert len(rows) == summary["paper_synthetic_fill_model_count"] > 0
