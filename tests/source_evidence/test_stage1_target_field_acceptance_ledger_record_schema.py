from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.source_evidence_acceptance_consumer_contract_check import (
    LEDGER_RECORD_TYPE,
    validate_static_surface,
    validate_target_field_ledger_record,
)


LEDGER_RECORD_SCHEMA = Path(
    "src/qtt/source_evidence/acceptance/stage1_target_field_acceptance_ledger_record.schema.json"
)
CONSUMER_CONTRACT_SCHEMA = Path(
    "src/qtt/source_evidence/acceptance/accepted_source_evidence_consumer_contract.schema.json"
)
EXPORT_RECORD_SCHEMA = Path(
    "src/qtt/source_evidence/acceptance/stage1_accepted_source_evidence_export_record.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/acceptance_consumer_contract/"
    "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger_records() -> list[dict]:
    return _load(FIXTURE)["target_field_acceptance_ledger_records"]


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_target_field_record_digest_scope_conflict_and_revalidation_fields_required():
    schema = _load(LEDGER_RECORD_SCHEMA)
    required = set(schema["required"])

    assert schema["additionalProperties"] is False
    assert (
        schema["properties"]["target_field_acceptance_ledger_record_type"]["const"]
        == LEDGER_RECORD_TYPE
    )
    assert {
        "target_field_acceptance_ledger_record_digest",
        "accepted_source_evidence_packet_digest",
        "target_field_path",
        "target_field_path_hash",
        "accepted_packet_applicability_scope",
        "accepted_packet_conflict_state",
        "accepted_packet_revalidation_due_condition",
        "accepted_packet_current_state",
        "authorized_consumer_task_ids",
        "consumer_contract_required_flag",
        "connector_semantic_binding_allowed_directly_from_ledger_flag",
        "runtime_resolver_snapshot_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "no_claim_flags",
    }.issubset(required)


def test_target_field_ledger_records_validate_synthetic_fixture_cases():
    assert validate_static_surface(repo_root=Path(".")) == []

    cases = {record["fixture_case"] for record in _ledger_records()}
    assert {
        "CURRENT_AUTHORIZED_NONLIVE",
        "BLOCKED_STALE",
        "BLOCKED_CONFLICT",
        "BLOCKED_TARGET_MISMATCH",
        "BLOCKED_UNDECLARED_CONSUMER",
        "BLOCKED_SUPERSEDED",
        "BLOCKED_SCHEMA_ERROR",
        "BLOCKED_FORBIDDEN_RUNTIME_ATTEMPT",
    }.issubset(cases)
    for record in _ledger_records():
        assert validate_target_field_ledger_record(record) == []
        assert record["consumer_contract_required_flag"] is True
        assert record["connector_semantic_binding_allowed_directly_from_ledger_flag"] is False
        assert record["runtime_resolver_snapshot_allowed_flag"] is False
        assert record["live_reachability_allowed_flag"] is False
        assert record["order_execution_allowed_flag"] is False
        assert record["runtime_cash_claim_allowed_flag"] is False


def test_target_field_ledger_validator_rejects_missing_hashes_and_digests():
    record = copy.deepcopy(_ledger_records()[0])
    record["target_field_path_hash"] = "0" * 64
    record["accepted_source_evidence_packet_digest"] = "not-a-digest"

    failures = validate_target_field_ledger_record(record)

    _assert_failure_contains(failures, "target_field_path_hash")
    _assert_failure_contains(failures, "accepted_source_evidence_packet_digest")


def test_target_field_ledger_cannot_directly_authorize_connector_consumption():
    record = copy.deepcopy(_ledger_records()[0])
    record["connector_semantic_binding_allowed_directly_from_ledger_flag"] = True

    failures = validate_target_field_ledger_record(record)

    _assert_failure_contains(
        failures,
        "connector_semantic_binding_allowed_directly_from_ledger_flag",
    )


def test_atomicrows_bundle_and_hash_remain_absent():
    assert Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()
