import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_generated_derivative_gate_source_required_disabled.v1.fixture.json"
)
SCHEMA_PATH = Path("schemas/atomicrows/atomicrows_generated_derivative_gate.schema.json")
CANONICAL_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")
EXPECTED_FIXTURE_NAME = (
    "synthetic_atomicrows_generated_derivative_gate_source_required_disabled"
    ".v1.fixture.json"
)
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_BUNDLE_NOT_SOURCE_FACT"
)
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
    "-----begin",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "contains_atomicrows_bundle",
    "contains_atomicrows_bundle_hash",
    "contains_sha_freeze_authority",
    "contains_generated_derivative_runtime_artifact",
    "treats_generated_derivative_as_authoritative",
    "contains_accepted_source_payload",
    "contains_real_source_locator",
    "contains_connector_binding",
    "contains_credentials",
    "contains_private_state",
    "contains_runtime_cash_value",
    "contains_runtime_cash_receipt",
    "contains_live_reachability",
    "contains_order_instruction",
    "contains_neural_training_output",
    "contains_neural_inference_output",
    "contains_external_repo_clone",
    "contains_package_install_script",
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
    "clones_external_repo",
    "installs_packages",
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


def test_atomicrows_fixture_exists_with_expected_name_and_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR11_ATOMICROWS_GENERATED_DERIVATIVE_GATE_SOURCE_REQUIRED_"
        "DISABLED_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR11_ATOMICROWS_GENERATED_DERIVATIVE_GATE_SOURCE_REQUIRED_DISABLED_"
        "FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR11_")


def test_atomicrows_fixture_validates_against_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    for field, definition in schema["properties"].items():
        if "const" in definition and field in fixture:
            assert fixture[field] == definition["const"]


def test_atomicrows_fixture_keeps_all_guardrails_disabled():
    fixture = _fixture()

    assert all(fixture[field] is False for field in GUARDRAIL_FIELDS)
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_atomicrows_fixture_has_no_live_private_or_real_source_material():
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


def test_atomicrows_fixture_is_inert_across_all_forbidden_boundaries():
    gate = _fixture()["atomicrows_generated_derivative_gate"]

    assert gate["static_contract_state"] == "STATIC_CONTRACT_ONLY_NO_RUNTIME_AUTHORITY"
    assert gate["bundle_state"] == "NO_ATOMICROWS_BUNDLE_CREATED"
    assert gate["bundle_reference"] == "SYNTHETIC_NONE_NO_ATOMICROWS_BUNDLE"
    assert gate["bundle_hash_state"] == "NO_ATOMICROWS_HASH_CREATED"
    assert gate["bundle_hash_reference"] == "SYNTHETIC_NONE_NO_ATOMICROWS_HASH"
    assert gate["sha_freeze_state"] == "NO_SHA_OR_FREEZE_AUTHORITY"
    assert gate["generated_derivative_authority_state"] == (
        "NO_GENERATED_DERIVATIVE_AUTHORITY"
    )
    assert gate["generated_derivative_runtime_artifact_state"] == (
        "NO_GENERATED_DERIVATIVE_RUNTIME_ARTIFACT"
    )
    assert gate["source_retrieval_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert gate["source_acceptance_state"] == "NOT_EXECUTED_NO_ACCEPTED_SOURCE"
    assert gate["connector_binding_state"] == "NOT_BOUND_NO_CONNECTOR_AUTHORITY"
    assert gate["private_state_state"] == "NO_PRIVATE_STATE_FETCH"
    assert gate["runtime_cash_state"] == "NO_RUNTIME_CASH_FETCH"
    assert gate["runtime_cash_receipt_state"] == "NO_RUNTIME_CASH_RECEIPT"
    assert gate["live_reachability_state"] == "NO_LIVE_REACHABILITY"
    assert gate["order_state"] == "NO_ORDER_EXECUTION"
    assert gate["neural_state"] == "NO_NEURAL_TRAINING_OR_INFERENCE"
    assert gate["external_repo_state"] == "NO_EXTERNAL_REPO_CLONE_OR_INSTALL"
    assert gate["profit_state"] == "NO_PROFIT_CLAIM"


def test_atomicrows_fixture_does_not_create_bundle_or_hash_files():
    assert CANONICAL_BUNDLE_PATH.exists()
    assert not CANONICAL_BUNDLE_SHA_PATH.exists()

