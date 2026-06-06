def test_paper_fill_simulator_walks_orderbook_depth(records):
    rows = records("PR163_PaperSyntheticFillEventRegistry.report.json")
    assert rows
    assert any(row["depth_walk_level_count"] > 1 for row in rows)
    for row in rows[:100]:
        assert sum(level["fill_qty_at_level"] for level in row["level_fills"]) == row["filled_qty"]
