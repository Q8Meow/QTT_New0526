import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/neural_signal/neural_signal.schema.json")
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


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_neural_signal_schema_is_source_required_and_disabled():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_NEURAL_SIGNAL_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == "NEURAL_SIGNAL_SOURCE_REQUIRED"
    assert schema["additionalProperties"] is True


def test_neural_signal_schema_is_static_contract_only():
    schema = _schema()
    properties = schema["properties"]

    assert "neural_training_receipt" not in properties
    assert "neural_model_weights" not in properties
    assert "neural_model_artifact_path" not in properties
    assert "raw_model_probability" not in properties
    assert "raw_price_prediction" not in properties
    assert "walk_forward_runner" not in properties
    assert "model_calibration_report_payload" not in properties
    assert "model_drift_monitor_payload" not in properties
    assert "neural_promotion_gate_packet" not in properties
    assert "accepted_source_payload" not in properties
    assert "connector_binding_payload" not in properties
    assert "private_state_payload" not in properties
    assert "runtime_cash_receipt" not in properties
    assert "order_execution_authority" not in properties
    assert "external_repo_clone_command" not in properties
    assert "package_install_command" not in properties
    assert "atomicrows_bundle_hash" not in properties
    assert "sha256" not in properties
    assert "freeze_authority" not in properties
    assert "profit_authority" not in properties


def test_neural_signal_schema_requires_disabled_guardrails():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in GUARDRAIL_FIELDS)


def test_neural_signal_schema_requires_source_validation_and_owner_gates():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )
