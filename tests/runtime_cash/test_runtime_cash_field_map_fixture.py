import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/runtime_cash/"
    "synthetic_runtime_cash_field_map_source_required.v1.fixture.json"
)
SCHEMA_PATH = Path("schemas/runtime_cash/runtime_cash_field_map.schema.json")
EXPECTED_FIXTURE_NAME = "synthetic_runtime_cash_field_map_source_required.v1.fixture.json"
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_RUNTIME_CASH_NOT_SOURCE_FACT"
)
GUARDRAIL_FIELDS = {
    "runtime_cash_semantic_population_allowed",
    "account_balance_semantics_allowed",
    "buying_power_semantics_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "connector_binding_allowed",
    "live_account_access_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_semantics",
    "runtime_cash_receipt_required_before_values",
    "owner_approval_required_before_live_use",
}
FORBIDDEN_TEXT_FRAGMENTS = {
    "://",
    "www.",
    "http",
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
    "owner_uploaded_private_doc_locator",
    "runtime_cash_receipt_id",
    "connector_unlock_authority",
    "-----begin",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "contains_real_account_identifier",
    "contains_balance_value",
    "contains_cash_value",
    "contains_buying_power_value",
    "contains_credentials",
    "contains_real_url",
    "contains_venue_identifier",
    "contains_private_locator",
    "contains_runtime_cash_receipt",
    "contains_accepted_source_evidence",
    "unlocks_connector_authority",
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


def test_runtime_cash_fixture_exists_with_expected_name_and_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR8_RUNTIME_CASH_FIELD_MAP_SOURCE_REQUIRED_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR8_RUNTIME_CASH_FIELD_MAP_SOURCE_REQUIRED_FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR8_")


def test_runtime_cash_fixture_matches_source_required_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"
    assert fixture["schema_authority_class"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_RUNTIME_CASH_AUTHORITY"
    )
    assert fixture["surface_kind"] == "RUNTIME_CASH_FIELD_MAP_SOURCE_REQUIRED"


def test_runtime_cash_fixture_keeps_all_guardrails_disabled():
    fixture = _fixture()

    assert all(fixture[field] is False for field in GUARDRAIL_FIELDS)
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_runtime_cash_fixture_has_no_live_or_private_runtime_material():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    for fragment in FORBIDDEN_TEXT_FRAGMENTS:
        assert fragment not in raw_text

    fixture = _fixture()
    for key, value in _walk(fixture):
        if key.endswith("_allowed") and isinstance(value, bool):
            assert value is False
        if isinstance(value, str):
            assert "://" not in value
            assert "\\" not in value
        if type(value) in {int, float}:
            raise AssertionError(f"fixture must not contain numeric runtime values: {key}")
        if key.endswith("_reference") and isinstance(value, str):
            assert value.startswith("SYNTHETIC_")


def test_runtime_cash_fixture_requires_evidence_and_receipts_without_creating_them():
    field_map = _fixture()["runtime_cash_field_map"]

    assert field_map["source_evidence_state"] == "NO_ACCEPTED_SOURCE_EVIDENCE_PRESENT"
    assert field_map["runtime_cash_receipt_state"] == "NO_RUNTIME_CASH_RECEIPT_PRESENT"
    assert field_map["semantic_state"] == "DISABLED_UNTIL_EVIDENCE_AND_RECEIPT"
    assert field_map["value_state"] == "NO_RUNTIME_VALUES_PRESENT"
    assert field_map["connector_state"] == "NOT_BOUND_NO_CONNECTOR_AUTHORITY"
    assert field_map["live_account_state"] == "NO_LIVE_ACCOUNT_ACCESS"
    assert field_map["account_reference"] == "SYNTHETIC_NONE_NO_ACCOUNT_REFERENCE"
    assert field_map["runtime_cash_receipt_reference"] == (
        "SYNTHETIC_NONE_NO_RUNTIME_CASH_RECEIPT"
    )
