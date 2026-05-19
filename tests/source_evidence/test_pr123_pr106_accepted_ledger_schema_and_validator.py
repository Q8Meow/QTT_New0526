import json
from pathlib import Path

from src.qtt.source_evidence.acceptance import validator as acceptance

from ._pr123_acceptance_helpers import execute, valid_candidate


def test_accepted_ledger_schema_and_validator_cover_required_fields():
    schema = json.loads(
        Path(
            "schemas/source_evidence/acceptance/accepted_source_evidence_ledger.schema.json"
        ).read_text(encoding="utf-8")
    )
    result = execute(valid_candidate())

    assert result.accepted_ledger_record is not None
    assert acceptance.validate_ledger_record(result.accepted_ledger_record) == []
    required = set(schema["required"])
    for field in (
        "accepted_ledger_record_id",
        "accepted_source_evidence_packet_id",
        "target_field_path",
        "source_locator",
        "source_locator_type",
        "source_digest_sha256",
        "connector_semantic_unlock_allowed_flag",
        "runtime_live_use_allowed_flag",
        "order_authority_allowed_flag",
        "profit_evidence_allowed_flag",
        "quantum_backend_execution_allowed_flag",
        "production_external_fact_authority",
    ):
        assert field in required
        assert field in result.accepted_ledger_record
