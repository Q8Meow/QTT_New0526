def test_dataset_binding_contracts(summary, records):
    rows = records("PR162R_B_ReplayPaperDatasetBindingRegistry.report.json")
    assert len(rows) == summary["dataset_binding_packets_created"]
    assert all(row["binding_task_id"] and row["unit_map"] and row["timestamp_policy"] for row in rows)
    assert all(row["live_allowed"] is False for row in rows)
