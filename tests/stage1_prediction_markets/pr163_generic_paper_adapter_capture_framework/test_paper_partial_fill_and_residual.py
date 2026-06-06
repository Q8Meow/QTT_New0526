def test_partial_fill_and_residual_rows_exist(records):
    rows = records("PR163_PaperSyntheticFillEventRegistry.report.json")
    partial = [row for row in rows if row["filled_qty"] > 0 and row["residual_qty"] > 0]
    assert partial
    assert all(row["filled_qty"] + row["residual_qty"] == row["requested_qty"] for row in partial[:100])
