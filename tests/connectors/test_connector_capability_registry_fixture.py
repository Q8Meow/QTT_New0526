import copy
import json
from pathlib import Path

from tools.validate_connector_capability_static import (
    CONNECTOR_FORBIDDEN_ACTION_FLAGS,
    SOURCE_REQUIRED_FIELD_KEYS,
    validate_connector_capability_registry_fixture,
    validate_static_surface,
)


SCHEMA_PATH = Path("schemas/connectors/connector_capability_registry.schema.json")
FIXTURE_PATH = Path(
    "tests/fixtures/connectors/synthetic_connector_capability_registry.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _registry(fixture: dict) -> dict:
    return fixture["connector_capability_registry"]


def _readiness_record(fixture: dict) -> dict:
    return _registry(fixture)["readiness_records"][0]


def test_connector_capability_static_validator_accepts_schema_and_fixture():
    failures = validate_static_surface(schema_path=SCHEMA_PATH, fixture_path=FIXTURE_PATH)

    assert failures == []


def test_valid_synthetic_connector_capability_registry_fixture_passes_validation():
    assert validate_connector_capability_registry_fixture(_fixture()) == []


def test_connector_capability_registry_rejects_missing_required_authority_scope_flags():
    fixture = _fixture()
    _registry(fixture)["connector_authority_scope_flags"].pop(
        "accepted_source_evidence_required_before_semantic_binding"
    )

    failures = validate_connector_capability_registry_fixture(fixture)

    assert any(
        "accepted_source_evidence_required_before_semantic_binding" in failure
        for failure in failures
    )


def test_connector_capability_registry_rejects_runtime_live_order_profit_source_and_binding_flags():
    for flag in sorted(
        {
            "runtime_enabled",
            "live_enabled",
            "order_execution_enabled",
            "profit_claim_enabled",
            "source_retrieval_enabled",
            "source_acceptance_execution_enabled",
            "connector_binding_enabled",
        }
    ):
        fixture = _fixture()
        _registry(fixture)["connector_forbidden_action_flags"][flag] = True

        failures = validate_connector_capability_registry_fixture(fixture)

        assert any(flag in failure for failure in failures)


def test_connector_capability_registry_rejects_every_forbidden_action_flag_when_true():
    for flag in sorted(CONNECTOR_FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        _registry(fixture)["connector_forbidden_action_flags"][flag] = True

        failures = validate_connector_capability_registry_fixture(fixture)

        assert any(flag in failure for failure in failures)


def test_connector_semantic_binding_claim_without_accepted_source_evidence_fails():
    fixture = _fixture()
    record = _readiness_record(fixture)
    record["connector_semantic_binding_claim_present"] = True
    record["accepted_source_evidence_present"] = False

    failures = validate_connector_capability_registry_fixture(fixture)

    assert any(
        "requires accepted source evidence before binding" in failure
        for failure in failures
    )


def test_connector_semantic_value_claim_without_accepted_source_evidence_fails():
    fixture = _fixture()
    record = _readiness_record(fixture)
    record["semantic_value"] = "SYNTHETIC_NON_SOURCE_REQUIRED_SEMANTIC_VALUE"

    failures = validate_connector_capability_registry_fixture(fixture)

    assert any("semantic_value must be SOURCE_REQUIRED" in failure for failure in failures)


def test_connector_source_required_fields_remain_source_required():
    fixture = _fixture()
    card_fields = _registry(fixture)["capability_cards"][0]["source_required_fields"]
    record_fields = _readiness_record(fixture)["source_required_fields"]

    for field in sorted(SOURCE_REQUIRED_FIELD_KEYS - {"semantic_value"}):
        assert card_fields[field] == "SOURCE_REQUIRED"
        assert record_fields[field] == "SOURCE_REQUIRED"


def test_real_connector_live_endpoint_private_state_or_order_authority_fields_fail():
    fixture = _fixture()
    record = copy.deepcopy(_readiness_record(fixture))
    record["source_required_fields"]["live_endpoint"] = (
        "SYNTHETIC_NON_SOURCE_REQUIRED_LIVE_ENDPOINT_CLAIM"
    )
    record["source_required_fields"]["private_state_fields"] = (
        "SYNTHETIC_NON_SOURCE_REQUIRED_PRIVATE_STATE_CLAIM"
    )
    record["source_required_fields"]["order_authority_fields"] = (
        "SYNTHETIC_NON_SOURCE_REQUIRED_ORDER_AUTHORITY_CLAIM"
    )
    record["submit_order_endpoint"] = "SYNTHETIC_NON_SOURCE_REQUIRED_ORDER_ENDPOINT_CLAIM"
    _registry(fixture)["readiness_records"][0] = record

    failures = validate_connector_capability_registry_fixture(fixture)

    assert any("live_endpoint must remain SOURCE_REQUIRED" in failure for failure in failures)
    assert any(
        "private_state_fields must remain SOURCE_REQUIRED" in failure
        for failure in failures
    )
    assert any(
        "order_authority_fields must remain SOURCE_REQUIRED" in failure
        for failure in failures
    )
    assert any(
        "submit_order_endpoint must remain SOURCE_REQUIRED" in failure
        for failure in failures
    )


def test_connector_capability_fixture_has_no_real_urls_credentials_or_venue_names():
    fixture = _fixture()
    raw_text = json.dumps(fixture, sort_keys=True).lower()

    for fragment in {"://", "www.", "kalshi", "polymarket", "ibkr", "password"}:
        assert fragment not in raw_text
