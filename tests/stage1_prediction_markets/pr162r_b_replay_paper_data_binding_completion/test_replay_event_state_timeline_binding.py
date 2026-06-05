def test_replay_event_state_timeline_binding(summary, records):
    rows = records("PR162R_B_ReplayEventStateTimelineBindingRegistry.report.json")
    assert len(rows) == summary["replay_event_state_timeline_binding_count"] > 0
