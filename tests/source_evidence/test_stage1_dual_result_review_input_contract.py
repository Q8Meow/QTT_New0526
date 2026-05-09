from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_dual_result_review_contract_check import (
    INPUT_CONTRACT_TYPE,
    REQUIRED_FIXTURE_CASES,
    validate_gate_case_record,
    validate_input_contract_record,
    validate_static_surface,
)


INPUT_CONTRACT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/dual_result_review/"
    "stage1_dual_result_review_input_contract.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/dual_result_review/"
    "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _input_contract() -> dict:
    return copy.deepcopy(_fixture()["dual_result_review_input_contract_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["dual_result_review_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_dual_result_review_static_surface_validates_and_contains_required_cases():
    assert INPUT_CONTRACT_SCHEMA.exists()
    assert FIXTURE.exists()
    assert validate_static_surface(repo_root=Path(".")) == []

    fixture = _fixture()
    fixture_cases = {
        record["fixture_case"]
        for key in [
            "dual_result_review_input_contract_records",
            "replay_paper_comparison_matrix_records",
            "owner_live_promotion_handoff_block_records",
            "dual_result_review_gate_case_records",
        ]
        for record in fixture[key]
    }
    assert REQUIRED_FIXTURE_CASES.issubset(fixture_cases)


def test_input_contract_schema_requires_separate_replay_paper_boundaries_and_matching_identity():
    schema = _load(INPUT_CONTRACT_SCHEMA)
    props = schema["properties"]
    required = set(schema["required"])

    assert schema["additionalProperties"] is False
    assert props["dual_result_review_input_contract_type"]["const"] == INPUT_CONTRACT_TYPE
    assert {
        "concurrent_replay_paper_execution_gate_report_ref",
        "replay_result_packet_boundary_ref",
        "paper_result_packet_boundary_ref",
        "replay_paper_input_identity_digest",
        "replay_lane_replay_paper_input_identity_digest",
        "paper_lane_replay_paper_input_identity_digest",
        "runtime_resolver_snapshot_id",
        "runtime_resolver_snapshot_digest",
        "replay_result_reference_immutable_flag",
        "paper_result_reference_immutable_flag",
        "review_decision_created_flag",
        "result_merge_created_flag",
        "auto_promotion_allowed_flag",
    }.issubset(required)
    assert props["review_decision_created_flag"]["const"] is False
    assert props["result_merge_created_flag"]["const"] is False
    assert props["auto_promotion_allowed_flag"]["const"] is False


def test_input_contract_references_separate_immutable_replay_and_paper_boundaries():
    record = _input_contract()

    assert record["replay_result_packet_boundary_ref"] != record["paper_result_packet_boundary_ref"]
    assert (
        record["replay_paper_input_identity_digest"]
        == record["replay_lane_replay_paper_input_identity_digest"]
        == record["paper_lane_replay_paper_input_identity_digest"]
    )
    assert (
        record["runtime_resolver_snapshot_id"]
        == record["replay_runtime_resolver_snapshot_id"]
        == record["paper_runtime_resolver_snapshot_id"]
    )
    assert (
        record["runtime_resolver_snapshot_digest"]
        == record["replay_runtime_resolver_snapshot_digest"]
        == record["paper_runtime_resolver_snapshot_digest"]
    )
    assert record["replay_result_reference_immutable_flag"] is True
    assert record["paper_result_reference_immutable_flag"] is True
    assert validate_input_contract_record(record) == []


def test_input_contract_rejects_missing_boundaries_digest_mismatch_stale_conflict_schema_lane_and_target():
    record = _input_contract()
    record["replay_result_packet_boundary_ref"] = ""
    record["paper_result_packet_boundary_ref"] = ""
    record["replay_paper_input_identity_digest"] = ""
    record["paper_lane_replay_paper_input_identity_digest"] = (
        "9999999999999999999999999999999999999999999999999999999999999999"
    )
    record["paper_runtime_resolver_snapshot_id"] = "SYNTHETIC_DIFFERENT_RUNTIME_SNAPSHOT"
    record["paper_runtime_resolver_snapshot_digest"] = (
        "8888888888888888888888888888888888888888888888888888888888888888"
    )
    record["replay_result_boundary_state"] = "STALE"
    record["paper_result_boundary_state"] = "STALE"
    record["conflict_state"] = "CONFLICT_PRESENT"
    record["schema_state"] = "SCHEMA_ERROR"
    record["lane_match_state"] = "MISMATCH"
    record["target_match_state"] = "MISMATCH"

    failures = validate_input_contract_record(record)

    for fragment in [
        "replay_result_packet_boundary_ref must be present",
        "paper_result_packet_boundary_ref must be present",
        "replay_paper_input_identity_digest must be present",
        "paper lane input identity digest must match",
        "paper runtime resolver snapshot id must match",
        "paper runtime resolver snapshot digest must match",
        "replay_result_boundary_state must be PRESENT_IMMUTABLE",
        "paper_result_boundary_state must be PRESENT_IMMUTABLE",
        "conflict_state must be NO_CONFLICT",
        "schema_state must be SCHEMA_VALID",
        "lane_match_state must be MATCH",
        "target_match_state must be MATCH",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_missing_result_boundaries_identity_and_snapshot_mismatches():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_MISSING_REPLAY_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_REPLAY_RESULT_BOUNDARY_MISSING",
        "BLOCKED_MISSING_PAPER_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_PAPER_RESULT_BOUNDARY_MISSING",
        "BLOCKED_MISSING_INPUT_IDENTITY_DIGEST": "BLOCKED_DUAL_REVIEW_INPUT_IDENTITY_DIGEST_MISSING",
        "BLOCKED_MISMATCHED_REPLAY_PAPER_INPUT_IDENTITY_DIGEST": "BLOCKED_DUAL_REVIEW_INPUT_IDENTITY_MISMATCH",
        "BLOCKED_MISMATCHED_RUNTIME_RESOLVER_SNAPSHOT_ID": "BLOCKED_DUAL_REVIEW_RUNTIME_RESOLVER_SNAPSHOT_ID_MISMATCH",
        "BLOCKED_MISMATCHED_RUNTIME_RESOLVER_SNAPSHOT_DIGEST": "BLOCKED_DUAL_REVIEW_RUNTIME_RESOLVER_SNAPSHOT_DIGEST_MISMATCH",
        "BLOCKED_STALE_REPLAY_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_STALE_REPLAY_RESULT_BOUNDARY",
        "BLOCKED_STALE_PAPER_RESULT_BOUNDARY": "BLOCKED_DUAL_REVIEW_STALE_PAPER_RESULT_BOUNDARY",
        "BLOCKED_CONFLICT_STATE": "BLOCKED_DUAL_REVIEW_CONFLICT_STATE",
        "BLOCKED_SCHEMA_ERROR_STATE": "BLOCKED_DUAL_REVIEW_SCHEMA_ERROR",
        "BLOCKED_LANE_MISMATCH": "BLOCKED_DUAL_REVIEW_LANE_MISMATCH",
        "BLOCKED_TARGET_MISMATCH": "BLOCKED_DUAL_REVIEW_TARGET_MISMATCH",
    }

    for fixture_case, expected_state in expected.items():
        record = cases[fixture_case]
        assert record["expected_gate_state"] == expected_state
        assert record["blocker_codes"]
        assert validate_gate_case_record(record) == []
