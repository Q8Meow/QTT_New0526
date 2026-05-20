from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_preserves_pr116_pr117_downstream_paths():
    handoff = support.handoff()
    assert handoff["downstream_prs"] == ["PR116", "PR117"]
    assert handoff["downstream_pr116_contract_prepared"] is True
    assert handoff["downstream_pr117_contract_prepared"] is True
    assert handoff["downstream_pr116_execution_authorized"] is False
    assert handoff["downstream_pr117_execution_authorized"] is False
