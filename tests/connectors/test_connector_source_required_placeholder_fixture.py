import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/connectors/synthetic_connector_source_required_placeholder.v1.fixture.json"
)
SCHEMA_PATH = Path("schemas/connectors/source_required_placeholders.schema.json")
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_CONNECTOR_NOT_SOURCE_FACT"
)
EXPECTED_FIXTURE_NAME = "synthetic_connector_source_required_placeholder.v1.fixture.json"
GUARDRAIL_FIELDS = {
    "connector_semantic_binding_allowed",
    "live_connector_allowed",
    "api_key_required_or_allowed",
    "source_acceptance_execution_allowed",
    "private_state_fetch_allowed",
    "order_execution_allowed",
    "runtime_cash_fetch_allowed",
    "profit_claim_allowed",
}
FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
    "kalshi",
    "polymarket",
    "interactivebrokers",
    "ibkr",
    "secret_key",
    "client_secret",
    "sk_live",
    "pk_live",
    "bearer ",
    "password",
    "-----begin",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "contains_real_connector",
    "contains_credentials",
    "contains_real_url",
    "contains_venue_api_semantics",
    "contains_accepted_source_facts",
    "unlocks_connector_semantics",
    "retrieves_source_facts",
    "accepts_source_facts",
    "fetches_private_state",
    "fetches_runtime_cash",
    "executes_orders",
    "creates_profit_evidence",
}


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def test_connector_fixture_exists_with_expected_name_and_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR7_CONNECTOR_SOURCE_REQUIRED_PLACEHOLDER_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR7_CONNECTOR_SOURCE_REQUIRED_PLACEHOLDER_FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR7_")


def test_connector_fixture_matches_source_required_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"
    assert fixture["schema_authority_class"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_CONNECTOR_AUTHORITY"
    )
    assert fixture["surface_kind"] == "CONNECTOR_SOURCE_REQUIRED_PLACEHOLDER"


def test_connector_fixture_keeps_all_guardrails_disabled():
    fixture = _fixture()

    assert all(fixture[field] is False for field in GUARDRAIL_FIELDS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_connector_fixture_has_no_retrievable_sources_credentials_or_real_venues():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    for fragment in FORBIDDEN_TEXT_FRAGMENTS:
        assert fragment not in raw_text

    fixture = _fixture()
    for key, value in _walk(fixture):
        if "locator" in key.lower() and isinstance(value, str):
            assert value.startswith("SYNTHETIC_")
            assert "://" not in value
        if key.endswith("_allowed") and isinstance(value, bool):
            assert value is False


def test_connector_fixture_has_no_source_acceptance_or_unlock_authority():
    placeholder = _fixture()["connector_placeholder"]

    assert placeholder["source_evidence_state"] == "NO_ACCEPTED_SOURCE_EVIDENCE_PRESENT"
    assert placeholder["credential_state"] == "CREDENTIALS_NOT_REQUIRED_NOT_ALLOWED"
    assert placeholder["semantic_binding_state"] == "NOT_BOUND_NO_UNLOCK_AUTHORITY"
    assert placeholder["runtime_state"] == "DISABLED_NO_RUNTIME_AUTHORITY"
    assert placeholder["accepted_source_fact_reference"] == (
        "SYNTHETIC_NONE_NO_ACCEPTED_SOURCE_FACT"
    )
    assert placeholder["venue_api_semantics_reference"] == (
        "SYNTHETIC_NONE_NO_VENUE_API_SEMANTICS"
    )
