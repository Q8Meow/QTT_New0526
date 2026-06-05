def test_paper_order_state_machine_has_required_terminal_states(records):
    rows = records("PR163_PaperOrderStateTransitionRegistry.report.json")
    states = {row["next_state"] for row in rows}
    assert "FILLED" in states
    assert "RESTING" in states
    assert "CANCELLED" in states
    assert "REJECTED" in states
    assert "SYNTHETIC_SETTLED_FOR_FIXTURE_ACCOUNTING_ONLY" in states
