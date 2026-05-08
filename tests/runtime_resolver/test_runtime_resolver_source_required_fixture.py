import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/runtime_resolver/"
    "synthetic_runtime_resolver_source_required_disabled.v1.fixture.json"
)
SCHEMA_PATH = Path("schemas/runtime_resolver/runtime_resolver.schema.json")
EXPECTED_FIXTURE_NAME = (
    "synthetic_runtime_resolver_source_required_disabled.v1.fixture.json"
)
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_RUNTIME_RESOLVER_NOT_SOURCE_FACT"
)
GUARDRAIL_FIELDS = {
    "resolver_execution_allowed",
    "candidate_resolution_allowed",
    "cross_platform_selection_allowed",
    "market_selection_allowed",
    "selected_candidate_allowed",
    "connector_binding_allowed",
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "live_venue_access_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_resolution",
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
    "account_id",
    "-----begin",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "contains_real_venue_identifier",
    "contains_real_market_identifier",
    "contains_real_connector_identifier",
    "contains_credentials",
    "contains_real_url",
    "contains_candidate_resolution",
    "contains_selected_candidate",
    "contains_accepted_source_payload",
    "contains_private_state",
    "contains_runtime_cash_value",
    "contains_order_instruction",
    "executes_resolver",
    "resolves_candidates",
    "selects_cross_platform_candidate",
    "selects_market",
    "binds_connector",
    "retrieves_source_facts",
    "accepts_source_facts",
    "fetches_private_state",
    "fetches_runtime_cash",
    "accesses_live_venue",
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


def test_runtime_resolver_fixture_exists_with_expected_name_and_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR9_RUNTIME_RESOLVER_SOURCE_REQUIRED_DISABLED_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR9_RUNTIME_RESOLVER_SOURCE_REQUIRED_DISABLED_FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR9_")


def test_runtime_resolver_fixture_matches_source_required_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    for field, definition in schema["properties"].items():
        if "const" in definition and field in fixture:
            assert fixture[field] == definition["const"]


def test_runtime_resolver_fixture_keeps_all_guardrails_disabled():
    fixture = _fixture()

    assert all(fixture[field] is False for field in GUARDRAIL_FIELDS)
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_runtime_resolver_fixture_has_no_live_private_or_real_source_material():
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


def test_runtime_resolver_fixture_is_inert_and_has_no_selected_candidate():
    resolver = _fixture()["runtime_resolver"]

    assert resolver["resolver_execution_state"] == "DISABLED_NO_RESOLVER_EXECUTION"
    assert resolver["candidate_resolution_state"] == (
        "BLOCKED_SOURCE_REQUIRED_NO_CANDIDATE_RESOLUTION"
    )
    assert resolver["candidate_set_state"] == "NO_CANDIDATES_PRESENT"
    assert resolver["selected_candidate_state"] == "NO_SELECTED_CANDIDATE"
    assert resolver["selected_candidate_reference"] is None
    assert resolver["cross_platform_selection_state"] == (
        "NOT_EXECUTED_NO_SELECTION_AUTHORITY"
    )
    assert resolver["market_selection_state"] == (
        "NOT_EXECUTED_NO_MARKET_SELECTION_AUTHORITY"
    )
    assert resolver["connector_binding_state"] == "NOT_BOUND_NO_CONNECTOR_AUTHORITY"
    assert resolver["source_retrieval_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert resolver["source_acceptance_state"] == "NOT_EXECUTED_NO_ACCEPTED_SOURCE"
    assert resolver["private_state_state"] == "NO_PRIVATE_STATE_FETCH"
    assert resolver["runtime_cash_state"] == "NO_RUNTIME_CASH_FETCH"
    assert resolver["live_access_state"] == "NO_LIVE_VENUE_ACCESS"
    assert resolver["order_state"] == "NO_ORDER_EXECUTION"
