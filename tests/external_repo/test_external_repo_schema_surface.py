import json
from pathlib import Path


SCHEMA_PATH = Path(
    "schemas/external_repo/external_repo_quarantine_and_bot_taxonomy.schema.json"
)
GUARDRAIL_FIELDS = {
    "external_repo_clone_allowed",
    "external_repo_code_execution_allowed",
    "package_install_script_allowed",
    "dependency_trust_grant_allowed",
    "secret_materialization_allowed",
    "credential_pattern_trust_allowed",
    "api_key_use_allowed",
    "official_venue_fact_authority_allowed",
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "connector_binding_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "order_execution_allowed",
    "neural_training_allowed",
    "neural_inference_allowed",
    "atomicrows_bundle_creation_allowed",
    "atomicrows_bundle_hash_creation_allowed",
    "sha_freeze_authority_allowed",
    "live_reachability_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "supply_chain_quarantine_required_before_dependency_use",
    "credential_quarantine_required_before_pattern_use",
    "accepted_source_evidence_required_before_fact_authority",
    "qtt_native_reimplementation_required_before_execution",
    "owner_approval_required_before_live_use",
}


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_external_repo_schema_is_source_required_and_disabled():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_EXTERNAL_REPO_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == (
        "EXTERNAL_REPO_QUARANTINE_AND_BOT_TAXONOMY_SOURCE_REQUIRED"
    )
    assert schema["additionalProperties"] is True


def test_external_repo_schema_is_static_contract_only():
    schema = _schema()
    properties = schema["properties"]

    assert "external_repo_clone_command" not in properties
    assert "external_repo_checkout_path" not in properties
    assert "external_repo_execution_entrypoint" not in properties
    assert "package_install_command" not in properties
    assert "dependency_lockfile_path" not in properties
    assert "credential_value" not in properties
    assert "secret_value" not in properties
    assert "accepted_source_payload" not in properties
    assert "official_venue_fact_payload" not in properties
    assert "connector_binding_payload" not in properties
    assert "runtime_authority" not in properties
    assert "order_execution_authority" not in properties
    assert "atomicrows_bundle_hash" not in properties
    assert "sha256" not in properties
    assert "freeze_authority" not in properties
    assert "profit_authority" not in properties


def test_external_repo_schema_requires_disabled_guardrails():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in GUARDRAIL_FIELDS)


def test_external_repo_schema_requires_quarantine_gates_before_enablement():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )
