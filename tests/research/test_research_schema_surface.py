import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/dashboard_research_edge_quantum_risk/"
    "synthetic_dashboard_research_edge_quantum_risk_source_required_disabled.v1.fixture.json"
)
SCHEMA_PATH = Path(
    "schemas/dashboard_research_edge_quantum_risk/"
    "dashboard_research_edge_quantum_risk.schema.json"
)
EXPECTED_FIXTURE_NAME = (
    "synthetic_dashboard_research_edge_quantum_risk_source_required_disabled"
    ".v1.fixture.json"
)
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_DASHBOARD_NOT_RESEARCH_FACT_NOT_"
    "EDGE_TRADE_NOT_QUANTUM_ORDER_NOT_RISK_EXPOSURE"
)
RESEARCH_GUARDRAIL_FIELDS = {
    "research_intake_source_fact_authority_allowed",
    "owner_submitted_website_x_news_material_source_fact_authority_allowed",
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "connector_binding_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
}
RESEARCH_REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_research_fact_authority",
    "owner_material_source_acceptance_required_before_fact_use",
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
    "\"sk_live_",
    "\"pk_live_",
    "bearer ",
    "password",
    "account_id",
    "atomicrows.bundle",
    ".sha256",
    "owner_uploaded_private_doc_locator",
    "runtime_cash_receipt_id",
    "git clone",
    "pip install",
    "npm install",
    "pnpm install",
    "yarn install",
    "poetry install",
    "conda install",
    "-----begin",
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


def test_research_fixture_exists_with_expected_name_and_synthetic_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR14_DASHBOARD_RESEARCH_EDGE_QUANTUM_RISK_SOURCE_REQUIRED_"
        "DISABLED_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR14_DASHBOARD_RESEARCH_EDGE_QUANTUM_RISK_SOURCE_REQUIRED_DISABLED_"
        "FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR14_")


def test_research_fixture_validates_against_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    for field, definition in schema["properties"].items():
        if "const" in definition and field in fixture:
            assert fixture[field] == definition["const"]


def test_research_schema_and_fixture_keep_intake_non_authoritative():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])
    fixture = _fixture()
    surface = fixture["dashboard_research_edge_quantum_risk"]
    flags = fixture["fixture_no_claim_flags"]

    assert RESEARCH_GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in RESEARCH_GUARDRAIL_FIELDS)
    assert all(fixture[field] is False for field in RESEARCH_GUARDRAIL_FIELDS)
    assert all(
        fixture[field] is True for field in RESEARCH_REQUIRED_BEFORE_ENABLE_MARKERS
    )
    assert surface["research_intake_state"] == (
        "RESEARCH_INPUT_ONLY_NOT_SOURCE_FACT_AUTHORITY"
    )
    assert surface["owner_submitted_material_state"] == (
        "WEBSITE_X_NEWS_MATERIAL_RESEARCH_INPUT_ONLY"
    )
    assert flags["treats_research_intake_as_source_fact_authority"] is False
    assert flags["treats_owner_submitted_website_x_news_material_as_source_fact"] is False


def test_research_fixture_performs_no_source_retrieval_or_acceptance():
    fixture = _fixture()
    surface = fixture["dashboard_research_edge_quantum_risk"]
    flags = fixture["fixture_no_claim_flags"]

    assert surface["source_retrieval_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert surface["source_acceptance_state"] == "NOT_EXECUTED_NO_ACCEPTED_SOURCE"
    assert surface["source_reference"] == "SYNTHETIC_NONE_NO_ACCEPTED_SOURCE"
    assert flags["retrieves_source_facts"] is False
    assert flags["accepts_source_facts"] is False
    assert flags["contains_accepted_source_payload"] is False
    assert flags["contains_real_source_locator"] is False


def test_research_fixture_has_no_live_private_or_real_source_material():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    for fragment in FORBIDDEN_TEXT_FRAGMENTS:
        assert fragment not in raw_text

    for key, value in _walk(_fixture()):
        if key.endswith("_allowed") and isinstance(value, bool):
            assert value is False
        if isinstance(value, str):
            assert "://" not in value
            assert "\\" not in value
        if type(value) in {int, float}:
            raise AssertionError(f"fixture must not contain numeric runtime values: {key}")
        if key.endswith("_reference") and isinstance(value, str):
            assert value.startswith("SYNTHETIC_")
