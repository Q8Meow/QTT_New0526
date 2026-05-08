import json
from pathlib import Path


FIXTURE_PATH = Path(
    "tests/fixtures/replay_paper_review/"
    "synthetic_replay_paper_review_source_required_disabled.v1.fixture.json"
)
SCHEMA_PATH = Path("schemas/replay_paper_review/replay_paper_review.schema.json")
EXPECTED_FIXTURE_NAME = (
    "synthetic_replay_paper_review_source_required_disabled.v1.fixture.json"
)
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_REPLAY_PAPER_REVIEW_NOT_SOURCE_FACT"
)
GUARDRAIL_FIELDS = {
    "replay_lane_execution_allowed",
    "paper_lane_execution_allowed",
    "replay_result_creation_allowed",
    "paper_result_creation_allowed",
    "dual_result_review_creation_allowed",
    "runtime_resolver_snapshot_creation_allowed",
    "shared_input_identity_creation_allowed",
    "result_packet_merge_allowed",
    "owner_live_promotion_review_creation_allowed",
    "limited_live_canary_eligibility_allowed",
    "live_reachability_allowed",
    "connector_binding_allowed",
    "source_retrieval_allowed",
    "source_acceptance_execution_allowed",
    "private_state_fetch_allowed",
    "runtime_cash_fetch_allowed",
    "runtime_cash_receipt_creation_allowed",
    "api_key_use_allowed",
    "order_execution_allowed",
    "neural_training_allowed",
    "neural_inference_allowed",
    "external_repo_clone_allowed",
    "atomicrows_bundle_creation_allowed",
    "sha_freeze_authority_allowed",
    "blocker_reduction_allowed",
    "profit_claim_allowed",
}
REQUIRED_BEFORE_ENABLE_MARKERS = {
    "runtime_resolver_snapshot_required_before_replay_paper",
    "shared_input_identity_required_before_lanes",
    "separate_replay_and_paper_results_required_before_review",
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
    "owner_uploaded_private_doc_locator",
    "-----begin",
}
FORBIDDEN_AUTHORITY_FIELDS = {
    "contains_real_runtime_resolver_snapshot",
    "contains_shared_input_identity",
    "contains_replay_result_packet",
    "contains_paper_result_packet",
    "contains_dual_result_review_packet",
    "contains_result_merge",
    "contains_owner_approval",
    "contains_live_canary_eligibility",
    "contains_live_reachability",
    "contains_real_venue_identifier",
    "contains_real_market_identifier",
    "contains_real_connector_identifier",
    "contains_credentials",
    "contains_real_url",
    "contains_accepted_source_payload",
    "contains_private_state",
    "contains_runtime_cash_value",
    "contains_runtime_cash_receipt",
    "contains_order_instruction",
    "contains_neural_training_output",
    "contains_neural_inference_output",
    "contains_external_repo_clone",
    "contains_atomicrows_bundle",
    "contains_sha_freeze_authority",
    "executes_replay",
    "executes_paper",
    "creates_replay_result",
    "creates_paper_result",
    "creates_dual_result_review",
    "creates_owner_live_promotion_review",
    "creates_limited_live_canary_eligibility",
    "creates_live_reachability",
    "binds_connector",
    "retrieves_source_facts",
    "accepts_source_facts",
    "fetches_private_state",
    "fetches_runtime_cash",
    "creates_runtime_cash_receipts",
    "executes_orders",
    "trains_neural_model",
    "runs_neural_inference",
    "clones_external_repo",
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


def test_replay_paper_review_fixture_exists_with_expected_name_and_identity():
    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME

    fixture = _fixture()
    assert fixture["fixture_id"] == (
        "SYNTHETIC_PR10_REPLAY_PAPER_REVIEW_SOURCE_REQUIRED_DISABLED_FIXTURE"
    )
    assert fixture["fixture_version"] == (
        "PR10_REPLAY_PAPER_REVIEW_SOURCE_REQUIRED_DISABLED_FIXTURE_V1"
    )
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert fixture["fixture_id"].startswith("SYNTHETIC_PR10_")


def test_replay_paper_review_fixture_validates_against_disabled_schema_surface():
    fixture = _fixture()
    schema = _schema()

    for field in schema["required"]:
        assert field in fixture

    for field, definition in schema["properties"].items():
        if "const" in definition and field in fixture:
            assert fixture[field] == definition["const"]


def test_replay_paper_review_fixture_keeps_all_guardrails_disabled():
    fixture = _fixture()

    assert all(fixture[field] is False for field in GUARDRAIL_FIELDS)
    assert all(fixture[field] is True for field in REQUIRED_BEFORE_ENABLE_MARKERS)
    assert set(fixture["fixture_no_claim_flags"]) == FORBIDDEN_AUTHORITY_FIELDS
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())


def test_replay_paper_review_fixture_has_no_live_private_or_real_source_material():
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


def test_replay_paper_review_fixture_is_inert_across_all_boundaries():
    surface = _fixture()["replay_paper_review"]

    assert surface["runtime_resolver_snapshot_state"] == "MISSING_NO_SNAPSHOT_CREATED"
    assert surface["shared_input_identity_state"] == "MISSING_NO_SHARED_INPUT_IDENTITY"
    assert surface["replay_lane_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert surface["paper_lane_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert surface["replay_result_state"] == "NO_REPLAY_RESULT_PACKET"
    assert surface["paper_result_state"] == "NO_PAPER_RESULT_PACKET"
    assert surface["dual_result_review_state"] == "NOT_CREATED_NO_REVIEW_AUTHORITY"
    assert surface["result_merge_state"] == "DISALLOWED_NO_COMBINED_RESULT"
    assert surface["owner_live_promotion_review_state"] == (
        "NOT_CREATED_NO_OWNER_APPROVAL"
    )
    assert surface["limited_live_canary_state"] == "NO_LIVE_CANARY_ELIGIBILITY"
    assert surface["live_reachability_state"] == "NO_LIVE_REACHABILITY"
    assert surface["source_retrieval_state"] == "NOT_EXECUTED_SOURCE_REQUIRED"
    assert surface["source_acceptance_state"] == "NOT_EXECUTED_NO_ACCEPTED_SOURCE"
    assert surface["connector_binding_state"] == "NOT_BOUND_NO_CONNECTOR_AUTHORITY"
    assert surface["private_state_state"] == "NO_PRIVATE_STATE_FETCH"
    assert surface["runtime_cash_state"] == "NO_RUNTIME_CASH_FETCH"
    assert surface["runtime_cash_receipt_state"] == "NO_RUNTIME_CASH_RECEIPT"
    assert surface["order_state"] == "NO_ORDER_EXECUTION"
    assert surface["neural_state"] == "NO_NEURAL_TRAINING_OR_INFERENCE"
    assert surface["atomicrows_state"] == "NO_ATOMICROWS_BUNDLE_OR_HASH"
    assert surface["sha_freeze_state"] == "NO_SHA_OR_FREEZE_AUTHORITY"
    assert surface["profit_state"] == "NO_PROFIT_CLAIM"
