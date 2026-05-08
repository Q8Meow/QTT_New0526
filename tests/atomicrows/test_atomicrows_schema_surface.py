import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/atomicrows/atomicrows_generated_derivative_gate.schema.json")
CANONICAL_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")
GUARDRAIL_FIELDS = {
    "atomicrows_bundle_creation_allowed",
    "atomicrows_bundle_hash_creation_allowed",
    "sha_freeze_authority_allowed",
    "generated_derivative_authority_allowed",
    "generated_derivative_runtime_artifact_creation_allowed",
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "connector_binding_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "live_reachability_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
    "neural_training_allowed",
    "neural_inference_allowed",
    "external_repo_clone_allowed",
    "package_install_script_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "accepted_source_evidence_required_before_bundle",
    "owner_approval_required_before_live_use",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_atomicrows_schema_is_source_required_and_disabled():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == (
        "ATOMICROWS_GENERATED_DERIVATIVE_GATE_SOURCE_REQUIRED"
    )
    assert schema["additionalProperties"] is True


def test_atomicrows_schema_is_static_contract_only():
    schema = _schema()
    properties = schema["properties"]

    assert "bundle_hash" not in properties
    assert "bundle_sha256" not in properties
    assert "sha256" not in properties
    assert "freeze_authority" not in properties
    assert "atomicrows_runtime_authority" not in properties
    assert "generated_derivative_runtime_authority" not in properties


def test_atomicrows_schema_requires_disabled_guardrails():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in GUARDRAIL_FIELDS)


def test_atomicrows_schema_requires_source_and_owner_gates_before_enablement():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )


def test_atomicrows_schema_does_not_create_bundle_or_hash_files():
    assert not CANONICAL_BUNDLE_PATH.exists()
    assert not CANONICAL_BUNDLE_SHA_PATH.exists()
