def test_no_source_acceptance_connector_private_state(summary):
    assert summary["source_acceptance_count"] == 0
    assert summary["connector_binding_count"] == 0
    assert summary["private_state_fetch_count"] == 0
    assert summary["runtime_cash_receipt_count"] == 0
