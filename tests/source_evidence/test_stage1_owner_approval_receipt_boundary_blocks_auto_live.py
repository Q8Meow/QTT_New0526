from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_owner_live_promotion_review_contract_check import (
    OWNER_APPROVAL_RECEIPT_BOUNDARY_TYPE,
    THREE_VENUE_CANARY_GATE_ONLY_CONSUMER,
    build_report,
    validate_owner_approval_receipt_boundary_record,
)


BOUNDARY_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/owner_live_promotion_review/"
    "stage1_owner_approval_receipt_boundary.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/owner_live_promotion_review/"
    "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _boundary() -> dict:
    return copy.deepcopy(_fixture()["owner_approval_receipt_boundary_records"][0])


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_owner_approval_receipt_boundary_schema_blocks_receipt_creation_and_live_authority():
    schema = _load(BOUNDARY_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["owner_approval_receipt_boundary_type"]["const"] == (
        OWNER_APPROVAL_RECEIPT_BOUNDARY_TYPE
    )
    assert props["owner_approval_receipt_creation_authority_state"]["const"] == (
        "BLOCKED_STATIC_CONTRACT_ONLY"
    )
    assert props["owner_approval_receipt_created_flag"]["const"] is False
    assert props["live_eligibility_allowed_flag"]["const"] is False
    assert props["three_venue_canary_eligibility_allowed_flag"]["const"] is False
    assert props["live_reachability_allowed_flag"]["const"] is False
    assert props["order_execution_allowed_flag"]["const"] is False
    assert props["runtime_cash_claim_allowed_flag"]["const"] is False
    assert props["profit_claim_allowed_flag"]["const"] is False


def test_owner_approval_receipt_boundary_is_blocked_static_only_with_required_receipts():
    record = _boundary()

    assert record["owner_approval_receipt_creation_authority_state"] == (
        "BLOCKED_STATIC_CONTRACT_ONLY"
    )
    assert record["owner_approval_receipt_created_flag"] is False
    assert record["owner_approval_decision_created_flag"] is False
    assert record["live_eligibility_allowed_flag"] is False
    assert record["three_venue_canary_eligibility_allowed_flag"] is False
    assert record["blocker_codes"]
    assert record["receipt_ids"]
    assert validate_owner_approval_receipt_boundary_record(record) == []


def test_owner_approval_receipt_boundary_rejects_auto_live_canary_order_cash_profit_atomicrows_and_blocker_claims():
    record = _boundary()
    record["owner_approval_receipt_created_flag"] = True
    record["owner_approval_decision_created_flag"] = True
    record["live_eligibility_allowed_flag"] = True
    record["three_venue_canary_eligibility_allowed_flag"] = True
    record["live_reachability_allowed_flag"] = True
    record["order_execution_allowed_flag"] = True
    record["runtime_cash_claim_allowed_flag"] = True
    record["profit_claim_allowed_flag"] = True
    record["atomicrows_bundle_hash_created_or_mutated_flag"] = True
    record["blocker_reduction_claim_allowed_flag"] = True
    record["owner_live_promotion_review_auto_approval_allowed"] = True
    record["owner_live_promotion_review_auto_promotion_allowed"] = True

    failures = validate_owner_approval_receipt_boundary_record(record)

    for fragment in [
        "owner_approval_receipt_created_flag",
        "owner_approval_decision_created_flag",
        "live_eligibility_allowed_flag",
        "three_venue_canary_eligibility_allowed_flag",
        "live_reachability_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "atomicrows_bundle_hash_created_or_mutated_flag",
        "blocker_reduction_claim_allowed_flag",
        "owner_live_promotion_review_auto_approval_allowed",
        "owner_live_promotion_review_auto_promotion_allowed",
    ]:
        _assert_failure_contains(failures, fragment)


def test_gate_report_keeps_owner_approval_receipt_boundary_before_any_live_or_canary_eligibility():
    report = build_report(fixture=_fixture(), repo_root=Path("."), validation_failures=[])

    assert report["owner_live_promotion_review_pass_next_allowed_consumer"] == (
        THREE_VENUE_CANARY_GATE_ONLY_CONSUMER
    )
    assert report["owner_live_promotion_review_auto_approval_allowed"] is False
    assert report["owner_live_promotion_review_auto_promotion_allowed"] is False
    assert report["owner_live_promotion_review_decision_created_flag"] is False
    assert report["owner_approval_receipt_created_flag"] is False
    assert report["live_eligibility_allowed_flag"] is False
    assert report["three_venue_canary_eligibility_allowed_flag"] is False
    assert report["live_reachability_allowed_flag"] is False
    assert report["order_execution_allowed_flag"] is False
    assert report["runtime_cash_claim_allowed_flag"] is False
    assert report["profit_claim_allowed_flag"] is False
