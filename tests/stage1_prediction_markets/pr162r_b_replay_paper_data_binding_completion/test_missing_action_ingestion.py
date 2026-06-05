def test_missing_action_ingestion(summary, records):
    rows = records("PR162R_B_PR162RMissingActionIngestionLedger.report.json")
    assert len(rows) == summary["raw_missing_actions_consumed"] == 19506
    assert all(row["consumed_by_pr162r_b"] for row in rows)
