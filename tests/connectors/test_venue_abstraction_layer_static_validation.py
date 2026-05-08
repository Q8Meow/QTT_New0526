import json
from pathlib import Path

from tools.validate_venue_abstraction_layer_static import (
    VENUE_FORBIDDEN_ACTION_FLAGS,
    validate_static_surface,
    validate_venue_abstraction_layer_fixture,
)


SCHEMA_PATH = Path("schemas/connectors/venue_abstraction_layer.schema.json")
FIXTURE_PATH = Path(
    "tests/fixtures/connectors/synthetic_venue_abstraction_layer.v1.fixture.json"
)
EXPECTED_FIXTURE_NAME = "synthetic_venue_abstraction_layer.v1.fixture.json"
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_VENUE_AUTHORITY_NOT_SOURCE_FACT"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _layer(fixture: dict) -> dict:
    return fixture["venue_abstraction_layer"]


def _market_data_surface(fixture: dict) -> dict:
    return _layer(fixture)["market_data_surfaces"][0]


def _order_intent_surface(fixture: dict) -> dict:
    return _layer(fixture)["order_intent_surfaces"][0]


def _private_state_placeholder(fixture: dict) -> dict:
    return _layer(fixture)["private_state_placeholders"][0]


def _connector_capability_reference(fixture: dict) -> dict:
    return _layer(fixture)["connector_capability_references"][0]


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_venue_abstraction_static_validator_accepts_schema_and_fixture():
    failures = validate_static_surface(schema_path=SCHEMA_PATH, fixture_path=FIXTURE_PATH)

    assert failures == []


def test_valid_synthetic_venue_abstraction_layer_fixture_passes():
    fixture = _fixture()
    layer = _layer(fixture)

    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME
    assert fixture["fixture_id"] == "SYNTHETIC_PR24_VENUE_ABSTRACTION_LAYER_FIXTURE"
    assert fixture["fixture_version"] == "PR24_VENUE_ABSTRACTION_LAYER_FIXTURE_V1"
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert layer["layer_state"] == "SCAFFOLD_ONLY_NOT_EXECUTABLE"
    assert _market_data_surface(fixture)["semantic_binding_state"] == "UNBOUND"
    assert _order_intent_surface(fixture)["runtime_state"] == "DISABLED"
    assert _private_state_placeholder(fixture)["private_state_reference"] == "UNBOUND"
    assert _connector_capability_reference(fixture)["connector_capability_reference"] == (
        "UNBOUND"
    )
    assert validate_venue_abstraction_layer_fixture(fixture) == []


def test_venue_abstraction_rejects_missing_required_authority_scope_flags():
    fixture = _fixture()
    _layer(fixture)["venue_authority_scope_flags"].pop(
        "accepted_source_evidence_required_before_semantic_binding"
    )

    failures = validate_venue_abstraction_layer_fixture(fixture)

    _assert_failure_contains(
        failures, "accepted_source_evidence_required_before_semantic_binding"
    )


def test_runtime_live_order_profit_source_binding_and_private_state_flags_true_fail():
    forbidden_flags = {
        "runtime_enabled",
        "runtime_execution_enabled",
        "live_enabled",
        "live_reachability_enabled",
        "live_endpoint_enabled",
        "live_client_enabled",
        "order_execution_enabled",
        "profit_claim_enabled",
        "source_retrieval_enabled",
        "source_acceptance_execution_enabled",
        "external_fact_acceptance_enabled",
        "connector_binding_enabled",
        "private_state_fetch_enabled",
    }

    for flag in sorted(forbidden_flags):
        fixture = _fixture()
        _layer(fixture)["venue_forbidden_action_flags"][flag] = True

        failures = validate_venue_abstraction_layer_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_venue_abstraction_rejects_every_forbidden_action_flag_when_true():
    for flag in sorted(VENUE_FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        _layer(fixture)["venue_forbidden_action_flags"][flag] = True

        failures = validate_venue_abstraction_layer_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_venue_specific_semantic_values_fail_unless_source_required_or_unbound():
    fixture = _fixture()
    market_data = _market_data_surface(fixture)
    market_data["source_required_semantic_fields"]["market_data_snapshot_semantics"] = (
        "SYNTHETIC_POPULATED_MARKET_DATA_SEMANTIC"
    )
    market_data["source_required_semantic_fields"]["tick_semantics"] = (
        "SYNTHETIC_POPULATED_TICK_SEMANTIC"
    )
    market_data["venue_reference"] = "SYNTHETIC_POPULATED_VENUE_REFERENCE"
    market_data["semantic_binding_state"] = "BOUND"

    failures = validate_venue_abstraction_layer_fixture(fixture)

    _assert_failure_contains(failures, "market_data_snapshot_semantics")
    _assert_failure_contains(failures, "tick_semantics")
    _assert_failure_contains(failures, "venue_reference")
    _assert_failure_contains(failures, "semantic_binding_state must be UNBOUND")


def test_live_endpoint_client_private_state_and_order_authority_fields_fail():
    fixture = _fixture()
    market_data = _market_data_surface(fixture)
    order_intent = _order_intent_surface(fixture)
    private_state = _private_state_placeholder(fixture)
    market_data["market_data_endpoint_reference"] = "SYNTHETIC_LIVE_ENDPOINT_CLAIM"
    market_data["market_data_client_reference"] = "SYNTHETIC_CLIENT_CLAIM"
    market_data["live_endpoint_present"] = True
    market_data["live_client_present"] = True
    order_intent["order_client_reference"] = "SYNTHETIC_ORDER_CLIENT_CLAIM"
    order_intent["order_authority_reference"] = "SYNTHETIC_ORDER_AUTHORITY_CLAIM"
    order_intent["order_authority_present"] = True
    private_state["private_state_reference"] = "SYNTHETIC_PRIVATE_STATE_CLAIM"
    private_state["private_state_client_reference"] = "SYNTHETIC_PRIVATE_CLIENT_CLAIM"
    private_state["private_state_present"] = True

    failures = validate_venue_abstraction_layer_fixture(fixture)

    _assert_failure_contains(failures, "market_data_endpoint_reference")
    _assert_failure_contains(failures, "market_data_client_reference")
    _assert_failure_contains(failures, "live_endpoint_present")
    _assert_failure_contains(failures, "live_client_present")
    _assert_failure_contains(failures, "order_client_reference")
    _assert_failure_contains(failures, "order_authority_reference")
    _assert_failure_contains(failures, "order_authority_present")
    _assert_failure_contains(failures, "private_state_reference")
    _assert_failure_contains(failures, "private_state_client_reference")
    _assert_failure_contains(failures, "private_state_present")


def test_runtime_resolver_snapshot_claims_fail():
    fixture = _fixture()
    layer = _layer(fixture)
    action_flags = layer["venue_forbidden_action_flags"]
    action_flags["runtime_resolver_snapshot_creation_enabled"] = True
    action_flags["runtime_resolver_snapshot_materialization_enabled"] = True
    layer["runtime_resolver_snapshot_reference"] = "SYNTHETIC_RUNTIME_SNAPSHOT_CLAIM"
    layer["contains_runtime_resolver_snapshot"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_resolver_snapshot"] = True

    failures = validate_venue_abstraction_layer_fixture(fixture)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_enabled")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_materialization_enabled")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_reference")
    _assert_failure_contains(failures, "contains_runtime_resolver_snapshot")
    _assert_failure_contains(failures, "creates_runtime_resolver_snapshot")


def test_replay_and_paper_execution_claims_fail():
    fixture = _fixture()
    action_flags = _layer(fixture)["venue_forbidden_action_flags"]
    action_flags["replay_execution_enabled"] = True
    action_flags["paper_execution_enabled"] = True
    action_flags["replay_paper_execution_enabled"] = True
    fixture["fixture_no_claim_flags"]["executes_replay"] = True
    fixture["fixture_no_claim_flags"]["executes_paper"] = True
    fixture["fixture_no_claim_flags"]["creates_replay_result"] = True
    fixture["fixture_no_claim_flags"]["creates_paper_result"] = True

    failures = validate_venue_abstraction_layer_fixture(fixture)

    _assert_failure_contains(failures, "replay_execution_enabled")
    _assert_failure_contains(failures, "paper_execution_enabled")
    _assert_failure_contains(failures, "replay_paper_execution_enabled")
    _assert_failure_contains(failures, "executes_replay")
    _assert_failure_contains(failures, "executes_paper")
    _assert_failure_contains(failures, "creates_replay_result")
    _assert_failure_contains(failures, "creates_paper_result")


def test_runtime_cash_receipt_claims_fail():
    fixture = _fixture()
    action_flags = _layer(fixture)["venue_forbidden_action_flags"]
    action_flags["runtime_cash_fetch_enabled"] = True
    action_flags["runtime_cash_receipt_creation_enabled"] = True
    _layer(fixture)["contains_runtime_cash_receipt"] = True
    fixture["fixture_no_claim_flags"]["fetches_runtime_cash"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_cash_receipts"] = True

    failures = validate_venue_abstraction_layer_fixture(fixture)

    _assert_failure_contains(failures, "runtime_cash_fetch_enabled")
    _assert_failure_contains(failures, "runtime_cash_receipt_creation_enabled")
    _assert_failure_contains(failures, "contains_runtime_cash_receipt")
    _assert_failure_contains(failures, "fetches_runtime_cash")
    _assert_failure_contains(failures, "creates_runtime_cash_receipts")


def test_venue_abstraction_fixture_has_no_live_private_or_real_source_material():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    for fragment in {
        "://",
        "www.",
        "http",
        "kalshi",
        "polymarket",
        "ibkr",
        "password",
        "account_id",
        "atomicrows.bundle",
    }:
        assert fragment not in raw_text

    fixture = _fixture()
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())
    assert all(value is False for value in fixture["no_claim_flags"].values())
    assert _layer(fixture)["runtime_resolver_snapshot_reference"] == "UNBOUND"
    assert _market_data_surface(fixture)["market_data_endpoint_reference"] == "UNBOUND"
    assert _order_intent_surface(fixture)["order_authority_reference"] == "UNBOUND"
    assert _private_state_placeholder(fixture)["private_state_reference"] == "UNBOUND"
