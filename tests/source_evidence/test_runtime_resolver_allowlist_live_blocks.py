from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_runtime_resolver_to_replay_paper_handoff_check import (
    ALLOWED_IMMEDIATE_CONSUMER,
    ALLOWLIST_TYPE,
    BLOCKED_CONSUMER_CLASSES,
    validate_consumer_allowlist_record,
    validate_static_surface,
)


ALLOWLIST_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/"
    "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/runtime_resolver_snapshot/"
    "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _allowlist() -> dict:
    return copy.deepcopy(_load(FIXTURE)["consumer_allowlist_records"][0])


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_allowlist_schema_allows_only_concurrent_replay_paper_input_lock_gate():
    schema = _load(ALLOWLIST_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["consumer_allowlist_type"]["const"] == ALLOWLIST_TYPE
    assert (
        props["runtime_resolver_snapshot_green_next_allowed_consumer"]["const"]
        == ALLOWED_IMMEDIATE_CONSUMER
    )
    assert props["allowed_immediate_consumer_count"]["const"] == 1
    assert props["concurrent_replay_paper_input_lock_gate_consumer_allowed_flag"]["const"] is True
    assert props["runtime_execution_authority_created_flag"]["const"] is False
    assert props["replay_paper_execution_authority_allowed_flag"]["const"] is False
    assert props["replay_paper_result_packet_creation_allowed_flag"]["const"] is False


def test_only_concurrent_replay_paper_input_lock_gate_is_allowed_immediate_consumer():
    assert validate_static_surface(repo_root=Path(".")) == []
    record = _allowlist()

    assert record["allowed_immediate_consumer_count"] == 1
    assert record["allowed_immediate_consumers"] == [ALLOWED_IMMEDIATE_CONSUMER]
    assert record["runtime_resolver_snapshot_green_next_allowed_consumer"] == ALLOWED_IMMEDIATE_CONSUMER
    assert validate_consumer_allowlist_record(record) == []


def test_allowlist_blocks_direct_live_dual_owner_canary_day1_dashboard_order_cash_profit_and_undeclared_consumers():
    record = _allowlist()
    blocked_by_class = {
        item["consumer_class"]: item
        for item in record["blocked_immediate_consumers"]
    }

    assert BLOCKED_CONSUMER_CLASSES.issubset(blocked_by_class)
    for consumer_class in BLOCKED_CONSUMER_CLASSES:
        blocked = blocked_by_class[consumer_class]
        assert blocked["consumer_allowed_flag"] is False
        assert blocked["authorization_state"] == "BLOCKED_FORBIDDEN_CONSUMER"
        assert blocked["blocker_code"]

    assert record["direct_live_consumer_allowed_flag"] is False
    assert record["direct_dual_result_review_consumer_allowed_flag"] is False
    assert record["direct_owner_review_consumer_allowed_flag"] is False
    assert record["direct_canary_eligibility_consumer_allowed_flag"] is False
    assert record["direct_live_gate_day1_consumer_allowed_flag"] is False
    assert record["direct_dashboard_mutation_consumer_allowed_flag"] is False
    assert record["direct_order_router_consumer_allowed_flag"] is False
    assert record["runtime_cash_profit_consumer_allowed_flag"] is False
    assert record["undeclared_consumer_allowed_flag"] is False


def test_allowlist_rejects_added_direct_live_or_dashboard_consumer_fail_closed():
    record = _allowlist()
    record["allowed_immediate_consumers"].append("DIRECT_LIVE_CONSUMER")
    record["allowed_immediate_consumer_count"] = 2
    record["direct_live_consumer_allowed_flag"] = True
    record["direct_dashboard_mutation_consumer_allowed_flag"] = True

    failures = validate_consumer_allowlist_record(record)

    _assert_failure_contains(failures, "allowed_immediate_consumer_count")
    _assert_failure_contains(failures, "allowed_immediate_consumers")
    _assert_failure_contains(failures, "direct_live_consumer_allowed_flag")
    _assert_failure_contains(failures, "direct_dashboard_mutation_consumer_allowed_flag")


def test_allowlist_rejects_runtime_execution_authority_and_result_packet_claims():
    record = _allowlist()
    record["runtime_execution_authority_created_flag"] = True
    record["replay_paper_execution_authority_allowed_flag"] = True
    record["replay_paper_result_packet_creation_allowed_flag"] = True
    record["dual_result_review_creation_allowed_flag"] = True
    record["order_execution_allowed_flag"] = True
    record["runtime_cash_claim_allowed_flag"] = True
    record["profit_claim_allowed_flag"] = True
    record["no_claim_flags"]["executes_replay_or_paper"] = True
    record["no_claim_flags"]["creates_replay_paper_result_packets"] = True

    failures = validate_consumer_allowlist_record(record)

    for fragment in [
        "runtime_execution_authority_created_flag",
        "replay_paper_execution_authority_allowed_flag",
        "replay_paper_result_packet_creation_allowed_flag",
        "dual_result_review_creation_allowed_flag",
        "order_execution_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "executes_replay_or_paper",
        "creates_replay_paper_result_packets",
    ]:
        _assert_failure_contains(failures, fragment)
