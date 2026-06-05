def test_agent_replay_paper_handoff(summary, records):
    rows = records("PR162R_QKUAgentReplayPaperHandoffMatrix.report.json")
    assert len(rows) == summary["qku_agent_replay_paper_handoff_rows_count"]
    assert rows
    for row in rows[:25]:
        assert row["upstream_refs"]
        assert row["downstream_refs"]
        assert row["replay_adapter_input_ref"]
        assert row["paper_adapter_input_ref"]
        assert row["orphan_flag"] is False
