from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_preserves_pr115_pr116_pr117_downstream_paths():
    handoff = support.downstream_handoff()

    assert handoff["downstream_prs"] == ["PR115", "PR116", "PR117"]
    assert handoff["downstream_pr115_contract_prepared"] is True
    assert handoff["downstream_pr116_contract_prepared"] is True
    assert handoff["downstream_pr117_contract_prepared"] is True
    assert handoff["downstream_pr115_execution_authorized"] is False
    assert handoff["downstream_pr116_execution_authorized"] is False
    assert handoff["downstream_pr117_execution_authorized"] is False
