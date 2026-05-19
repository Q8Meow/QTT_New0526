import json
from pathlib import Path

from src.qtt.source_evidence.acceptance import validator as acceptance

from ._pr123_acceptance_helpers import execute, mutated_candidate, valid_candidate


def test_acceptance_decision_receipt_schema_and_validator_cover_accept_and_reject():
    schema = json.loads(
        Path(
            "schemas/source_evidence/acceptance/acceptance_decision_receipt.schema.json"
        ).read_text(encoding="utf-8")
    )
    accepted = execute(valid_candidate()).decision_receipt
    rejected = execute(mutated_candidate("MISSING_DIGEST")).decision_receipt

    assert acceptance.validate_decision_receipt(accepted) == []
    assert acceptance.validate_decision_receipt(rejected) == []
    for field in (
        "acceptance_decision_packet_id",
        "decision",
        "candidate_source_evidence_packet_id",
        "accepted_source_evidence_packet_id",
        "accepted_ledger_record_id",
        "rejection_codes",
        "connector_semantic_binding_created_count",
        "runtime_live_authority_created",
        "order_authority_created",
        "profit_evidence_created",
        "quantum_backend_execution_count",
    ):
        assert field in schema["required"]
        assert field in accepted
        assert field in rejected
