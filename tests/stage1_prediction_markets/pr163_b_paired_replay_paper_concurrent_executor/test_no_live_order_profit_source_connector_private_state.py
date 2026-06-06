def test_no_live_order_profit_source_connector_private_state(summary):
    for field in ("live_order_authority_count", "profit_evidence_count", "source_acceptance_count", "connector_binding_count", "private_state_fetch_count", "runtime_cash_receipt_count"):
        assert summary[field] == 0
