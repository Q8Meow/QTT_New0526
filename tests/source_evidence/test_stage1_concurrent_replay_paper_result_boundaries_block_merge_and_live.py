from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_concurrent_replay_paper_contract_check import (
    PAPER_RESULT_BOUNDARY_TYPE,
    REPLAY_RESULT_BOUNDARY_TYPE,
    build_report,
    validate_gate_case_record,
    validate_result_boundary_record,
)


REPLAY_RESULT_BOUNDARY_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "replay_result_packet_boundary.schema.json"
)
PAPER_RESULT_BOUNDARY_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "paper_result_packet_boundary.schema.json"
)
GATE_REPORT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/replay_paper/"
    "concurrent_replay_paper_execution_gate_report.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/replay_paper/"
    "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _replay_boundary() -> dict:
    return copy.deepcopy(_fixture()["replay_result_packet_boundary_records"][0])


def _paper_boundary() -> dict:
    return copy.deepcopy(_fixture()["paper_result_packet_boundary_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["execution_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_result_boundary_schemas_block_replay_paper_packet_creation_merge_review_and_live():
    replay_schema = _load(REPLAY_RESULT_BOUNDARY_SCHEMA)
    paper_schema = _load(PAPER_RESULT_BOUNDARY_SCHEMA)
    report_schema = _load(GATE_REPORT_SCHEMA)

    assert replay_schema["additionalProperties"] is False
    assert paper_schema["additionalProperties"] is False
    assert replay_schema["properties"]["replay_result_packet_boundary_type"]["const"] == (
        REPLAY_RESULT_BOUNDARY_TYPE
    )
    assert paper_schema["properties"]["paper_result_packet_boundary_type"]["const"] == (
        PAPER_RESULT_BOUNDARY_TYPE
    )
    assert replay_schema["properties"]["replay_result_packet_creation_authority_state"]["const"] == (
        "BLOCKED_STATIC_CONTRACT_ONLY"
    )
    assert paper_schema["properties"]["paper_result_packet_creation_authority_state"]["const"] == (
        "BLOCKED_STATIC_CONTRACT_ONLY"
    )
    assert replay_schema["properties"]["replay_lane_execution_allowed_flag"]["const"] is False
    assert paper_schema["properties"]["paper_lane_execution_allowed_flag"]["const"] is False
    assert replay_schema["properties"]["replay_result_packet_created_flag"]["const"] is False
    assert paper_schema["properties"]["paper_result_packet_created_flag"]["const"] is False
    assert report_schema["properties"]["result_merge_created_flag"]["const"] is False
    assert report_schema["properties"]["dual_result_review_created_flag"]["const"] is False
    assert report_schema["properties"]["owner_live_promotion_review_created_flag"]["const"] is False
    assert report_schema["properties"]["live_reachability_created_flag"]["const"] is False
    assert report_schema["properties"]["order_authority_created_flag"]["const"] is False
    assert report_schema["properties"]["profit_evidence_created_flag"]["const"] is False


def test_replay_and_paper_result_boundaries_are_separate_immutable_and_static_blocked():
    replay = _replay_boundary()
    paper = _paper_boundary()

    assert replay["lane_type"] == "REPLAY"
    assert paper["lane_type"] == "PAPER"
    assert replay["shared_input_identity_id"] == paper["shared_input_identity_id"]
    assert replay["replay_paper_input_identity_digest"] == paper["replay_paper_input_identity_digest"]
    assert replay["replay_result_packet_creation_authority_state"] == (
        "BLOCKED_STATIC_CONTRACT_ONLY"
    )
    assert paper["paper_result_packet_creation_authority_state"] == (
        "BLOCKED_STATIC_CONTRACT_ONLY"
    )
    assert replay["immutable_after_creation_required_flag"] is True
    assert paper["immutable_after_creation_required_flag"] is True
    assert replay["result_merge_allowed_flag"] is False
    assert paper["result_merge_allowed_flag"] is False
    assert validate_result_boundary_record(replay, lane_type="REPLAY") == []
    assert validate_result_boundary_record(paper, lane_type="PAPER") == []


def test_result_boundaries_reject_creation_merge_dual_review_live_order_cash_profit_and_atomicrows_claims():
    replay = _replay_boundary()
    replay["replay_lane_execution_allowed_flag"] = True
    replay["replay_result_packet_creation_allowed_flag"] = True
    replay["replay_result_packet_created_flag"] = True
    replay["result_merge_allowed_flag"] = True
    replay["dual_result_review_allowed_flag"] = True
    replay["owner_live_promotion_review_allowed_flag"] = True
    replay["live_reachability_allowed_flag"] = True
    replay["order_execution_allowed_flag"] = True
    replay["runtime_cash_claim_allowed_flag"] = True
    replay["profit_claim_allowed_flag"] = True
    replay["atomicrows_bundle_mutation_allowed_flag"] = True
    replay["blocker_reduction_claim_allowed_flag"] = True

    failures = validate_result_boundary_record(replay, lane_type="REPLAY")

    for fragment in [
        "replay_lane_execution_allowed_flag",
        "replay_result_packet_creation_allowed_flag",
        "replay_result_packet_created_flag",
        "result_merge_allowed_flag",
        "dual_result_review_allowed_flag",
        "owner_live_promotion_review_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_mutation_allowed_flag",
        "blocker_reduction_claim_allowed_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_result_creation_merge_dual_review_live_cash_atomicrows_and_blocker_reduction_claims():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_REPLAY_RESULT_PACKET_CREATION_CLAIM": "REPLAY_RESULT_PACKET_CREATION",
        "BLOCKED_PAPER_RESULT_PACKET_CREATION_CLAIM": "PAPER_RESULT_PACKET_CREATION",
        "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM": "REPLAY_PAPER_RESULT_MERGE",
        "BLOCKED_DUAL_RESULT_REVIEW_CLAIM": "DUAL_RESULT_REVIEW",
        "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": "LIVE_ORDER_RUNTIME_CASH_PROFIT",
        "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "ATOMICROWS_BUNDLE_HASH_MUTATION",
        "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKER_REDUCTION",
    }

    for fixture_case, claim_type in expected.items():
        record = cases[fixture_case]
        assert record["claim_attempt_type"] == claim_type
        assert record["expected_gate_state"].startswith("BLOCKED_")
        assert record["blocker_codes"]
        assert validate_gate_case_record(record) == []


def test_execution_gate_report_remains_static_and_creates_no_live_or_result_authority():
    report = build_report(fixture=_fixture(), repo_root=Path("."), validation_failures=[])

    assert report["gate_state"] == (
        "STATIC_CONCURRENT_REPLAY_PAPER_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
    )
    assert report["replay_lane_execution_allowed_flag"] is False
    assert report["paper_lane_execution_allowed_flag"] is False
    assert report["replay_result_packet_created_flag"] is False
    assert report["paper_result_packet_created_flag"] is False
    assert report["result_merge_created_flag"] is False
    assert report["dual_result_review_created_flag"] is False
    assert report["owner_live_promotion_review_created_flag"] is False
    assert report["live_reachability_created_flag"] is False
    assert report["order_authority_created_flag"] is False
    assert report["runtime_cash_claim_created_flag"] is False
    assert report["atomicrows_bundle_hash_created_or_mutated_flag"] is False
    assert report["blocker_reduction_claim_created_flag"] is False
    assert report["profit_evidence_created_flag"] is False
