from src.qtt.source_evidence.acceptance import validator as acceptance

from ._pr123_acceptance_helpers import execute, valid_candidate


def test_acceptance_executor_accepts_valid_fixture_candidate():
    result = execute(valid_candidate())

    assert result.decision_receipt["decision"] == "ACCEPTED"
    assert result.accepted_packet is not None
    assert result.accepted_ledger_record is not None
    assert result.reject_receipt is None
    assert acceptance.validate_decision_receipt(result.decision_receipt) == []
    assert acceptance.validate_accepted_packet(result.accepted_packet) == []
    assert acceptance.validate_ledger_record(result.accepted_ledger_record) == []
    assert result.accepted_packet["accepted_packet_record_type"] == (
        "ACCEPTED_SOURCE_EVIDENCE_PACKET"
    )
    assert result.accepted_packet["no_connector_semantic_population_flag"] is True
    assert result.accepted_ledger_record["connector_semantic_unlock_allowed_flag"] is False
