import json
from pathlib import Path


SCHEMA_PATH = Path(
    "schemas/dashboard_research_edge_quantum_risk/"
    "dashboard_research_edge_quantum_risk.schema.json"
)
FIXTURE_DIR = Path("tests/fixtures/dashboard_research_edge_quantum_risk")
FIXTURE_PATH = (
    FIXTURE_DIR
    / "synthetic_dashboard_research_edge_quantum_risk_source_required_disabled.v1.fixture.json"
)
DASHBOARD_RUNTIME_GUARDRAILS = {
    "dashboard_runtime_ui_service_creation_allowed",
    "telegram_runtime_notification_service_creation_allowed",
    "runtime_research_ingestion_service_creation_allowed",
    "live_reachability_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_research_fact_authority",
    "owner_material_source_acceptance_required_before_fact_use",
    "owner_approval_required_before_live_use",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_dashboard_schema_surface_is_source_required_disabled_static_contract():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_DASHBOARD_RESEARCH_EDGE_QUANTUM_RISK_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == (
        "DASHBOARD_RESEARCH_EDGE_QUANTUM_RISK_SOURCE_REQUIRED"
    )
    assert schema["additionalProperties"] is True
    assert sorted(FIXTURE_DIR.glob("*.fixture.json")) == [FIXTURE_PATH]


def test_dashboard_schema_disables_runtime_ui_and_telegram_services():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert DASHBOARD_RUNTIME_GUARDRAILS.issubset(required)
    assert all(
        properties[field]["const"] is False for field in DASHBOARD_RUNTIME_GUARDRAILS
    )


def test_dashboard_schema_requires_prior_gates_before_enablement():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )


def test_dashboard_schema_does_not_define_runtime_service_payloads():
    properties = _schema()["properties"]

    assert "dashboard_runtime_service_module" not in properties
    assert "dashboard_runtime_ui_endpoint" not in properties
    assert "telegram_runtime_service_module" not in properties
    assert "telegram_notification_endpoint" not in properties
    assert "runtime_research_ingestion_service_module" not in properties
    assert "live_reachability_endpoint" not in properties
    assert "api_key_value" not in properties
    assert "order_execution_authority" not in properties


def test_dashboard_fixture_creates_no_runtime_ui_or_notification_service():
    surface = _fixture()["dashboard_research_edge_quantum_risk"]
    flags = _fixture()["fixture_no_claim_flags"]

    assert surface["dashboard_ui_state"] == "NO_DASHBOARD_RUNTIME_UI_SERVICE_CREATED"
    assert surface["telegram_notification_state"] == (
        "NO_TELEGRAM_RUNTIME_NOTIFICATION_SERVICE_CREATED"
    )
    assert surface["runtime_research_ingestion_state"] == (
        "NO_RUNTIME_RESEARCH_INGESTION_SERVICE_CREATED"
    )
    assert flags["creates_dashboard_runtime_ui_service"] is False
    assert flags["creates_telegram_runtime_notification_service"] is False
    assert flags["creates_runtime_research_ingestion_service"] is False
