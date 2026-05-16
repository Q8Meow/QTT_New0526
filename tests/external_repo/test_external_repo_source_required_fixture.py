import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/external_repo/"
    "synthetic_external_repo_quarantine_and_bot_taxonomy_source_required_disabled"
    ".v1.fixture.json"
)
SCHEMA_PATH = Path(
    "schemas/external_repo/external_repo_quarantine_and_bot_taxonomy.schema.json"
)
CANONICAL_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")
EXPECTED_FIXTURE_NAME = (
    "synthetic_external_repo_quarantine_and_bot_taxonomy_source_required_disabled"
    ".v1.fixture.json"
)
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_EXTERNAL_REPO_NOT_SOURCE_FACT"
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
    "contains_real_external_repo_identifier",
    "contains_external_repo_clone",
    "contains_external_repo_code",
    "contains_dependency_manifest",
    "contains_package_install_script",
    "contains_dependency_trust_grant",
    "contains_secret_material",
    "contains_credentials",
    "contains_credential_pattern_trust",
    "contains_official_venue_fact_authority",
    "contains_accepted_source_payload",
    "contains_real_source_locator",
    "contains_connector_binding",
    "contains_private_state",
    "contains_runtime_cash_value",
    "contains_runtime_cash_receipt",
    "contains_live_reachability",
    "contains_order_instruction",
    "contains_neural_training_output",
    "contains_neural_inference_output",
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "contains_sha_freeze_authority",
    "contains_profit_claim",
    "clones_external_repo",
    "executes_external_repo_code",
    "runs_package_install_scripts",
    "grants_dependency_trust",
    "materializes_secrets",
    "trusts_credential_patterns",
    "grants_official_venue_fact_authority",
    "retrieves_source_facts",
    "accepts_source_facts",
    "binds_connector",
    "fetches_private_state",
    "fetches_runtime_cash",
    "creates_runtime_cash_receipts",
    "creates_live_reachability",
    "executes_orders",
    "trains_neural_model",
    "runs_neural_inference",
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


def test_external_repo_fixture_exists_with_expected_name_and_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR12_EXTERNAL_REPO_QUARANTINE_AND_BOT_TAXONOMY_SOURCE_"
        "REQUIRED_DISABLED_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR12_EXTERNAL_REPO_QUARANTINE_AND_BOT_TAXONOMY_SOURCE_REQUIRED_"
        "DISABLED_FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR12_")


def test_external_repo_fixture_validates_against_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    for field, definition in schema["properties"].items():
        if "const" in definition and field in fixture:
            assert fixture[field] == definition["const"]


def test_external_repo_fixture_keeps_all_guardrails_disabled():
    fixture = _fixture()

    assert all(fixture[field] is False for field in GUARDRAIL_FIELDS)
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_external_repo_fixture_has_no_live_private_or_real_source_material():
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


def test_external_repo_fixture_is_inert_across_all_forbidden_boundaries():
    surface = _fixture()["external_repo_quarantine_and_bot_taxonomy"]

    assert surface["static_contract_state"] == "STATIC_CONTRACT_ONLY_NO_RUNTIME_AUTHORITY"
    assert surface["external_repo_clone_state"] == "NO_EXTERNAL_REPO_CLONE"
    assert surface["external_repo_reference"] == "SYNTHETIC_NONE_NO_EXTERNAL_REPO"
    assert surface["external_repo_code_execution_state"] == (
        "NO_EXTERNAL_REPO_CODE_EXECUTION"
    )
    assert surface["package_install_script_state"] == (
        "NO_PACKAGE_INSTALL_SCRIPT_EXECUTION"
    )
    assert surface["dependency_trust_state"] == "NO_DEPENDENCY_TRUST_GRANT"
    assert surface["secret_materialization_state"] == "NO_SECRET_MATERIALIZATION"
    assert surface["credential_pattern_state"] == (
        "QUARANTINED_NO_CREDENTIAL_PATTERN_TRUST"
    )
    assert surface["bot_taxonomy_state"] == (
        "SYNTHETIC_TAXONOMY_PLACEHOLDER_ONLY_NO_AUTHORITY"
    )
    assert surface["taxonomy_route_state"] == (
        "QTT_NATIVE_REIMPLEMENTATION_REQUIRED_NO_EXTERNAL_CODE_ADOPTION"
    )
    assert surface["official_venue_fact_authority_state"] == (
        "NO_OFFICIAL_VENUE_FACT_AUTHORITY"
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
    assert surface["neural_state"] == "NO_NEURAL_TRAINING_OR_INFERENCE"
    assert surface["atomicrows_state"] == "NO_ATOMICROWS_BUNDLE_OR_HASH"
    assert surface["atomicrows_bundle_reference"] == (
        "SYNTHETIC_NONE_NO_ATOMICROWS_BUNDLE"
    )
    assert surface["atomicrows_bundle_hash_reference"] == (
        "SYNTHETIC_NONE_NO_ATOMICROWS_HASH"
    )
    assert surface["sha_freeze_state"] == "NO_SHA_OR_FREEZE_AUTHORITY"
    assert surface["profit_state"] == "NO_PROFIT_CLAIM"


def test_external_repo_fixture_does_not_create_bundle_or_hash_files():
    assert CANONICAL_BUNDLE_PATH.exists()
    assert not CANONICAL_BUNDLE_SHA_PATH.exists()
