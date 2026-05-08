import copy
import json
from pathlib import Path

import pytest

from tools.validate_order_intent_execution_router_static import (
    FORBIDDEN_ACTION_FLAGS,
    validate_order_intent_execution_router_fixture,
    validate_static_surface,
)

SCHEMA_PATH = Path("schemas/connectors/order_intent_execution_router_scaffolding.schema.json")
FIXTURE_PATH = Path(
    "tests/fixtures/connectors/"
    "synthetic_order_intent_execution_router_scaffolding.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _intent(fixture: dict) -> dict:
    return fixture["order_intent_placeholders"][0]


def _gate(fixture: dict) -> dict:
    return fixture["execution_router_gate_placeholders"][0]


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_order_intent_execution_router_static_validator_accepts_schema_and_fixture():
    assert validate_static_surface(schema_path=SCHEMA_PATH, fixture_path=FIXTURE_PATH) == []


def test_valid_synthetic_fixture_is_static_disabled_and_unbound():
    fixture = _fixture()

    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"
    assert fixture["deterministic_output"] is True
    assert fixture["runtime_resolver_snapshot_reference"] == "UNBOUND"
    assert _intent(fixture)["intent_state"] == "PLACEHOLDER_ONLY_NOT_RUNTIME_INTENT"
    assert _intent(fixture)["runtime_state"] == "DISABLED"
    assert _gate(fixture)["router_state"] == "GATE_PLACEHOLDER_ONLY_NOT_EXECUTABLE"
    assert _gate(fixture)["final_order_submission_authority_present"] is False
    assert validate_order_intent_execution_router_fixture(fixture) == []


def test_missing_required_authority_scope_flag_fails():
    fixture = _fixture()
    fixture["scope_flags"].pop("final_order_submission_authority_disabled")

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "final_order_submission_authority_disabled")


@pytest.mark.parametrize(
    "flag",
    [
        "runtime_enabled",
        "runtime_execution_enabled",
        "live_enabled",
        "order_execution_enabled",
        "profit_claim_enabled",
        "source_retrieval_enabled",
        "source_acceptance_execution_enabled",
        "external_fact_acceptance_enabled",
        "connector_binding_enabled",
        "connector_semantic_binding_enabled",
        "private_state_fetch_enabled",
    ],
)
def test_runtime_live_order_profit_source_binding_and_private_state_flags_true_fail(flag):
    fixture = _fixture()
    fixture["forbidden_action_flags"][flag] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, flag)


def test_every_forbidden_action_flag_fails_when_true():
    for flag in sorted(FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        fixture["forbidden_action_flags"][flag] = True

        failures = validate_order_intent_execution_router_fixture(fixture)

        _assert_failure_contains(failures, flag)


@pytest.mark.parametrize(
    "field",
    [
        "submits_orders",
        "cancels_orders",
        "reduces_orders",
        "closes_orders",
        "replaces_orders",
        "amends_orders",
        "creates_final_order_release_authority",
    ],
)
def test_real_order_submission_cancel_reduce_close_replace_amend_authority_claims_fail(
    field,
):
    fixture = _fixture()
    fixture["fixture_no_claim_flags"][field] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, field)


def test_live_signer_path_claims_fail():
    fixture = _fixture()
    gate = _gate(fixture)
    gate["live_signer_path_reference"] = "SYNTHETIC_SIGNER_PATH_CLAIM"
    gate["live_signer_path_present"] = True
    fixture["forbidden_action_flags"]["live_signer_path_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_live_signer_path"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "live_signer_path_reference")
    _assert_failure_contains(failures, "live_signer_path_present")
    _assert_failure_contains(failures, "live_signer_path_enabled")
    _assert_failure_contains(failures, "creates_live_signer_path")


def test_venue_write_connectivity_claims_fail():
    fixture = _fixture()
    gate = _gate(fixture)
    gate["venue_write_connectivity_reference"] = "SYNTHETIC_WRITE_CONNECTIVITY_CLAIM"
    gate["venue_write_connectivity_present"] = True
    fixture["forbidden_action_flags"]["venue_write_connectivity_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_venue_write_connectivity"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "venue_write_connectivity_reference")
    _assert_failure_contains(failures, "venue_write_connectivity_present")
    _assert_failure_contains(failures, "venue_write_connectivity_enabled")
    _assert_failure_contains(failures, "creates_venue_write_connectivity")


def test_venue_specific_order_semantic_values_fail_unless_source_required_or_unbound():
    fixture = _fixture()
    intent = _intent(fixture)
    intent["source_required_order_intent_fields"]["order_type_semantics"] = "LIMIT"
    intent["source_required_order_intent_fields"]["order_side_semantics"] = "BUY"
    intent["venue_reference"] = "SYNTHETIC_POPULATED_VENUE_REFERENCE"
    intent["semantic_binding_state"] = "BOUND"

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "order_type_semantics")
    _assert_failure_contains(failures, "order_side_semantics")
    _assert_failure_contains(failures, "venue_reference")
    _assert_failure_contains(failures, "semantic_binding_state must be UNBOUND")


def test_runtime_resolver_snapshot_claims_fail():
    fixture = _fixture()
    fixture["runtime_resolver_snapshot_reference"] = "SYNTHETIC_RUNTIME_SNAPSHOT_CLAIM"
    fixture["contains_runtime_resolver_snapshot"] = True
    fixture["forbidden_action_flags"]["runtime_resolver_snapshot_creation_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_resolver_snapshot"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_reference")
    _assert_failure_contains(failures, "contains_runtime_resolver_snapshot")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_enabled")
    _assert_failure_contains(failures, "creates_runtime_resolver_snapshot")


def test_replay_and_paper_execution_claims_fail():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["replay_execution_enabled"] = True
    fixture["forbidden_action_flags"]["paper_execution_enabled"] = True
    fixture["forbidden_action_flags"]["replay_result_packet_creation_enabled"] = True
    fixture["forbidden_action_flags"]["paper_result_packet_creation_enabled"] = True
    fixture["fixture_no_claim_flags"]["executes_replay"] = True
    fixture["fixture_no_claim_flags"]["executes_paper"] = True
    fixture["fixture_no_claim_flags"]["creates_replay_result"] = True
    fixture["fixture_no_claim_flags"]["creates_paper_result"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "replay_execution_enabled")
    _assert_failure_contains(failures, "paper_execution_enabled")
    _assert_failure_contains(failures, "replay_result_packet_creation_enabled")
    _assert_failure_contains(failures, "paper_result_packet_creation_enabled")
    _assert_failure_contains(failures, "executes_replay")
    _assert_failure_contains(failures, "executes_paper")
    _assert_failure_contains(failures, "creates_replay_result")
    _assert_failure_contains(failures, "creates_paper_result")


def test_runtime_cash_receipt_claims_fail():
    fixture = _fixture()
    fixture["contains_runtime_cash_receipt"] = True
    fixture["forbidden_action_flags"]["runtime_cash_receipt_creation_enabled"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_cash_receipts"] = True

    failures = validate_order_intent_execution_router_fixture(fixture)

    _assert_failure_contains(failures, "contains_runtime_cash_receipt")
    _assert_failure_contains(failures, "runtime_cash_receipt_creation_enabled")
    _assert_failure_contains(failures, "creates_runtime_cash_receipts")


def test_fixture_has_no_live_private_real_source_or_profit_material():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()
    for fragment in {
        "://",
        "www.",
        "password",
        "account_id",
        "atomicrows.bundle",
        "owner_uploaded_private_doc_locator",
    }:
        assert fragment not in raw_text

    fixture = _fixture()
    frozen = copy.deepcopy(fixture)
    assert all(value is False for value in fixture["forbidden_action_flags"].values())
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())
    assert _intent(fixture)["order_payload_reference"] == "UNBOUND"
    assert _gate(fixture)["final_order_release_reference"] == "UNBOUND"
    assert _gate(fixture)["venue_write_connectivity_reference"] == "UNBOUND"
    assert _gate(fixture)["live_signer_path_reference"] == "UNBOUND"
    assert frozen == fixture
