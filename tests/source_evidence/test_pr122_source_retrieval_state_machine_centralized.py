from __future__ import annotations

import json
from pathlib import Path

from src.qtt.source_evidence.retrieval import controller


STATE_MACHINE = Path(
    "src/qtt/source_evidence/retrieval/source_retrieval_state_machine.json"
)
VALIDATOR = Path("tools/validate_source_evidence_retrieval_executor.py")
SCHEMA_DIR = Path("schemas/source_evidence/retrieval")
REPORT = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR122_SOURCE_EVIDENCE_RETRIEVAL_CONTROLLER_GATED_REPORT.json"
)


def _machine() -> dict:
    return json.loads(STATE_MACHINE.read_text(encoding="utf-8"))


def test_state_machine_defines_required_states_once_with_no_authority_flags():
    machine = _machine()
    states = controller.state_by_id(machine)

    assert controller.state_machine_failures(machine) == []
    assert len(states) == len(machine["state_records"])
    for required_state in (
        "OWNER_SOURCE_DEFINITIONS_PACKET_MISSING",
        "OWNER_SOURCE_DEFINITIONS_PACKET_PRESENT_NOT_APPROVED",
        "OWNER_SOURCE_DEFINITIONS_PACKET_APPROVED_FOR_RETRIEVAL_SCOPE",
        "SOURCE_TARGET_DECLARED_NOT_RETRIEVED",
        "SOURCE_RETRIEVAL_MANIFEST_READY",
        "SOURCE_RETRIEVAL_ATTEMPTED_FIXTURE_ONLY",
        "SOURCE_RETRIEVAL_ATTEMPTED_EXTERNAL_GATED_DISABLED",
        "SOURCE_RETRIEVED_CANDIDATE_RECEIPT_CREATED_NOT_ACCEPTED",
        "SOURCE_RETRIEVED_CANDIDATE_RECEIPT_CONFLICTED",
        "SOURCE_RETRIEVED_CANDIDATE_RECEIPT_STALE",
        "SOURCE_BLOCKED_SECRET_OR_PRIVATE_VALUE_DETECTED",
        "SOURCE_BLOCKED_PRIVATE_DOC_UNCLEAR_ACCESS_RIGHTS",
        "SOURCE_BLOCKED_NON_AUTHORITATIVE_SOURCE_CLASS",
        "SOURCE_ACCEPTANCE_REQUIRED_NOT_PERFORMED",
        "CONNECTOR_BINDING_BLOCKED_PENDING_ACCEPTED_TARGET_FIELD_PACKET",
        "RUNTIME_LIVE_USE_BLOCKED_PENDING_ACCEPTED_SOURCE_AND_CONNECTOR_BINDING",
        "QUANTUM_BACKEND_EXECUTION_BLOCKED_METADATA_ONLY",
    ):
        assert required_state in states

    for state in states.values():
        for flag in controller.FORCED_FALSE_AUTHORITY_FLAGS:
            assert state[flag] is False


def test_validator_loads_controller_instead_of_duplicating_blocker_meanings():
    validator_text = VALIDATOR.read_text(encoding="utf-8")
    machine = _machine()

    assert "from src.qtt.source_evidence.retrieval import controller" in validator_text
    for state in machine["state_records"]:
        assert state["block_reason_canonical"] not in validator_text


def test_schemas_do_not_create_parallel_state_meaning_definitions():
    machine = _machine()
    schema_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SCHEMA_DIR.glob("*.schema.json"))
    )

    assert "parallel readiness state" not in schema_text.lower()
    for state in machine["state_records"]:
        assert state["block_reason_canonical"] not in schema_text


def test_generated_report_references_central_state_ids_and_block_codes():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    block = report["source_retrieval_target_derivation_source"]
    receipt_path = Path(report["target_derivation_block_receipt"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert block["derivation_state"] == (
        "SOURCE_TARGET_DERIVATION_BLOCKED_AMBIGUOUS_CANONICAL_TARGET_RECORDS"
    )
    assert receipt["target_derivation_block"]["block_code"] == (
        "SOURCE_TARGET_DERIVATION_AMBIGUOUS_PENDING_CANONICAL_TARGET_RECORDS"
    )
    assert receipt["reason_loaded_from_central_state_machine"] is True
