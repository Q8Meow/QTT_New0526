from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.source_evidence_acceptance_consumer_contract_check import (
    AUTHORIZED_STATE,
    BLOCKED_CONFLICT,
    BLOCKED_CONSUMER_NOT_DECLARED,
    BLOCKED_STALE,
    BLOCKED_TARGET_MISMATCH,
    validate_export_record,
    validate_static_surface,
)


FIXTURE = Path(
    "tests/fixtures/source_evidence/acceptance_consumer_contract/"
    "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _exports_by_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["accepted_source_evidence_export_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_stale_conflicted_wildcard_cross_venue_and_runtime_resolver_direct_consumption_are_blocked():
    records = _exports_by_case()
    expected_states = {
        "BLOCKED_STALE": BLOCKED_STALE,
        "BLOCKED_SUPERSEDED": BLOCKED_STALE,
        "BLOCKED_CONFLICT": BLOCKED_CONFLICT,
        "BLOCKED_SCHEMA_ERROR": BLOCKED_CONFLICT,
        "BLOCKED_FORBIDDEN_RUNTIME_ATTEMPT": BLOCKED_CONFLICT,
    }

    for case, expected_state in expected_states.items():
        record = records[case]
        assert record["consumer_authorization_state"] == expected_state
        assert record["connector_semantic_binding_allowed_flag"] is False
        assert record["runtime_resolver_snapshot_allowed_flag"] is False
        assert record["live_reachability_allowed_flag"] is False
        assert record["order_execution_allowed_flag"] is False
        assert record["runtime_cash_claim_allowed_flag"] is False
        assert record["accepted_packet_applicability_scope"]["wildcard_scope_allowed"] is False
        assert record["accepted_packet_applicability_scope"]["cross_venue_scope_allowed"] is False
        assert validate_export_record(record) == []


def test_target_mismatch_blocks_connector_semantic_consumption():
    record = _exports_by_case()["BLOCKED_TARGET_MISMATCH"]

    assert record["requested_target_field_path"] != record["target_field_path"]
    assert record["consumer_authorization_state"] == BLOCKED_TARGET_MISMATCH
    assert record["connector_semantic_binding_allowed_flag"] is False
    assert validate_export_record(record) == []


def test_undeclared_consumer_blocks_connector_semantic_consumption():
    record = _exports_by_case()["BLOCKED_UNDECLARED_CONSUMER"]

    assert record["requested_consumer_task_id"] not in record["authorized_consumer_task_ids"]
    assert record["consumer_authorization_state"] == BLOCKED_CONSUMER_NOT_DECLARED
    assert record["connector_semantic_binding_allowed_flag"] is False
    assert validate_export_record(record) == []


def test_runtime_resolver_live_order_runtime_cash_and_profit_claims_are_blocked():
    record = copy.deepcopy(_exports_by_case()["CURRENT_AUTHORIZED_NONLIVE"])
    record["runtime_resolver_snapshot_allowed_flag"] = True
    record["live_reachability_allowed_flag"] = True
    record["order_execution_allowed_flag"] = True
    record["runtime_cash_claim_allowed_flag"] = True
    record["no_claim_flags"]["creates_profit_evidence"] = True

    failures = validate_export_record(record)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_allowed_flag")
    _assert_failure_contains(failures, "live_reachability_allowed_flag")
    _assert_failure_contains(failures, "order_execution_allowed_flag")
    _assert_failure_contains(failures, "runtime_cash_claim_allowed_flag")
    _assert_failure_contains(failures, "creates_profit_evidence")


def test_unauthorized_over_scope_mutations_fail_closed():
    record = copy.deepcopy(_exports_by_case()["CURRENT_AUTHORIZED_NONLIVE"])
    record["requested_target_field_path"] = "synthetic.connector.other_field"
    record["consumer_authorization_state"] = AUTHORIZED_STATE
    record["connector_semantic_binding_allowed_flag"] = True

    failures = validate_export_record(record)

    _assert_failure_contains(failures, BLOCKED_TARGET_MISMATCH)

    record = copy.deepcopy(_exports_by_case()["CURRENT_AUTHORIZED_NONLIVE"])
    record["requested_consumer_task_id"] = "UNDECLARED_STAGE1_RUNTIME_RESOLVER_TASK"
    record["consumer_authorization_state"] = AUTHORIZED_STATE
    record["connector_semantic_binding_allowed_flag"] = True

    failures = validate_export_record(record)

    _assert_failure_contains(failures, BLOCKED_CONSUMER_NOT_DECLARED)


def test_validator_fails_when_atomicrows_bundle_or_hash_exists(tmp_path):
    bundle = tmp_path / "docs" / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
    bundle.parent.mkdir(parents=True)
    bundle.write_text("{}\n", encoding="utf-8")

    failures = validate_static_surface(repo_root=tmp_path)

    _assert_failure_contains(failures, "canonical AtomicRows bundle")
