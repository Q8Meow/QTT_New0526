from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess

from tools.source_evidence_acceptance_consumer_contract_check import (
    AUTHORIZED_STATE,
    CONSUMER_CONTRACT_TYPE,
    EXPORT_RECORD_TYPE,
    VALIDATION_HOOK,
    validate_consumer_contract_record,
    validate_export_record,
    validate_static_surface,
)


CONSUMER_CONTRACT_SCHEMA = Path(
    "src/qtt/source_evidence/acceptance/accepted_source_evidence_consumer_contract.schema.json"
)
EXPORT_RECORD_SCHEMA = Path(
    "src/qtt/source_evidence/acceptance/stage1_accepted_source_evidence_export_record.schema.json"
)
LEDGER_RECORD_SCHEMA = Path(
    "src/qtt/source_evidence/acceptance/stage1_target_field_acceptance_ledger_record.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/acceptance_consumer_contract/"
    "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _current_export() -> dict:
    return next(
        record
        for record in _fixture()["accepted_source_evidence_export_records"]
        if record["fixture_case"] == "CURRENT_AUTHORIZED_NONLIVE"
    )


def _current_contract() -> dict:
    return next(
        record
        for record in _fixture()["consumer_contract_records"]
        if record["fixture_case"] == "CURRENT_AUTHORIZED_NONLIVE"
    )


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_consumer_contract_artifacts_exist_and_validate_synthetic_fixture():
    for path in [CONSUMER_CONTRACT_SCHEMA, EXPORT_RECORD_SCHEMA, LEDGER_RECORD_SCHEMA, FIXTURE]:
        assert path.exists(), path

    assert (
        validate_static_surface(
            repo_root=Path("."),
            consumer_contract_schema_path=CONSUMER_CONTRACT_SCHEMA,
            target_field_ledger_schema_path=LEDGER_RECORD_SCHEMA,
            export_record_schema_path=EXPORT_RECORD_SCHEMA,
            fixture_path=FIXTURE,
        )
        == []
    )


def test_export_record_authorizes_only_declared_target_field_and_consumer_task():
    record = _current_export()

    assert record["accepted_source_evidence_export_record_type"] == EXPORT_RECORD_TYPE
    assert record["consumer_authorization_state"] == AUTHORIZED_STATE
    assert record["connector_semantic_binding_allowed_flag"] is True
    assert record["requested_consumer_task_id"] in record["authorized_consumer_task_ids"]
    assert record["requested_target_field_path"] == record["target_field_path"]
    assert record["runtime_resolver_snapshot_allowed_flag"] is False
    assert record["live_reachability_allowed_flag"] is False
    assert record["order_execution_allowed_flag"] is False
    assert record["runtime_cash_claim_allowed_flag"] is False
    assert validate_export_record(record) == []


def test_candidate_evidence_packet_is_blocked_as_accepted_evidence():
    record = copy.deepcopy(_current_export())
    record["accepted_source_evidence_packet_version"] = "CANDIDATE_SOURCE_PACKET_NOT_ACCEPTED"
    record["accepted_source_evidence_packet_authority_class"] = (
        "CANDIDATE_SOURCE_PACKET_NOT_ACCEPTED"
    )

    failures = validate_export_record(record)

    _assert_failure_contains(failures, "accepted_source_evidence_packet_version")
    _assert_failure_contains(failures, "candidate")


def test_consumer_contract_schema_is_static_closed_and_nonlive_only():
    schema = _load(CONSUMER_CONTRACT_SCHEMA)
    props = schema["properties"]
    required = set(schema["required"])

    assert schema["additionalProperties"] is False
    assert props["accepted_source_evidence_consumer_contract_type"]["const"] == CONSUMER_CONTRACT_TYPE
    assert props["runtime_resolver_snapshot_allowed_flag"]["const"] is False
    assert props["live_reachability_allowed_flag"]["const"] is False
    assert props["order_execution_allowed_flag"]["const"] is False
    assert props["runtime_cash_claim_allowed_flag"]["const"] is False
    assert props["connector_semantic_value_population_allowed_flag"]["const"] is False
    assert props["nonlive_schema_level_downstream_work_only_flag"]["const"] is True
    assert {
        "requested_consumer_task_id",
        "requested_target_field_path",
        "authorized_consumer_task_ids",
        "candidate_evidence_packet_is_accepted_source_evidence_flag",
        "consumer_authorization_state",
        "connector_semantic_binding_allowed_flag",
        "validation_hook_ids",
    }.issubset(required)


def test_consumer_contract_record_blocks_candidate_packet_authority():
    record = copy.deepcopy(_current_contract())
    record["candidate_evidence_packet_is_accepted_source_evidence_flag"] = True

    failures = validate_consumer_contract_record(record)

    _assert_failure_contains(
        failures,
        "candidate_evidence_packet_is_accepted_source_evidence_flag",
    )


def test_consumer_contract_validation_hook_is_pr39_static_audit_only():
    record = _current_contract()

    assert record["validation_hook_ids"] == [VALIDATION_HOOK]
    assert record["no_claim_flags"]["accepts_source_facts"] is False
    assert record["no_claim_flags"]["creates_real_accepted_source_evidence"] is False
    assert record["no_claim_flags"]["populates_connector_semantic_values"] is False


def test_master_plan_remains_unchanged():
    completed = subprocess.run(
        ["git", "diff", "--", "docs/master_plan/QTT_MasterPlan_Current.md"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
