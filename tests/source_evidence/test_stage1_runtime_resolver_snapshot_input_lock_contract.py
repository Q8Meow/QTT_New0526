from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_runtime_resolver_snapshot_contract_check import (
    INPUT_LOCK_TYPE,
    REQUIRED_FIXTURE_CASES,
    VALID_INPUT_LOCK_STATE,
    validate_input_lock_record,
    validate_static_surface,
)


INPUT_LOCK_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_snapshot_input_lock.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/runtime_resolver/"
    "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _input_lock_by_case() -> dict[str, dict]:
    return {record["fixture_case"]: record for record in _fixture()["input_lock_records"]}


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_runtime_resolver_snapshot_input_lock_static_surface_validates():
    assert INPUT_LOCK_SCHEMA.exists()
    assert FIXTURE.exists()
    assert validate_static_surface(repo_root=Path(".")) == []

    fixture_cases = {
        record["fixture_case"] for record in _fixture()["input_lock_records"]
    } | {
        record["fixture_case"] for record in _fixture()["consumer_contract_records"]
    } | {
        record["fixture_case"] for record in _fixture()["snapshot_manifest_records"]
    }
    assert REQUIRED_FIXTURE_CASES.issubset(fixture_cases)


def test_input_lock_schema_requires_static_upstream_linkages_digests_scopes_and_no_runtime_flags():
    schema = _load(INPUT_LOCK_SCHEMA)
    required = set(schema["required"])
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["runtime_resolver_snapshot_input_lock_type"]["const"] == INPUT_LOCK_TYPE
    assert {
        "accepted_source_evidence_export_record_ids",
        "accepted_source_evidence_export_record_digests",
        "connector_semantic_binding_ledger_record_ids",
        "connector_semantic_binding_ledger_record_digests",
        "source_to_connector_field_binding_record_ids",
        "source_to_connector_field_binding_record_digests",
        "canonical_contract_venue_identity_normalization_record_ids",
        "canonical_contract_venue_identity_normalization_record_digests",
        "target_field_paths",
        "target_field_path_hashes",
        "venue_ids",
        "applicability_scope",
        "freshness_state",
        "runtime_resolver_snapshot_allowed_flag",
        "replay_paper_input_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
    }.issubset(required)


def test_valid_synthetic_static_input_lock_remains_blocked_static_only():
    record = _input_lock_by_case()["VALID_SYNTHETIC_STATIC_INPUT_LOCK"]

    assert record["input_lock_validation_state"] == VALID_INPUT_LOCK_STATE
    assert record["snapshot_creation_authority_state"] == "BLOCKED_STATIC_CONTRACT_ONLY"
    assert record["runtime_resolver_snapshot_allowed_flag"] is False
    assert record["replay_paper_input_allowed_flag"] is False
    assert record["live_reachability_allowed_flag"] is False
    assert record["order_execution_allowed_flag"] is False
    assert record["runtime_cash_claim_allowed_flag"] is False
    assert validate_input_lock_record(record) == []


def test_input_lock_blocks_stale_conflict_target_mismatch_missing_links_missing_digest_and_cross_venue():
    records = _input_lock_by_case()
    expected = {
        "BLOCKED_STALE_UPSTREAM_BINDING": "BLOCKED_STALE_UPSTREAM_BINDING",
        "BLOCKED_CONFLICT_UPSTREAM_BINDING": "BLOCKED_CONFLICT_UPSTREAM_BINDING",
        "BLOCKED_TARGET_MISMATCH": "BLOCKED_TARGET_MISMATCH",
        "BLOCKED_MISSING_ACCEPTED_SOURCE_EVIDENCE_EXPORT_LINKAGE": (
            "BLOCKED_MISSING_ACCEPTED_SOURCE_EVIDENCE_EXPORT_LINKAGE"
        ),
        "BLOCKED_MISSING_CONNECTOR_SEMANTIC_BINDING_LINKAGE": (
            "BLOCKED_MISSING_CONNECTOR_SEMANTIC_BINDING_LINKAGE"
        ),
        "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_FIELD_BINDING_LINKAGE": (
            "BLOCKED_MISSING_SOURCE_TO_CONNECTOR_FIELD_BINDING_LINKAGE"
        ),
        "BLOCKED_MISSING_DIGEST_OR_HASH": "BLOCKED_MISSING_DIGEST_OR_HASH",
        "BLOCKED_CROSS_VENUE_TARGET_FIELD_MISUSE": (
            "BLOCKED_CROSS_VENUE_TARGET_FIELD_MISUSE"
        ),
    }

    for case, state in expected.items():
        record = records[case]
        assert record["input_lock_validation_state"] == state
        assert record["blocker_codes"]
        assert record["runtime_resolver_snapshot_allowed_flag"] is False
        assert validate_input_lock_record(record) == []


def test_candidate_source_evidence_missing_digest_and_cross_venue_mutations_fail_closed():
    record = copy.deepcopy(_input_lock_by_case()["VALID_SYNTHETIC_STATIC_INPUT_LOCK"])
    record["candidate_source_evidence_packet_is_accepted_source_evidence_flag"] = True
    record["accepted_source_evidence_export_record_ids"] = [
        "CANDIDATE_SOURCE_EVIDENCE_PACKET_NOT_ACCEPTED"
    ]
    record["accepted_source_evidence_export_record_digests"] = [
        "MISSING_DIGEST"
    ]
    record["applicability_scope"]["requested_venue_id"] = "POLYMARKET"

    failures = validate_input_lock_record(record)

    _assert_failure_contains(failures, "candidate_source_evidence_packet_is_accepted_source_evidence_flag")
    _assert_failure_contains(failures, "candidate source evidence")
    _assert_failure_contains(failures, "digests")
    _assert_failure_contains(failures, "cross venue")
