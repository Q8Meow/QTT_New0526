def test_no_source_acceptance_connector_private_state(summary, records):
    rows = records("PR163_NoSourceAcceptanceConnectorPrivateStateAudit.report.json")
    assert rows[0]["source_acceptance_count"] == 0
    assert rows[0]["connector_binding_count"] == 0
    assert rows[0]["private_state_fetch_count"] == 0
    assert summary["runtime_cash_receipt_count"] == 0
