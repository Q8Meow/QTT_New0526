def test_paper_order_intents_are_paper_only(records, summary):
    rows = records("PR163_PaperOrderIntentRegistry.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["no_venue_order_id"] for row in rows[:100])
    assert all(row["no_order_submission"] for row in rows[:100])
