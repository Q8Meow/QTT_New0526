import json
from pathlib import Path

from tools.validate_replay_paper_execution_graph_static import (
    EXECUTION_GRAPH_FORBIDDEN_ACTION_FLAGS,
    validate_replay_paper_execution_graph_fixture,
    validate_static_surface,
)


SCHEMA_PATH = Path(
    "schemas/replay_paper_review/replay_paper_execution_graph.schema.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/replay_paper_review/"
    "synthetic_replay_paper_execution_graph.v1.fixture.json"
)
EXPECTED_FIXTURE_NAME = "synthetic_replay_paper_execution_graph.v1.fixture.json"
SYNTHETIC_AUTHORITY_CLASS = (
    "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_REPLAY_PAPER_EXECUTION_NOT_SOURCE_FACT"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _graph(fixture: dict) -> dict:
    return fixture["replay_paper_execution_graph"]


def _lane(fixture: dict, lane_id: str) -> dict:
    lanes = _graph(fixture)["lane_separation"]["lane_placeholders"]
    return next(lane for lane in lanes if lane["lane_id"] == lane_id)


def _boundary(fixture: dict, boundary_type: str) -> dict:
    boundaries = _graph(fixture)["result_packet_boundaries"]
    return next(
        boundary for boundary in boundaries if boundary["boundary_type"] == boundary_type
    )


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_replay_paper_execution_graph_static_validator_accepts_schema_and_fixture():
    failures = validate_static_surface(schema_path=SCHEMA_PATH, fixture_path=FIXTURE_PATH)

    assert failures == []


def test_valid_synthetic_replay_paper_execution_graph_fixture_passes():
    fixture = _fixture()

    assert FIXTURE_PATH.name == EXPECTED_FIXTURE_NAME
    assert fixture["fixture_id"] == "SYNTHETIC_PR23_REPLAY_PAPER_EXECUTION_GRAPH_FIXTURE"
    assert fixture["fixture_version"] == "PR23_REPLAY_PAPER_EXECUTION_GRAPH_FIXTURE_V1"
    assert fixture["fixture_authority_class"] == SYNTHETIC_AUTHORITY_CLASS
    assert validate_replay_paper_execution_graph_fixture(fixture) == []


def test_replay_paper_execution_graph_preserves_input_lock_lane_and_boundary_shape():
    fixture = _fixture()
    graph = _graph(fixture)

    assert graph["shared_input_identity"]["identity_state"] == (
        "SCAFFOLD_ONLY_NOT_RUNTIME_IDENTITY"
    )
    assert graph["shared_input_identity"][
        "replay_paper_input_identity_digest_state"
    ] == "PLACEHOLDER_ONLY_NOT_COMPUTED"
    assert graph["immutable_input_lock_contract"]["input_lock_state"] == (
        "SCAFFOLD_ONLY_NOT_LOCKED"
    )
    assert graph["lane_separation"]["lane_separation_state"] == (
        "SCAFFOLD_ONLY_SEPARATED_NON_EXECUTING"
    )
    assert _lane(fixture, "REPLAY_LANE")["lane_output_state"] == (
        "NO_REPLAY_RESULT_PACKET"
    )
    assert _lane(fixture, "PAPER_LANE")["lane_output_state"] == (
        "NO_PAPER_RESULT_PACKET"
    )
    assert _boundary(
        fixture, "REPLAY_RESULT_PACKET_BOUNDARY_PLACEHOLDER"
    )["boundary_state"] == "FUTURE_BOUNDARY_ONLY_NO_RESULT_PACKET"
    assert _boundary(
        fixture, "PAPER_RESULT_PACKET_BOUNDARY_PLACEHOLDER"
    )["boundary_state"] == "FUTURE_BOUNDARY_ONLY_NO_RESULT_PACKET"


def test_replay_paper_execution_graph_rejects_missing_required_authority_scope_flags():
    fixture = _fixture()
    _graph(fixture)["execution_graph_authority_scope_flags"].pop(
        "immutable_input_lock_required_before_lanes"
    )

    failures = validate_replay_paper_execution_graph_fixture(fixture)

    _assert_failure_contains(failures, "immutable_input_lock_required_before_lanes")


def test_runtime_live_order_profit_source_binding_and_private_state_flags_true_fail():
    forbidden_flags = {
        "runtime_enabled",
        "runtime_execution_enabled",
        "live_reachability_enabled",
        "order_execution_enabled",
        "profit_claim_enabled",
        "source_retrieval_enabled",
        "source_acceptance_execution_enabled",
        "external_fact_acceptance_enabled",
        "connector_binding_enabled",
        "private_state_fetch_enabled",
    }

    for flag in sorted(forbidden_flags):
        fixture = _fixture()
        _graph(fixture)["execution_graph_forbidden_action_flags"][flag] = True

        failures = validate_replay_paper_execution_graph_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_replay_paper_execution_graph_rejects_every_forbidden_action_flag_when_true():
    for flag in sorted(EXECUTION_GRAPH_FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        _graph(fixture)["execution_graph_forbidden_action_flags"][flag] = True

        failures = validate_replay_paper_execution_graph_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_replay_execution_claims_fail():
    fixture = _fixture()
    _graph(fixture)["execution_graph_forbidden_action_flags"][
        "replay_execution_enabled"
    ] = True
    _lane(fixture, "REPLAY_LANE")["lane_execution_allowed"] = True
    fixture["fixture_no_claim_flags"]["executes_replay"] = True

    failures = validate_replay_paper_execution_graph_fixture(fixture)

    _assert_failure_contains(failures, "replay_execution_enabled")
    _assert_failure_contains(failures, "lane_execution_allowed")
    _assert_failure_contains(failures, "executes_replay")


def test_paper_execution_claims_fail():
    fixture = _fixture()
    _graph(fixture)["execution_graph_forbidden_action_flags"][
        "paper_execution_enabled"
    ] = True
    _lane(fixture, "PAPER_LANE")["lane_execution_allowed"] = True
    fixture["fixture_no_claim_flags"]["executes_paper"] = True

    failures = validate_replay_paper_execution_graph_fixture(fixture)

    _assert_failure_contains(failures, "paper_execution_enabled")
    _assert_failure_contains(failures, "lane_execution_allowed")
    _assert_failure_contains(failures, "executes_paper")


def test_real_replay_and_paper_result_packet_claims_fail():
    fixture = _fixture()
    action_flags = _graph(fixture)["execution_graph_forbidden_action_flags"]
    action_flags["real_replay_result_packet_claimed"] = True
    action_flags["real_paper_result_packet_claimed"] = True
    action_flags["replay_result_packet_creation_enabled"] = True
    action_flags["paper_result_packet_creation_enabled"] = True
    replay_boundary = _boundary(fixture, "REPLAY_RESULT_PACKET_BOUNDARY_PLACEHOLDER")
    paper_boundary = _boundary(fixture, "PAPER_RESULT_PACKET_BOUNDARY_PLACEHOLDER")
    replay_boundary["contains_result_packet"] = True
    replay_boundary["contains_replay_output"] = True
    replay_boundary["result_packet_creation_allowed"] = True
    paper_boundary["contains_result_packet"] = True
    paper_boundary["contains_paper_output"] = True
    paper_boundary["result_packet_creation_allowed"] = True
    fixture["fixture_no_claim_flags"]["contains_replay_result_packet"] = True
    fixture["fixture_no_claim_flags"]["contains_paper_result_packet"] = True
    fixture["fixture_no_claim_flags"]["creates_replay_result"] = True
    fixture["fixture_no_claim_flags"]["creates_paper_result"] = True

    failures = validate_replay_paper_execution_graph_fixture(fixture)

    _assert_failure_contains(failures, "real_replay_result_packet_claimed")
    _assert_failure_contains(failures, "real_paper_result_packet_claimed")
    _assert_failure_contains(failures, "contains_replay_output")
    _assert_failure_contains(failures, "contains_paper_output")
    _assert_failure_contains(failures, "creates_replay_result")
    _assert_failure_contains(failures, "creates_paper_result")


def test_dual_result_review_or_live_eligibility_claims_fail():
    fixture = _fixture()
    action_flags = _graph(fixture)["execution_graph_forbidden_action_flags"]
    action_flags["dual_result_review_enabled"] = True
    action_flags["live_eligibility_creation_enabled"] = True
    lane_separation = _graph(fixture)["lane_separation"]
    lane_separation["dual_result_review_allowed"] = True
    lane_separation["live_eligibility_creation_allowed"] = True
    fixture["fixture_no_claim_flags"]["contains_dual_result_review_packet"] = True
    fixture["fixture_no_claim_flags"]["contains_live_eligibility"] = True
    fixture["fixture_no_claim_flags"]["creates_dual_result_review"] = True
    fixture["fixture_no_claim_flags"]["creates_live_eligibility"] = True

    failures = validate_replay_paper_execution_graph_fixture(fixture)

    _assert_failure_contains(failures, "dual_result_review_enabled")
    _assert_failure_contains(failures, "live_eligibility_creation_enabled")
    _assert_failure_contains(failures, "dual_result_review_allowed")
    _assert_failure_contains(failures, "contains_live_eligibility")
    _assert_failure_contains(failures, "creates_dual_result_review")


def test_runtime_resolver_snapshot_creation_claims_fail():
    fixture = _fixture()
    action_flags = _graph(fixture)["execution_graph_forbidden_action_flags"]
    action_flags["runtime_resolver_snapshot_creation_enabled"] = True
    action_flags["runtime_resolver_snapshot_materialization_enabled"] = True
    _graph(fixture)["shared_input_identity"]["contains_runtime_resolver_snapshot"] = True
    _graph(fixture)["immutable_input_lock_contract"][
        "runtime_resolver_snapshot_creation_allowed"
    ] = True
    fixture["fixture_no_claim_flags"]["contains_runtime_resolver_snapshot"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_resolver_snapshot"] = True

    failures = validate_replay_paper_execution_graph_fixture(fixture)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_enabled")
    _assert_failure_contains(failures, "runtime_resolver_snapshot_materialization_enabled")
    _assert_failure_contains(failures, "contains_runtime_resolver_snapshot")
    _assert_failure_contains(failures, "creates_runtime_resolver_snapshot")


def test_runtime_cash_receipt_claims_fail():
    fixture = _fixture()
    _graph(fixture)["execution_graph_forbidden_action_flags"][
        "runtime_cash_receipt_creation_enabled"
    ] = True
    _boundary(fixture, "REPLAY_RESULT_PACKET_BOUNDARY_PLACEHOLDER")[
        "contains_runtime_cash_receipt"
    ] = True
    fixture["fixture_no_claim_flags"]["contains_runtime_cash_receipt"] = True
    fixture["fixture_no_claim_flags"]["creates_runtime_cash_receipts"] = True

    failures = validate_replay_paper_execution_graph_fixture(fixture)

    _assert_failure_contains(failures, "runtime_cash_receipt_creation_enabled")
    _assert_failure_contains(failures, "contains_runtime_cash_receipt")
    _assert_failure_contains(failures, "creates_runtime_cash_receipts")


def test_replay_paper_execution_graph_fixture_has_no_live_private_or_real_source_material():
    raw_text = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    for fragment in {
        "://",
        "www.",
        "http",
        "kalshi",
        "polymarket",
        "ibkr",
        "password",
        "account_id",
        "atomicrows.bundle",
    }:
        assert fragment not in raw_text

    fixture = _fixture()
    graph = _graph(fixture)
    assert all(value is False for value in fixture["fixture_no_claim_flags"].values())
    assert all(value is False for value in fixture["no_claim_flags"].values())
    assert graph["shared_input_identity"]["runtime_resolver_snapshot_reference"] == (
        "SYNTHETIC_NONE_NO_RUNTIME_RESOLVER_SNAPSHOT"
    )
    assert _boundary(
        fixture, "REPLAY_RESULT_PACKET_BOUNDARY_PLACEHOLDER"
    )["result_packet_reference"] == "SYNTHETIC_NONE_NO_REPLAY_RESULT_PACKET"
    assert _boundary(
        fixture, "PAPER_RESULT_PACKET_BOUNDARY_PLACEHOLDER"
    )["result_packet_reference"] == "SYNTHETIC_NONE_NO_PAPER_RESULT_PACKET"
