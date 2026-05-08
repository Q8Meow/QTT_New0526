import json
from pathlib import Path


SCHEMA_PATH = Path("schemas/replay_paper_review/replay_paper_review.schema.json")
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


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_replay_paper_review_schema_is_source_required_and_disabled():
    schema = _schema()
    properties = schema["properties"]

    assert properties["mode"]["const"] == "SOURCE_REQUIRED"
    assert properties["execution"]["const"] == "DISABLED"
    assert properties["schema_authority_class"]["const"] == (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_REPLAY_PAPER_REVIEW_AUTHORITY"
    )
    assert properties["surface_kind"]["const"] == "REPLAY_PAPER_REVIEW_SOURCE_REQUIRED"
    assert schema["additionalProperties"] is True


def test_replay_paper_review_schema_requires_disabled_guardrails():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert GUARDRAIL_FIELDS.issubset(required)
    assert all(properties[field]["const"] is False for field in GUARDRAIL_FIELDS)


def test_replay_paper_review_schema_requires_prior_gates_before_enable():
    schema = _schema()
    properties = schema["properties"]
    required = set(schema["required"])

    assert REQUIRED_BEFORE_ENABLE_MARKERS.issubset(required)
    assert all(
        properties[field]["const"] is True
        for field in REQUIRED_BEFORE_ENABLE_MARKERS
    )


def test_replay_paper_review_schema_does_not_define_runtime_authority():
    schema = _schema()
    properties = schema["properties"]

    assert "replay_runtime_authority" not in properties
    assert "paper_runtime_authority" not in properties
    assert "dual_result_review_authority" not in properties
    assert "live_reachability_authority" not in properties
    assert "order_execution_authority" not in properties
    assert "sha_freeze_authority" not in properties
    assert "profit_authority" not in properties
