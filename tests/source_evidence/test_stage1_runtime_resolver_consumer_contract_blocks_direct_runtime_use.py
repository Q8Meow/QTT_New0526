from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_runtime_resolver_snapshot_contract_check import (
    CONSUMER_CONTRACT_TYPE,
    validate_consumer_contract_record,
    validate_static_surface,
)


CONSUMER_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/runtime_resolver/"
    "stage1_runtime_resolver_consumer_contract.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/runtime_resolver/"
    "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return _load(FIXTURE)


def _consumer_by_class() -> dict[str, dict]:
    return {record["consumer_class"]: record for record in _fixture()["consumer_contract_records"]}


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_consumer_contract_schema_blocks_direct_runtime_use_and_all_live_authority():
    schema = _load(CONSUMER_SCHEMA)
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["runtime_resolver_consumer_contract_type"]["const"] == CONSUMER_CONTRACT_TYPE
    assert props["runtime_resolver_schema_gate_may_validate_synthetic_fixture_records_only_flag"]["const"] is True
    assert props["runtime_resolver_snapshot_creation_allowed_flag"]["const"] is False
    assert props["replay_paper_may_consume_runtime_resolver_data_from_pr41_flag"]["const"] is False
    assert props["live_canary_live_arbitrage_may_consume_runtime_resolver_data_from_pr41_flag"]["const"] is False
    assert props["order_router_may_consume_runtime_resolver_data_from_pr41_flag"]["const"] is False
    assert props["dashboard_may_display_blocked_static_gate_reports_only_flag"]["const"] is True
    assert props["dashboard_live_readiness_claim_allowed_flag"]["const"] is False
    assert props["direct_runtime_use_allowed_flag"]["const"] is False
    assert props["live_client_import_allowed_flag"]["const"] is False
    assert props["network_io_allowed_flag"]["const"] is False
    assert props["order_execution_allowed_flag"]["const"] is False
    assert props["live_reachability_allowed_flag"]["const"] is False
    assert props["runtime_cash_claim_allowed_flag"]["const"] is False
    assert props["profit_claim_allowed_flag"]["const"] is False


def test_static_schema_gate_and_dashboard_are_limited_to_synthetic_or_blocked_report_display():
    assert validate_static_surface(repo_root=Path(".")) == []
    consumers = _consumer_by_class()

    schema_gate = consumers["STATIC_SCHEMA_GATE_SYNTHETIC_FIXTURE_VALIDATION_ONLY"]
    dashboard = consumers["DASHBOARD_BLOCKED_STATIC_GATE_REPORT_DISPLAY_ONLY"]

    assert schema_gate["consumer_authorization_state"] == (
        "AUTHORIZED_SYNTHETIC_STATIC_VALIDATION_ONLY"
    )
    assert dashboard["consumer_authorization_state"] == (
        "AUTHORIZED_BLOCKED_STATIC_REPORT_DISPLAY_ONLY"
    )
    assert dashboard["dashboard_live_readiness_claim_allowed_flag"] is False
    assert validate_consumer_contract_record(schema_gate) == []
    assert validate_consumer_contract_record(dashboard) == []


def test_snapshot_creation_replay_paper_live_order_cash_profit_and_atomicrows_consumers_are_blocked():
    consumers = _consumer_by_class()
    expected = {
        "RUNTIME_RESOLVER_SNAPSHOT_CREATION_ATTEMPT": "BLOCKED_STATIC_CONTRACT_ONLY",
        "REPLAY_PAPER_DIRECT_CONSUMER_ATTEMPT": "BLOCKED_REPLAY_PAPER_DIRECT_CONSUMPTION",
        "LIVE_CANARY_LIVE_ARBITRAGE_CONSUMER_ATTEMPT": "BLOCKED_LIVE_CONSUMPTION",
        "ORDER_ROUTER_CONSUMER_ATTEMPT": "BLOCKED_ORDER_AUTHORITY",
        "RUNTIME_CASH_PROFIT_CLAIM_ATTEMPT": "BLOCKED_RUNTIME_CASH_OR_PROFIT_CLAIM",
        "ATOMICROWS_BUNDLE_HASH_MUTATION_CLAIM_ATTEMPT": "BLOCKED_ATOMICROWS_MUTATION",
    }

    for consumer_class, state in expected.items():
        record = consumers[consumer_class]
        assert record["consumer_authorization_state"] == state
        assert record["blocker_codes"]
        assert record["runtime_resolver_snapshot_creation_allowed_flag"] is False
        assert record["replay_paper_may_consume_runtime_resolver_data_from_pr41_flag"] is False
        assert record["live_canary_live_arbitrage_may_consume_runtime_resolver_data_from_pr41_flag"] is False
        assert record["order_router_may_consume_runtime_resolver_data_from_pr41_flag"] is False
        assert record["runtime_cash_claim_allowed_flag"] is False
        assert record["profit_claim_allowed_flag"] is False
        assert validate_consumer_contract_record(record) == []


def test_direct_runtime_use_claims_fail_closed():
    record = copy.deepcopy(_consumer_by_class()["RUNTIME_CASH_PROFIT_CLAIM_ATTEMPT"])
    record["runtime_resolver_snapshot_creation_allowed_flag"] = True
    record["replay_paper_may_consume_runtime_resolver_data_from_pr41_flag"] = True
    record["live_canary_live_arbitrage_may_consume_runtime_resolver_data_from_pr41_flag"] = True
    record["order_router_may_consume_runtime_resolver_data_from_pr41_flag"] = True
    record["dashboard_live_readiness_claim_allowed_flag"] = True
    record["direct_runtime_use_allowed_flag"] = True
    record["runtime_cash_claim_allowed_flag"] = True
    record["profit_claim_allowed_flag"] = True
    record["no_claim_flags"]["creates_profit_evidence"] = True
    record["no_claim_flags"]["creates_atomicrows_bundle_or_hash"] = True
    record["no_claim_flags"]["reduces_blockers"] = True

    failures = validate_consumer_contract_record(record)

    for fragment in [
        "runtime_resolver_snapshot_creation_allowed_flag",
        "replay_paper_may_consume_runtime_resolver_data_from_pr41_flag",
        "live_canary_live_arbitrage_may_consume_runtime_resolver_data_from_pr41_flag",
        "order_router_may_consume_runtime_resolver_data_from_pr41_flag",
        "dashboard_live_readiness_claim_allowed_flag",
        "direct_runtime_use_allowed_flag",
        "runtime_cash_claim_allowed_flag",
        "profit_claim_allowed_flag",
        "creates_profit_evidence",
        "creates_atomicrows_bundle_or_hash",
        "reduces_blockers",
    ]:
        _assert_failure_contains(failures, fragment)
