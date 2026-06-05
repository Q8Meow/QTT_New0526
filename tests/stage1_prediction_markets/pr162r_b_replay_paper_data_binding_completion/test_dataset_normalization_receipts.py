def test_dataset_normalization_receipts(summary, records):
    rows = records("PR162R_B_DatasetNormalizationReceiptRegistry.report.json")
    assert len(rows) == summary["normalization_receipt_rows"]
    assert all("schema_parse_ok" in row["validation_checks"] for row in rows)
    assert all(row["live_allowed"] is False for row in rows)
