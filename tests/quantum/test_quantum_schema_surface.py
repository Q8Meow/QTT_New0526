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
CANONICAL_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")
QUANTUM_AND_CROSS_BOUNDARY_GUARDRAILS = {
    "quantum_optimizer_order_submission_allowed",
    "quantum_trade_intent_execution_router_bypass_allowed",
    "connector_binding_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "order_execution_allowed",
    "neural_training_allowed",
    "neural_inference_allowed",
    "external_repo_clone_allowed",
    "package_install_script_allowed",
    "atomicrows_bundle_creation_allowed",
    "atomicrows_bundle_hash_creation_allowed",
    "sha_freeze_authority_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "execution_router_required_before_quantum_trade_intent",
    "owner_approval_required_before_live_use",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "contains_dashboard_runtime_ui_service",
    "creates_dashboard_runtime_ui_service",
    "contains_telegram_runtime_notification_service",
    "creates_telegram_runtime_notification_service",
    "contains_runtime_research_ingestion_service",
    "creates_runtime_research_ingestion_service",
    "treats_research_intake_as_source_fact_authority",
    "treats_owner_submitted_website_x_news_material_as_source_fact",
    "treats_edge_hypothesis_as_trade_authority",
    "treats_parameter_stack_selection_as_live_order_authority",
    "submits_quantum_optimizer_orders",
    "bypasses_execution_router_with_quantum_trade_intent",
    "creates_risk_live_exposure_authority",
    "contains_accepted_source_payload",
    "contains_real_source_locator",
    "retrieves_source_facts",
    "accepts_source_facts",
    "contains_connector_binding",
    "binds_connector",
    "contains_credentials",
    "contains_private_state",
    "fetches_private_state",
    "contains_runtime_cash_value",
    "fetches_runtime_cash",
    "contains_runtime_cash_receipt",
    "creates_runtime_cash_receipts",
    "executes_replay",
    "executes_paper",
    "executes_live",
    "contains_live_reachability",
    "creates_live_reachability",
    "contains_order_instruction",
    "executes_orders",
    "contains_neural_training_output",
    "contains_neural_inference_output",
    "trains_neural_model",
    "runs_neural_inference",
    "contains_external_repo_clone",
    "clones_external_repo",
    "contains_package_install_script",
    "installs_packages",
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "contains_sha_freeze_authority",
    "creates_sha_freeze_authority",
    "contains_profit_claim",
    "creates_profit_evidence",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_quantum_schema_disables_optimizer_orders_and_router_bypass():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert QUANTUM_AND_CROSS_BOUNDARY_GUARDRAILS.issubset(required)
    assert all(
        properties[field]["const"] is False
        for field in QUANTUM_AND_CROSS_BOUNDARY_GUARDRAILS
    )
    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )


def test_quantum_schema_is_static_contract_only():
    properties = _schema()["properties"]

    assert "quantum_optimizer_order_payload" not in properties
    assert "quantum_order_submission_endpoint" not in properties
    assert "quantum_trade_intent_router_bypass" not in properties
    assert "execution_router_bypass_authority" not in properties
    assert "connector_binding_payload" not in properties
    assert "private_state_payload" not in properties
    assert "runtime_cash_receipt" not in properties
    assert "neural_model_artifact_path" not in properties
    assert "external_repo_clone_command" not in properties
    assert "package_install_command" not in properties
    assert "atomicrows_bundle_hash" not in properties
    assert "sha256" not in properties
    assert "freeze_authority" not in properties
    assert "profit_authority" not in properties


def test_quantum_fixture_keeps_all_no_claim_flags_disabled():
    fixture = _fixture()

    assert all(
        fixture[field] is False for field in QUANTUM_AND_CROSS_BOUNDARY_GUARDRAILS
    )
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_quantum_fixture_does_not_submit_orders_or_bypass_router():
    surface = _fixture()["dashboard_research_edge_quantum_risk"]

    assert surface["quantum_optimizer_state"] == "NO_QUANTUM_ORDER_SUBMISSION"
    assert surface["quantum_trade_intent_state"] == "NO_EXECUTION_ROUTER_BYPASS"
    assert surface["connector_binding_state"] == "NOT_BOUND_NO_CONNECTOR_AUTHORITY"
    assert surface["private_state_state"] == "NO_PRIVATE_STATE_FETCH"
    assert surface["runtime_cash_state"] == "NO_RUNTIME_CASH_FETCH"
    assert surface["runtime_cash_receipt_state"] == "NO_RUNTIME_CASH_RECEIPT"
    assert surface["api_key_state"] == "NO_API_KEY_USE"
    assert surface["order_state"] == "NO_ORDER_EXECUTION"


def test_quantum_fixture_has_no_neural_external_atomicrows_sha_or_profit_authority():
    surface = _fixture()["dashboard_research_edge_quantum_risk"]

    assert surface["neural_state"] == "NO_NEURAL_TRAINING_OR_INFERENCE"
    assert surface["external_repo_state"] == "NO_EXTERNAL_REPO_CLONE_OR_INSTALL"
    assert surface["atomicrows_state"] == "NO_ATOMICROWS_BUNDLE_OR_HASH"
    assert surface["atomicrows_bundle_reference"] == (
        "SYNTHETIC_NONE_NO_ATOMICROWS_BUNDLE"
    )
    assert surface["atomicrows_bundle_hash_reference"] == (
        "SYNTHETIC_NONE_NO_ATOMICROWS_HASH"
    )
    assert surface["sha_freeze_state"] == "NO_SHA_OR_FREEZE_AUTHORITY"
    assert surface["profit_state"] == "NO_PROFIT_CLAIM"
    assert CANONICAL_BUNDLE_PATH.exists()
    assert not CANONICAL_BUNDLE_SHA_PATH.exists()
