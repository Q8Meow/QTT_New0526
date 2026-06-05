def test_online_source_scout_queue(summary, records):
    rows = records("PR162R_OnlineSourceScoutQueue.report.json")
    assert len(rows) == summary["online_source_scout_queue_row_count"]
    assert rows
    for row in rows[:25]:
        assert row["target_field"]
        assert row["expected_unit"]
        assert row["expected_scale"]
        assert row["responsible_agent"]
        assert row["replay_impact"]
        assert row["paper_impact"]
        assert row["ci_network_required_flag"] is False
