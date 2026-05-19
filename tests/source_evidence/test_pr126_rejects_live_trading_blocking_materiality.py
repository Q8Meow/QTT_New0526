from tests.source_evidence.pr126_connector_semantic_implementation_support import (
    rejection_by_binding,
)


def test_pr126_rejects_live_trading_blocking_materiality():
    rejection = rejection_by_binding()["PR126_BINDING_LIVE_TRADING_BLOCKING"]

    assert rejection["implementation_gate_state"] == (
        "REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY"
    )
    assert rejection["rejection_reason_code"] == "LIVE_TRADING_BLOCKING_MATERIALITY"
    assert rejection["order_execution_allowed_flag"] is False
