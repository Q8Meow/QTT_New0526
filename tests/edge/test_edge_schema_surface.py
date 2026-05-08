import json
from pathlib import Path


SCHEMA_PATH = Path(
    "schemas/dashboard_research_edge_quantum_risk/"
    "dashboard_research_edge_quantum_risk.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/dashboard_research_edge_quantum_risk/"
    "synthetic_dashboard_research_edge_quantum_risk_source_required_disabled.v1.fixture.json"
)
EDGE_AND_RISK_GUARDRAILS = {
    "edge_hypothesis_trade_authority_allowed",
    "parameter_stack_selection_live_order_authority_allowed",
    "risk_surface_live_exposure_authority_allowed",
    "replay_execution_allowed",
    "paper_execution_allowed",
    "live_execution_allowed",
    "live_reachability_allowed",
    "order_execution_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "edge_replay_and_paper_required_before_trade_authority",
    "risk_owner_approval_required_before_live_exposure",
    "owner_approval_required_before_live_use",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_edge_schema_disables_hypothesis_stack_and_risk_authority():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert EDGE_AND_RISK_GUARDRAILS.issubset(required)
    assert all(
        properties[field]["const"] is False for field in EDGE_AND_RISK_GUARDRAILS
    )


def test_edge_schema_requires_replay_paper_and_owner_gates():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )


def test_edge_schema_is_static_contract_only_for_trade_and_exposure():
    properties = _schema()["properties"]

    assert "edge_trade_authority" not in properties
    assert "edge_to_trade_live_authority" not in properties
    assert "parameter_stack_order_payload" not in properties
    assert "live_order_authority" not in properties
    assert "risk_live_exposure_authority" not in properties
    assert "runtime_cash_receipt" not in properties
    assert "live_exposure_payload" not in properties
    assert "order_instruction" not in properties
    assert "profit_authority" not in properties


def test_edge_fixture_keeps_hypothesis_and_parameter_stack_inert():
    fixture = _fixture()
    surface = fixture["dashboard_research_edge_quantum_risk"]
    flags = fixture["fixture_no_claim_flags"]

    assert all(fixture[field] is False for field in EDGE_AND_RISK_GUARDRAILS)
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert surface["edge_hypothesis_state"] == "NO_EDGE_TO_TRADE_AUTHORITY"
    assert surface["parameter_stack_selection_state"] == "NO_LIVE_ORDER_AUTHORITY"
    assert surface["risk_surface_state"] == "NO_LIVE_EXPOSURE_AUTHORITY"
    assert flags["treats_edge_hypothesis_as_trade_authority"] is False
    assert flags["treats_parameter_stack_selection_as_live_order_authority"] is False
    assert flags["creates_risk_live_exposure_authority"] is False


def test_edge_fixture_performs_no_replay_paper_live_or_order_execution():
    surface = _fixture()["dashboard_research_edge_quantum_risk"]

    assert surface["replay_state"] == "NO_REPLAY_EXECUTION"
    assert surface["paper_state"] == "NO_PAPER_EXECUTION"
    assert surface["live_execution_state"] == "NO_LIVE_EXECUTION"
    assert surface["live_reachability_state"] == "NO_LIVE_REACHABILITY"
    assert surface["runtime_cash_state"] == "NO_RUNTIME_CASH_FETCH"
    assert surface["runtime_cash_receipt_state"] == "NO_RUNTIME_CASH_RECEIPT"
    assert surface["order_state"] == "NO_ORDER_EXECUTION"
    assert surface["profit_state"] == "NO_PROFIT_CLAIM"
