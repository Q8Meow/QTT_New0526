from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_runtime_resolver_snapshot_contract_check import (
    MANIFEST_TYPE,
    build_report,
    validate_manifest_record,
    validate_static_surface,
)


MANIFEST_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_snapshot_manifest.schema.json"
)
GATE_REPORT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_snapshot_gate_report.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/runtime_resolver/"
    "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _manifest_by_case() -> dict[str, dict]:
    return {record["fixture_case"]: record for record in _fixture()["snapshot_manifest_records"]}


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_manifest_schema_contains_required_snapshot_gate_contract_fields_and_false_authority_flags():
    schema = _load(MANIFEST_SCHEMA)
    required = set(schema["required"])
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["runtime_resolver_snapshot_manifest_type"]["const"] == MANIFEST_TYPE
    assert {
        "snapshot_creation_authority_state",
        "input_lock_id",
        "input_lock_digest",
        "connector_semantic_binding_ledger_record_ids",
        "connector_semantic_binding_ledger_record_digests",
        "accepted_source_evidence_export_record_ids",
        "accepted_source_evidence_export_record_digests",
        "source_to_connector_field_binding_record_ids",
        "venue_ids",
        "target_field_paths",
        "target_field_path_hashes",
        "applicability_scope",
        "revalidation_state",
        "conflict_state",
        "contract_normalization_state",
        "consumer_authorization_state",
        "runtime_resolver_snapshot_allowed_flag",
        "replay_paper_input_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "blocker_codes",
        "receipt_ids",
    }.issubset(required)


def test_manifest_fixture_and_report_remain_blocked_static_only():
    assert validate_static_surface(repo_root=Path(".")) == []

    fixture = _fixture()
    record = _manifest_by_case()["VALID_SYNTHETIC_STATIC_INPUT_LOCK"]
    report = build_report(fixture=fixture, repo_root=Path("."), validation_failures=[])

    assert record["snapshot_creation_authority_state"] == "BLOCKED_STATIC_CONTRACT_ONLY"
    assert record["runtime_resolver_snapshot_allowed_flag"] is False
    assert validate_manifest_record(record) == []
    assert report["gate_state"] == "BLOCKED_STATIC_CONTRACT_ONLY"
    assert report["runtime_resolver_snapshot_allowed_flag"] is False
    assert report["replay_paper_input_allowed_flag"] is False
    assert report["live_reachability_allowed_flag"] is False
    assert report["order_execution_allowed_flag"] is False
    assert report["runtime_cash_claim_allowed_flag"] is False


def test_snapshot_manifest_gate_report_schema_is_static_blocked_only():
    schema = _load(GATE_REPORT_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["runtime_resolver_snapshot_gate_report_type"]["const"] == (
        "STAGE1_RUNTIME_RESOLVER_SNAPSHOT_GATE_REPORT"
    )
    assert props["snapshot_creation_authority_state"]["const"] == (
        "BLOCKED_STATIC_CONTRACT_ONLY"
    )
    assert props["runtime_resolver_snapshot_allowed_flag"]["const"] is False
    assert props["replay_paper_input_allowed_flag"]["const"] is False
    assert props["live_reachability_allowed_flag"]["const"] is False
    assert props["order_execution_allowed_flag"]["const"] is False
    assert props["runtime_cash_claim_allowed_flag"]["const"] is False


def test_manifest_rejects_future_snapshot_authority_and_runtime_consumption_flags():
    record = copy.deepcopy(_manifest_by_case()["VALID_SYNTHETIC_STATIC_INPUT_LOCK"])
    record["snapshot_creation_authority_state"] = "ELIGIBLE_FOR_FUTURE_SNAPSHOT_GATE_ONLY"
    record["runtime_resolver_snapshot_allowed_flag"] = True
    record["replay_paper_input_allowed_flag"] = True
    record["live_reachability_allowed_flag"] = True
    record["order_execution_allowed_flag"] = True
    record["runtime_cash_claim_allowed_flag"] = True

    failures = validate_manifest_record(record)

    _assert_failure_contains(failures, "snapshot_creation_authority_state")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_allowed_flag")
    _assert_failure_contains(failures, "replay_paper_input_allowed_flag")
    _assert_failure_contains(failures, "live_reachability_allowed_flag")
    _assert_failure_contains(failures, "order_execution_allowed_flag")
    _assert_failure_contains(failures, "runtime_cash_claim_allowed_flag")


def test_atomicrows_bundle_and_hash_remain_absent_for_manifest_gate():
    assert Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()
