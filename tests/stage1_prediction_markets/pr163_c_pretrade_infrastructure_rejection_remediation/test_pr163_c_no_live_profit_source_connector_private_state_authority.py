from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_no_live_profit_source_connector_private_state_authority():
    audit = load_records("PR163_C_NoLiveProfitSourceConnectorPrivateStateAudit.report.json")[0]
    assert audit["live_order_authority_count"] == 0
    assert summary()["private_state_fetch_count"] == 0
    assert summary()["runtime_cash_receipt_count"] == 0
    assert summary()["source_acceptance_count"] == 0
    assert summary()["connector_binding_count"] == 0
