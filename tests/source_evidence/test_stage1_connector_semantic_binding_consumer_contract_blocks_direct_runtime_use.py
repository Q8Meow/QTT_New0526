from __future__ import annotations

import copy
import json
from pathlib import Path

from tools.stage1_connector_semantic_binding_ledger_check import (
    validate_consumer_contract_record,
    validate_static_surface,
)


CONSUMER_CONTRACT_SCHEMA = Path(
    "src/qtt/stage1_prediction_markets/connector_semantic_binding/"
    "stage1_connector_semantic_binding_consumer_contract.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/source_evidence/connector_semantic_binding/"
    "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _consumer_by_class() -> dict[str, dict]:
    return {
        record["consumer_class"]: record
        for record in _fixture()["consumer_contract_records"]
    }


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_consumer_contract_schema_blocks_direct_runtime_use():
    schema = json.loads(CONSUMER_CONTRACT_SCHEMA.read_text(encoding="utf-8"))
    props = schema["properties"]

    assert schema["additionalProperties"] is False
    assert props["runtime_resolver_gate_may_consume_connector_semantic_binding_ledger_as_gate_input_only_flag"]["const"] is True
    assert props["runtime_resolver_snapshot_create_may_consume_only_after_runtime_resolver_snapshot_gate_green_flag"]["const"] is True
    assert props["venue_connector_scaffold_static_non_live_configuration_tests_only_flag"]["const"] is True
    assert props["venue_connector_live_client_may_consume_binding_flag"]["const"] is False
    assert props["replay_paper_may_consume_without_runtime_resolver_snapshot_input_lock_flag"]["const"] is False
    assert props["connector_semantic_binding_ledger_is_live_order_authority_flag"]["const"] is False
    assert props["runtime_resolver_snapshot_creation_allowed_flag"]["const"] is False
    assert props["direct_runtime_use_allowed_flag"]["const"] is False
    assert props["live_client_import_allowed_flag"]["const"] is False
    assert props["network_io_allowed_flag"]["const"] is False
    assert props["order_execution_allowed_flag"]["const"] is False
    assert props["live_reachability_allowed_flag"]["const"] is False
    assert props["replay_paper_live_order_profit_claim_allowed_flag"]["const"] is False


def test_runtime_resolver_snapshot_create_cannot_bypass_snapshot_gate_or_consume_accepted_packet_directly():
    assert validate_static_surface(repo_root=Path(".")) == []
    consumers = _consumer_by_class()

    gate_only = consumers["RUNTIME_RESOLVER_GATE_ONLY"]
    assert gate_only["ledger_consumption_authorization_state"] == "AUTHORIZED_GATE_INPUT_ONLY"
    assert gate_only["runtime_resolver_snapshot_creation_allowed_flag"] is False
    assert gate_only["direct_runtime_use_allowed_flag"] is False
    assert validate_consumer_contract_record(gate_only) == []

    direct_snapshot = consumers["RUNTIME_RESOLVER_SNAPSHOT_CREATE_DIRECT"]
    assert direct_snapshot["ledger_consumption_authorization_state"] == "BLOCKED_DIRECT_RUNTIME_USE"
    assert direct_snapshot["runtime_resolver_snapshot_creation_allowed_flag"] is False
    assert direct_snapshot["blocker_codes"] == ["BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_GATE_NOT_GREEN"]
    assert validate_consumer_contract_record(direct_snapshot) == []

    mutated = copy.deepcopy(direct_snapshot)
    mutated["runtime_resolver_snapshot_creation_allowed_flag"] = True
    mutated["direct_runtime_use_allowed_flag"] = True
    failures = validate_consumer_contract_record(mutated)
    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_allowed_flag")
    _assert_failure_contains(failures, "direct_runtime_use_allowed_flag")


def test_live_client_network_io_order_execution_and_live_reachability_are_blocked():
    live_client = copy.deepcopy(_consumer_by_class()["VENUE_CONNECTOR_LIVE_CLIENT"])
    assert live_client["ledger_consumption_authorization_state"] == "BLOCKED_LIVE_CLIENT"
    assert live_client["live_client_import_allowed_flag"] is False
    assert live_client["network_io_allowed_flag"] is False
    assert live_client["order_execution_allowed_flag"] is False
    assert live_client["live_reachability_allowed_flag"] is False
    assert validate_consumer_contract_record(live_client) == []

    live_client["live_client_import_allowed_flag"] = True
    live_client["network_io_allowed_flag"] = True
    live_client["order_execution_allowed_flag"] = True
    live_client["live_reachability_allowed_flag"] = True
    failures = validate_consumer_contract_record(live_client)

    _assert_failure_contains(failures, "live_client_import_allowed_flag")
    _assert_failure_contains(failures, "network_io_allowed_flag")
    _assert_failure_contains(failures, "order_execution_allowed_flag")
    _assert_failure_contains(failures, "live_reachability_allowed_flag")


def test_replay_paper_live_order_profit_and_atomicrows_claims_are_blocked():
    consumers = _consumer_by_class()
    replay_paper = consumers["REPLAY_PAPER_WITHOUT_RUNTIME_RESOLVER_INPUT_LOCK"]
    live_order = consumers["LIVE_ORDER_AUTHORITY_ATTEMPT"]

    assert replay_paper["ledger_consumption_authorization_state"] == (
        "BLOCKED_REPLAY_PAPER_WITHOUT_INPUT_LOCK"
    )
    assert replay_paper["replay_paper_may_consume_without_runtime_resolver_snapshot_input_lock_flag"] is False
    assert replay_paper["runtime_resolver_snapshot_input_lock_required_before_replay_paper_flag"] is True
    assert validate_consumer_contract_record(replay_paper) == []

    assert live_order["ledger_consumption_authorization_state"] == "BLOCKED_LIVE_ORDER_AUTHORITY"
    assert live_order["connector_semantic_binding_ledger_is_live_order_authority_flag"] is False
    assert live_order["replay_paper_live_order_profit_claim_allowed_flag"] is False
    assert validate_consumer_contract_record(live_order) == []

    mutated = copy.deepcopy(live_order)
    mutated["replay_paper_live_order_profit_claim_allowed_flag"] = True
    mutated["no_claim_flags"]["creates_profit_evidence"] = True
    mutated["no_claim_flags"]["creates_atomicrows_bundle_or_hash"] = True
    failures = validate_consumer_contract_record(mutated)
    _assert_failure_contains(failures, "replay_paper_live_order_profit_claim_allowed_flag")
    _assert_failure_contains(failures, "creates_profit_evidence")
    _assert_failure_contains(failures, "creates_atomicrows_bundle_or_hash")
