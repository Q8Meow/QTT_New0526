import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/neural_signal/"
    "synthetic_neural_signal_source_required_disabled.v1.fixture.json"
)
SCHEMA_PATH = Path("schemas/neural_signal/neural_signal.schema.json")
EXPECTED_FIXTURE_NAME = "synthetic_neural_signal_source_required_disabled.v1.fixture.json"
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_NEURAL_SIGNAL_NOT_SOURCE_FACT"
)
GUARDRAIL_FIELDS = {
    "neural_training_allowed",
    "neural_inference_allowed",
    "neural_model_artifact_creation_allowed",
    "raw_model_probability_order_authority_allowed",
    "raw_price_prediction_live_default_allowed",
    "walk_forward_validation_execution_allowed",
    "model_calibration_report_creation_allowed",
    "model_drift_monitor_creation_allowed",
    "neural_promotion_gate_packet_creation_allowed",
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "connector_binding_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "live_reachability_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
    "external_repo_clone_allowed",
    "package_install_script_allowed",
    "atomicrows_bundle_creation_allowed",
    "atomicrows_bundle_hash_creation_allowed",
    "sha_freeze_authority_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_neural_signal",
    "stationarity_and_leakage_audit_required_before_validation",
    "purged_walk_forward_validation_required_before_promotion",
    "calibration_and_drift_review_required_before_promotion",
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
    "atomicrows.bundle",
    ".sha256",
    "owner_uploaded_private_doc_locator",
    "runtime_cash_receipt_id",
    "model_artifact_path",
    "model.predict",
    "run_inference(",
    "train_model(",
    "fit_model(",
    "torch.load",
    "tensorflow",
    "keras",
    "onnxruntime",
    "git clone",
    "pip install",
    "npm install",
    "pnpm install",
    "yarn install",
    "poetry install",
    "conda install",
    "-----begin",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "contains_neural_training_output",
    "contains_neural_inference_output",
    "contains_neural_model_artifact",
    "contains_raw_model_probability_order_authority",
    "contains_raw_price_prediction_live_default",
    "contains_walk_forward_validation_execution",
    "contains_model_calibration_report",
    "contains_model_drift_monitor",
    "contains_neural_promotion_gate_packet",
    "contains_accepted_source_payload",
    "contains_real_source_locator",
    "contains_connector_binding",
    "contains_credentials",
    "contains_private_state",
    "contains_runtime_cash_value",
    "contains_runtime_cash_receipt",
    "contains_live_reachability",
    "contains_order_instruction",
    "contains_external_repo_clone",
    "contains_package_install_script",
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "contains_sha_freeze_authority",
    "contains_profit_claim",
    "trains_neural_model",
    "runs_neural_inference",
    "creates_neural_model_artifact",
    "treats_raw_model_probability_as_order_authority",
    "treats_raw_price_prediction_as_live_default",
    "executes_walk_forward_validation",
    "creates_model_calibration_report",
    "creates_model_drift_monitor",
    "creates_neural_promotion_gate_packet",
    "retrieves_source_facts",
    "accepts_source_facts",
    "binds_connector",
    "fetches_private_state",
    "fetches_runtime_cash",
    "creates_runtime_cash_receipts",
    "creates_live_reachability",
    "executes_orders",
    "clones_external_repo",
    "installs_packages",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_hash",
    "creates_sha_freeze_authority",
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


def test_neural_signal_fixture_exists_with_expected_name_and_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR13_NEURAL_SIGNAL_SOURCE_REQUIRED_DISABLED_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR13_NEURAL_SIGNAL_SOURCE_REQUIRED_DISABLED_FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR13_")


def test_neural_signal_fixture_validates_against_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    for field, definition in schema["properties"].items():
        if "const" in definition and field in fixture:
            assert fixture[field] == definition["const"]


def test_neural_signal_fixture_keeps_all_guardrails_disabled():
    fixture = _fixture()

    assert all(fixture[field] is False for field in GUARDRAIL_FIELDS)
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_neural_signal_fixture_has_no_live_private_model_or_real_source_material():
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


def test_neural_signal_fixture_is_inert_across_all_forbidden_boundaries():
    surface = _fixture()["neural_signal"]

    assert surface["static_contract_state"] == "STATIC_CONTRACT_ONLY_NO_RUNTIME_AUTHORITY"
    assert surface["neural_training_state"] == "NO_NEURAL_MODEL_TRAINING"
    assert surface["neural_inference_state"] == "NO_NEURAL_INFERENCE"
    assert surface["model_artifact_state"] == "NO_NEURAL_MODEL_ARTIFACT_CREATED"
    assert surface["raw_model_probability_order_authority_state"] == (
        "NO_RAW_MODEL_PROBABILITY_ORDER_AUTHORITY"
    )
    assert surface["raw_price_prediction_live_default_state"] == (
        "NO_RAW_PRICE_PREDICTION_LIVE_DEFAULT"
    )
    assert surface["walk_forward_validation_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert surface["calibration_report_state"] == (
        "NO_MODEL_CALIBRATION_REPORT_CREATED"
    )
    assert surface["drift_monitor_state"] == "NO_MODEL_DRIFT_MONITOR_CREATED"
    assert surface["promotion_gate_packet_state"] == (
        "NO_NEURAL_PROMOTION_GATE_PACKET_CREATED"
    )
    assert surface["source_retrieval_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert surface["source_acceptance_state"] == "NOT_EXECUTED_NO_ACCEPTED_SOURCE"
    assert surface["source_reference"] == "SYNTHETIC_NONE_NO_ACCEPTED_SOURCE"
    assert surface["connector_binding_state"] == "NOT_BOUND_NO_CONNECTOR_AUTHORITY"
    assert surface["private_state_state"] == "NO_PRIVATE_STATE_FETCH"
    assert surface["runtime_cash_state"] == "NO_RUNTIME_CASH_FETCH"
    assert surface["runtime_cash_receipt_state"] == "NO_RUNTIME_CASH_RECEIPT"
    assert surface["live_reachability_state"] == "NO_LIVE_REACHABILITY"
    assert surface["api_key_state"] == "NO_API_KEY_USE"
    assert surface["order_state"] == "NO_ORDER_EXECUTION"
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
