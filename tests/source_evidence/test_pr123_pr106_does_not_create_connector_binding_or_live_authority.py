from ._pr123_acceptance_helpers import execute, valid_candidate


def test_acceptance_executor_does_not_create_connector_binding_or_live_authority():
    result = execute(valid_candidate())

    assert result.decision_receipt["connector_semantic_binding_created_count"] == 0
    assert result.decision_receipt["runtime_live_authority_created"] is False
    assert result.decision_receipt["order_authority_created"] is False
    assert result.decision_receipt["profit_evidence_created"] is False
    assert result.decision_receipt["quantum_backend_execution_count"] == 0
    assert result.accepted_packet is not None
    assert result.accepted_ledger_record is not None
    assert result.accepted_packet["no_live_reachability_flag"] is True
    assert result.accepted_packet["no_order_execution_flag"] is True
    assert result.accepted_packet["no_runtime_cash_claim_flag"] is True
    assert result.accepted_ledger_record["runtime_live_use_allowed_flag"] is False
    assert result.accepted_ledger_record["order_authority_allowed_flag"] is False
    assert result.accepted_ledger_record["profit_evidence_allowed_flag"] is False
    assert result.accepted_ledger_record["quantum_backend_execution_allowed_flag"] is False
