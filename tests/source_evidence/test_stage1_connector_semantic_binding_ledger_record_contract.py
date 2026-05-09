from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess

from tools.stage1_connector_semantic_binding_ledger_check import (
    CONSUMABLE_STATE,
    LEDGER_RECORD_TYPE,
    REQUIRED_FIXTURE_CASES,
    build_report,
    validate_ledger_record,
    validate_static_surface,
)


LEDGER_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_binding_ledger_record.schema.json"
)
CANONICALIZATION_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_value_canonicalization.schema.json"
)
CONSUMER_CONTRACT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_binding_consumer_contract.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/connector_semantic_binding/"
    "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _ledger_by_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["connector_semantic_binding_ledger_records"]
    }


def _canonicalization_by_id() -> dict[str, dict]:
    return {
        record["semantic_value_canonicalization_record_id"]: record
        for record in _fixture()["semantic_value_canonicalization_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_connector_semantic_binding_static_surface_validates_synthetic_fixtures():
    for path in [LEDGER_SCHEMA, CANONICALIZATION_SCHEMA, CONSUMER_CONTRACT_SCHEMA, FIXTURE]:
        assert path.exists(), path

    assert validate_static_surface(repo_root=Path(".")) == []

    fixture = _fixture()
    cases = {
        record["fixture_case"]
        for record in fixture["connector_semantic_binding_ledger_records"]
    }
    assert REQUIRED_FIXTURE_CASES.issubset(cases)


def test_binding_ledger_record_requires_accepted_export_target_field_record_source_to_connector_record_and_no_live_flags():
    schema = _load(LEDGER_SCHEMA)
    required = set(schema["required"])
    props = schema["properties"]
    record = _ledger_by_case()["VALID_SYNTHETIC_BINDING_NONLIVE_ONLY"]

    assert props["connector_semantic_binding_ledger_record_type"]["const"] == LEDGER_RECORD_TYPE
    assert {
        "accepted_source_evidence_export_record_id",
        "target_field_acceptance_ledger_record_id",
        "source_to_connector_field_binding_record_id",
        "accepted_source_evidence_packet_digest",
        "target_field_acceptance_ledger_record_digest",
        "bound_value_original",
        "bound_value_canonical",
        "bound_value_type",
        "bound_value_unit_or_scale",
        "bound_value_scope",
        "stale_binding_invalidates_downstream_snapshot_flag",
        "rollback_receipt_required_flag",
        "consumer_contract_state",
        "live_client_import_allowed_flag",
        "network_io_allowed_flag",
        "order_execution_allowed_flag",
        "live_reachability_allowed_flag",
        "receipt_ids",
        "blocker_codes",
    }.issubset(required)

    assert record["consumer_contract_state"] == CONSUMABLE_STATE
    assert record["binding_packet_creation_allowed_flag"] is True
    assert record["blocker_codes"] == []
    assert record["stale_binding_invalidates_downstream_snapshot_flag"] is True
    assert record["rollback_receipt_required_flag"] is True
    assert record["live_client_import_allowed_flag"] is False
    assert record["network_io_allowed_flag"] is False
    assert record["order_execution_allowed_flag"] is False
    assert record["live_reachability_allowed_flag"] is False
    assert validate_ledger_record(record, canonicalization_records_by_id=_canonicalization_by_id()) == []


def test_ledger_blocks_stale_conflict_target_mismatch_schema_and_candidate_evidence():
    records = _ledger_by_case()
    expected = {
        "BLOCKED_STALE_BINDING": "BLOCKED_STALE",
        "BLOCKED_CONFLICT_BINDING": "BLOCKED_CONFLICT",
        "BLOCKED_TARGET_MISMATCH_BINDING": "BLOCKED_TARGET_MISMATCH",
        "BLOCKED_SCHEMA_ERROR_BINDING": "BLOCKED_SCHEMA_ERROR",
    }
    for case, state in expected.items():
        record = records[case]
        assert record["consumer_contract_state"] == state
        assert record["binding_packet_creation_allowed_flag"] is False
        assert record["blocker_codes"]
        assert validate_ledger_record(record, canonicalization_records_by_id=_canonicalization_by_id()) == []

    candidate = copy.deepcopy(records["VALID_SYNTHETIC_BINDING_NONLIVE_ONLY"])
    candidate["source_value_origin"] = "CANDIDATE_SOURCE_EVIDENCE_PACKET_NOT_ACCEPTED"
    failures = validate_ledger_record(candidate, canonicalization_records_by_id=_canonicalization_by_id())
    _assert_failure_contains(failures, "source_value_origin")


def test_ledger_rejects_missing_linkage_as_consumable():
    record = copy.deepcopy(_ledger_by_case()["VALID_SYNTHETIC_BINDING_NONLIVE_ONLY"])
    record["accepted_source_evidence_export_record_id"] = "MISSING_ACCEPTED_SOURCE_EVIDENCE_EXPORT_RECORD"

    failures = validate_ledger_record(record, canonicalization_records_by_id=_canonicalization_by_id())

    _assert_failure_contains(failures, "all linkage records")


def test_ledger_report_remains_static_blocked_and_reports_no_live_violations():
    fixture = _fixture()
    report = build_report(fixture=fixture, repo_root=Path("."), validation_failures=[])

    assert report["report_type"] == "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_CHECK_REPORT"
    assert report["gate_state"] == "BLOCKED"
    assert report["binding_ledger_record_count"] == len(
        fixture["connector_semantic_binding_ledger_records"]
    )
    assert report["accepted_export_record_missing_count"] == 1
    assert report["target_field_ledger_record_missing_count"] == 1
    assert report["source_to_connector_binding_record_missing_count"] == 1
    assert report["forbidden_live_client_import_count"] == 0
    assert report["network_io_violation_count"] == 0
    assert report["order_execution_violation_count"] == 0
    assert report["live_reachability_violation_count"] == 0
    assert report["runtime_snapshot_direct_creation_violation_count"] == 0


def test_atomicrows_bundle_hash_and_master_plan_remain_absent_or_unchanged():
    assert not Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()

    completed = subprocess.run(
        ["git", "diff", "--", "docs/master_plan/QTT_MasterPlan_Current.md"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
