from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_owner_live_promotion_review_contract_check import (
    HANDOFF_BLOCK_TYPE,
    OWNER_REVIEW_ONLY_CONSUMER,
    THREE_VENUE_CANARY_GATE_ONLY_CONSUMER,
    build_report,
    validate_gate_case_record,
    validate_handoff_block_record,
    validate_input_contract_record,
)


HANDOFF_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
    "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/owner_live_promotion_review/"
    "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _input_contract() -> dict:
    return copy.deepcopy(_fixture()["owner_live_promotion_review_input_contract_records"][0])


def _handoff_block() -> dict:
    return copy.deepcopy(_fixture()["three_venue_canary_eligibility_handoff_block_records"][0])


def _case_by_fixture_case() -> dict[str, dict]:
    return {
        record["fixture_case"]: record
        for record in _fixture()["owner_live_promotion_review_gate_case_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_handoff_block_schema_allows_only_later_three_venue_canary_gate_without_execution():
    schema = _load(HANDOFF_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["three_venue_canary_eligibility_handoff_block_type"]["const"] == (
        HANDOFF_BLOCK_TYPE
    )
    assert props["dual_result_review_pass_next_allowed_consumer"]["const"] == (
        OWNER_REVIEW_ONLY_CONSUMER
    )
    assert props["owner_live_promotion_review_pass_next_allowed_consumer"]["const"] == (
        THREE_VENUE_CANARY_GATE_ONLY_CONSUMER
    )
    assert props["owner_live_promotion_review_direct_live_consumer_allowed"]["const"] is False
    assert props["owner_live_promotion_review_direct_order_router_allowed"]["const"] is False
    assert props["owner_live_promotion_review_direct_canary_eligibility_allowed"]["const"] is False
    assert props["owner_live_promotion_review_direct_canary_execution_allowed"]["const"] is False
    assert props["owner_live_promotion_review_auto_promotion_allowed"]["const"] is False
    assert props["three_venue_canary_eligibility_gate_created_flag"]["const"] is False
    assert props["limited_live_canary_execution_created_flag"]["const"] is False


def test_handoff_block_routes_only_to_later_gate_without_creating_canary_live_order_cash_or_profit():
    record = _handoff_block()

    assert record["dual_result_review_pass_next_allowed_consumer"] == OWNER_REVIEW_ONLY_CONSUMER
    assert record["owner_live_promotion_review_pass_next_allowed_consumer"] == (
        THREE_VENUE_CANARY_GATE_ONLY_CONSUMER
    )
    assert record["live_eligibility_requires_later_three_venue_canary_eligibility_gate"] is True
    assert record["owner_live_promotion_review_direct_canary_eligibility_allowed"] is False
    assert record["owner_live_promotion_review_direct_canary_execution_allowed"] is False
    assert record["three_venue_canary_eligibility_gate_created_flag"] is False
    assert record["three_venue_canary_eligibility_created_flag"] is False
    assert record["limited_live_canary_execution_created_flag"] is False
    assert record["order_execution_allowed_flag"] is False
    assert record["runtime_cash_claim_allowed_flag"] is False
    assert record["profit_claim_allowed_flag"] is False
    assert validate_handoff_block_record(record) == []


def test_handoff_block_rejects_direct_live_canary_execution_order_cash_profit_atomicrows_and_blocker_claims():
    record = _handoff_block()
    record["owner_live_promotion_review_direct_live_consumer_allowed"] = True
    record["owner_live_promotion_review_direct_order_router_allowed"] = True
    record["owner_live_promotion_review_direct_canary_eligibility_allowed"] = True
    record["owner_live_promotion_review_direct_canary_execution_allowed"] = True
    record["owner_live_promotion_review_auto_approval_allowed"] = True
    record["owner_live_promotion_review_auto_promotion_allowed"] = True
    record["owner_approval_receipt_created_flag"] = True
    record["live_eligibility_allowed_flag"] = True
    record["three_venue_canary_eligibility_allowed_flag"] = True
    record["three_venue_canary_eligibility_gate_created_flag"] = True
    record["three_venue_canary_eligibility_created_flag"] = True
    record["limited_live_canary_execution_created_flag"] = True
    record["live_reachability_allowed_flag"] = True
    record["order_execution_allowed_flag"] = True
    record["runtime_cash_claim_allowed_flag"] = True
    record["profit_claim_allowed_flag"] = True
    record["atomicrows_bundle_hash_created_or_mutated_flag"] = True
    record["blocker_reduction_claim_created_flag"] = True

    failures = validate_handoff_block_record(record)

    for fragment in [
        "owner_live_promotion_review_direct_live_consumer_allowed",
        "owner_live_promotion_review_direct_order_router_allowed",
        "owner_live_promotion_review_direct_canary_eligibility_allowed",
        "owner_live_promotion_review_direct_canary_execution_allowed",
        "owner_live_promotion_review_auto_approval_allowed",
        "owner_live_promotion_review_auto_promotion_allowed",
        "owner_approval_receipt_created_flag",
        "live_eligibility_allowed_flag",
        "three_venue_canary_eligibility_allowed_flag",
        "three_venue_canary_eligibility_gate_created_flag",
        "three_venue_canary_eligibility_created_flag",
        "limited_live_canary_execution_created_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_hash_created_or_mutated_flag",
        "blocker_reduction_claim_created_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_input_contract_rejects_owner_approval_auto_live_canary_order_cash_atomicrows_blocker_and_profit_claims():
    record = _input_contract()
    record["dual_result_review_decision_created_flag"] = True
    record["owner_live_promotion_review_decision_created_flag"] = True
    record["owner_approval_receipt_created_flag"] = True
    record["owner_approval_receipt_creation_claimed_flag"] = True
    record["auto_live_promotion_claimed_flag"] = True
    record["direct_canary_eligibility_claimed_flag"] = True
    record["direct_canary_execution_claimed_flag"] = True
    record["live_eligibility_allowed_flag"] = True
    record["three_venue_canary_eligibility_allowed_flag"] = True
    record["three_venue_canary_eligibility_created_flag"] = True
    record["limited_live_canary_execution_created_flag"] = True
    record["live_reachability_allowed_flag"] = True
    record["order_execution_allowed_flag"] = True
    record["runtime_cash_claim_allowed_flag"] = True
    record["atomicrows_bundle_hash_created_or_mutated_flag"] = True
    record["blocker_reduction_claim_created_flag"] = True
    record["profit_claim_allowed_flag"] = True

    failures = validate_input_contract_record(record)

    for fragment in [
        "dual_result_review_decision_created_flag",
        "owner_live_promotion_review_decision_created_flag",
        "owner_approval_receipt_created_flag",
        "owner_approval_receipt_creation_claimed_flag",
        "auto_live_promotion_claimed_flag",
        "direct_canary_eligibility_claimed_flag",
        "direct_canary_execution_claimed_flag",
        "live_eligibility_allowed_flag",
        "three_venue_canary_eligibility_allowed_flag",
        "three_venue_canary_eligibility_created_flag",
        "limited_live_canary_execution_created_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "atomicrows_bundle_hash_created_or_mutated_flag",
        "blocker_reduction_claim_created_flag",
        "profit_claim_allowed_flag",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_cases_block_result_merge_owner_approval_auto_live_canary_order_cash_profit_atomicrows_and_blocker_reduction():
    cases = _case_by_fixture_case()
    expected = {
        "BLOCKED_REPLAY_PAPER_RESULT_MERGE_CLAIM": "RESULT_MERGE",
        "BLOCKED_DUAL_RESULT_REVIEW_DECISION_CLAIM": "DUAL_RESULT_REVIEW_DECISION",
        "BLOCKED_OWNER_APPROVAL_RECEIPT_CREATION_CLAIM": "OWNER_APPROVAL_RECEIPT",
        "BLOCKED_AUTO_LIVE_PROMOTION_CLAIM": "AUTO_LIVE_PROMOTION",
        "BLOCKED_DIRECT_CANARY_ELIGIBILITY_CLAIM": "DIRECT_CANARY_ELIGIBILITY",
        "BLOCKED_DIRECT_CANARY_EXECUTION_CLAIM": "DIRECT_CANARY_EXECUTION",
        "BLOCKED_LIVE_ORDER_RUNTIME_CASH_PROFIT_CLAIM": "LIVE_ORDER_RUNTIME_CASH_PROFIT",
        "BLOCKED_ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM": "ATOMICROWS_BUNDLE_HASH_MUTATION",
        "BLOCKED_BLOCKER_REDUCTION_CLAIM": "BLOCKER_REDUCTION",
    }

    for fixture_case, claim_type in expected.items():
        record = cases[fixture_case]
        assert record["claim_attempt_type"] == claim_type
        assert record["expected_gate_state"].startswith("BLOCKED_OWNER_REVIEW")
        assert validate_gate_case_record(record) == []


def test_gate_report_blocks_auto_promotion_direct_canary_execution_live_order_cash_atomicrows_and_profit():
    report = build_report(fixture=_fixture(), repo_root=Path("."), validation_failures=[])

    assert report["gate_state"] == (
        "STATIC_OWNER_LIVE_PROMOTION_REVIEW_CONTRACT_VALIDATED_NO_RUNTIME_AUTHORITY"
    )
    assert report["dual_result_review_pass_next_allowed_consumer"] == OWNER_REVIEW_ONLY_CONSUMER
    assert report["owner_live_promotion_review_pass_next_allowed_consumer"] == (
        THREE_VENUE_CANARY_GATE_ONLY_CONSUMER
    )
    assert report["owner_live_promotion_review_direct_live_consumer_allowed"] is False
    assert report["owner_live_promotion_review_direct_order_router_allowed"] is False
    assert report["owner_live_promotion_review_direct_canary_execution_allowed"] is False
    assert report["owner_live_promotion_review_auto_approval_allowed"] is False
    assert report["owner_live_promotion_review_auto_promotion_allowed"] is False
    assert report["owner_approval_receipt_created_flag"] is False
    assert report["three_venue_canary_eligibility_created_flag"] is False
    assert report["limited_live_canary_execution_created_flag"] is False
    assert report["order_execution_allowed_flag"] is False
    assert report["runtime_cash_claim_allowed_flag"] is False
    assert report["atomicrows_bundle_hash_created_or_mutated_flag"] is False
    assert report["blocker_reduction_claim_created_flag"] is False
    assert report["profit_claim_allowed_flag"] is False
