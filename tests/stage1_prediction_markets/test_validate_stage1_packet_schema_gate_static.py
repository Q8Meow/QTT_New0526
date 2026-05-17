import copy
import json
import shutil
from pathlib import Path

import pytest

from tools.validate_stage1_packet_schema_gate_static import (
    CANONICAL_BUNDLE_RELATIVE_PATH,
    CANONICAL_BUNDLE_SHA_RELATIVE_PATH,
    EXPECTED_PACKET_FAMILIES,
    FORBIDDEN_ACTION_FLAGS,
    NO_CLAIM_FLAGS,
    validate_stage1_packet_schema_gate_fixture,
    validate_static_surface,
)


SCHEMA_DIR = Path("schemas/stage1_prediction_markets")
FIXTURE_PATH = Path(
    "tests/fixtures/stage1_prediction_markets/"
    "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json"
)


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def _validate_fixture(fixture: dict, repo_root: Path = Path(".")) -> list[str]:
    return validate_stage1_packet_schema_gate_fixture(
        fixture,
        repo_root=repo_root,
        schema_dir=SCHEMA_DIR,
    )


def _canonical_bundle_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_RELATIVE_PATH.parts)


def _canonical_bundle_sha_path(root: Path) -> Path:
    return root / Path(*CANONICAL_BUNDLE_SHA_RELATIVE_PATH.parts)


def test_valid_schema_only_blocked_fixture_passes():
    assert (
        validate_static_surface(
            repo_root=Path("."),
            schema_dir=SCHEMA_DIR,
            fixture_path=FIXTURE_PATH,
        )
        == []
    )

    fixture = _fixture()
    assert fixture["expected_schema_families"] == EXPECTED_PACKET_FAMILIES
    assert fixture["authority_scope_flags"]["static_schema_gate_only"] is True
    assert fixture["source_dependency_policy"]["connector_source_dependent_fields_value"] == (
        "SOURCE_REQUIRED_PLACEHOLDER"
    )
    assert fixture["lane_separation_policy"]["replay_paper_merge_allowed"] is False


def test_missing_schema_only_authority_fails():
    fixture = _fixture()
    fixture["authority_scope_flags"].pop("static_schema_gate_only")

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "static_schema_gate_only")


def test_missing_generated_derivative_gate_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_gate_receipts"][
        "generated_derivative_gate_receipt_required"
    ] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "generated_derivative_gate_receipt_required")


def test_missing_source_evidence_gate_confirmation_receipt_requirement_fails():
    fixture = _fixture()
    fixture["prerequisite_gate_receipts"][
        "source_evidence_gate_confirmation_receipt_required"
    ] = False

    failures = _validate_fixture(fixture)

    _assert_failure_contains(
        failures,
        "source_evidence_gate_confirmation_receipt_required",
    )


def test_parameter_revitalization_gate_must_remain_required_or_blocked_pending():
    fixture = _fixture()
    fixture["prerequisite_gate_receipts"]["parameter_revitalization_gate_status"] = (
        "SATISFIED"
    )
    fixture["prerequisite_gate_receipts"]["parameter_revitalization_gate_satisfied"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "parameter_revitalization_gate_status")
    _assert_failure_contains(failures, "parameter_revitalization_gate_satisfied")


def test_connector_source_dependent_fields_must_remain_placeholder():
    fixture = _fixture()
    fixture["source_dependency_policy"]["connector_source_dependent_fields_value"] = (
        "BOUND_VALUE"
    )

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "SOURCE_REQUIRED_PLACEHOLDER")


@pytest.mark.parametrize(
    "flag",
    [
        "selects_exact_markets",
        "selects_exact_contracts",
        "selects_exact_events",
        "selects_exact_venues",
        "selects_live_venues",
    ],
)
def test_exact_market_contract_event_or_venue_selection_claim_fails(flag):
    fixture = _fixture()
    fixture["no_claim_flags"][flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, flag)


def test_source_acceptance_claim_fails():
    fixture = _fixture()
    fixture["source_dependency_policy"]["source_fact_acceptance_claimed"] = True
    fixture["forbidden_action_flags"]["source_fact_acceptance_enabled"] = True
    fixture["no_claim_flags"]["claims_source_fact_acceptance"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "source_fact_acceptance_claimed")
    _assert_failure_contains(failures, "source_fact_acceptance_enabled")
    _assert_failure_contains(failures, "claims_source_fact_acceptance")


def test_accepted_source_packet_creation_claim_fails():
    fixture = _fixture()
    fixture["source_dependency_policy"]["accepted_source_packets_created"] = True
    fixture["forbidden_action_flags"]["accepted_source_packet_creation_enabled"] = True
    fixture["no_claim_flags"]["creates_accepted_source_packets"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "accepted_source_packets_created")
    _assert_failure_contains(failures, "accepted_source_packet_creation_enabled")
    _assert_failure_contains(failures, "creates_accepted_source_packets")


def test_connector_binding_claim_fails():
    fixture = _fixture()
    fixture["source_dependency_policy"]["connector_binding_claimed"] = True
    fixture["forbidden_action_flags"]["connector_binding_enabled"] = True
    fixture["no_claim_flags"]["binds_connector_semantics"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "connector_binding_claimed")
    _assert_failure_contains(failures, "connector_binding_enabled")
    _assert_failure_contains(failures, "binds_connector_semantics")


def test_runtime_resolver_snapshot_creation_claim_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"][
        "runtime_resolver_snapshot_creation_enabled"
    ] = True
    fixture["no_claim_flags"]["creates_runtime_resolver_snapshots"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_resolver_snapshot_creation_enabled")
    _assert_failure_contains(failures, "creates_runtime_resolver_snapshots")


def test_replay_execution_claim_fails():
    fixture = _fixture()
    fixture["lane_separation_policy"]["replay_execution_claimed"] = True
    fixture["forbidden_action_flags"]["replay_execution_enabled"] = True
    fixture["no_claim_flags"]["executes_replay"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "replay_execution_claimed")
    _assert_failure_contains(failures, "replay_execution_enabled")
    _assert_failure_contains(failures, "executes_replay")


def test_paper_execution_claim_fails():
    fixture = _fixture()
    fixture["lane_separation_policy"]["paper_execution_claimed"] = True
    fixture["forbidden_action_flags"]["paper_execution_enabled"] = True
    fixture["no_claim_flags"]["executes_paper"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "paper_execution_claimed")
    _assert_failure_contains(failures, "paper_execution_enabled")
    _assert_failure_contains(failures, "executes_paper")


def test_runtime_replay_or_paper_result_packet_creation_claim_fails():
    fixture = _fixture()
    fixture["lane_separation_policy"]["runtime_replay_result_packet_created"] = True
    fixture["lane_separation_policy"]["runtime_paper_result_packet_created"] = True
    fixture["forbidden_action_flags"][
        "runtime_replay_result_packet_creation_enabled"
    ] = True
    fixture["forbidden_action_flags"]["runtime_paper_result_packet_creation_enabled"] = (
        True
    )

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "runtime_replay_result_packet_created")
    _assert_failure_contains(failures, "runtime_paper_result_packet_created")
    _assert_failure_contains(failures, "runtime_replay_result_packet_creation_enabled")
    _assert_failure_contains(failures, "runtime_paper_result_packet_creation_enabled")


def test_replay_paper_merge_permission_fails():
    fixture = _fixture()
    fixture["lane_separation_policy"]["replay_paper_merge_allowed"] = True
    fixture["forbidden_action_flags"]["replay_paper_merge_enabled"] = True
    fixture["no_claim_flags"]["merges_replay_and_paper_results"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "replay_paper_merge_allowed")
    _assert_failure_contains(failures, "replay_paper_merge_enabled")
    _assert_failure_contains(failures, "merges_replay_and_paper_results")


def test_dual_result_overwrite_permission_fails():
    fixture = _fixture()
    fixture["lane_separation_policy"]["dual_result_review_may_overwrite_replay"] = True
    fixture["lane_separation_policy"]["dual_result_review_may_overwrite_paper"] = True
    fixture["forbidden_action_flags"]["dual_result_review_overwrite_enabled"] = True
    fixture["no_claim_flags"]["allows_dual_result_overwrite"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "dual_result_review_may_overwrite_replay")
    _assert_failure_contains(failures, "dual_result_review_may_overwrite_paper")
    _assert_failure_contains(failures, "dual_result_review_overwrite_enabled")
    _assert_failure_contains(failures, "allows_dual_result_overwrite")


def test_shadow_mandatory_before_canary_claim_fails():
    fixture = _fixture()
    fixture["live_transition_policy"]["shadow_mandatory_before_canary"] = True
    fixture["forbidden_action_flags"]["shadow_mandatory_before_canary_enabled"] = True
    fixture["no_claim_flags"]["makes_shadow_mandatory_before_canary"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "shadow_mandatory_before_canary")
    _assert_failure_contains(failures, "shadow_mandatory_before_canary_enabled")
    _assert_failure_contains(failures, "makes_shadow_mandatory_before_canary")


@pytest.mark.parametrize(
    "field,claim_flag,forbidden_flag",
    [
        (
            "canary_risk_caps_required",
            "omits_canary_risk_caps",
            "limited_live_canary_without_risk_caps_enabled",
        ),
        (
            "canary_owner_review_required",
            "omits_canary_owner_review",
            "limited_live_canary_without_owner_review_enabled",
        ),
        (
            "canary_fail_closed_receipts_required",
            "omits_canary_fail_closed_receipts",
            "limited_live_canary_without_fail_closed_receipts_enabled",
        ),
    ],
)
def test_missing_canary_risk_caps_owner_review_or_fail_closed_receipts_fails(
    field,
    claim_flag,
    forbidden_flag,
):
    fixture = _fixture()
    fixture["live_transition_policy"][field] = False
    fixture["no_claim_flags"][claim_flag] = True
    fixture["forbidden_action_flags"][forbidden_flag] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, field)
    _assert_failure_contains(failures, claim_flag)
    _assert_failure_contains(failures, forbidden_flag)


def test_real_runtime_cash_receipt_claim_fails():
    fixture = _fixture()
    fixture["capital_cash_policy"]["real_runtime_cash_receipt_created"] = True
    fixture["forbidden_action_flags"]["real_runtime_cash_receipt_creation_enabled"] = (
        True
    )
    fixture["no_claim_flags"]["creates_real_runtime_cash_receipts"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "real_runtime_cash_receipt_created")
    _assert_failure_contains(failures, "real_runtime_cash_receipt_creation_enabled")
    _assert_failure_contains(failures, "creates_real_runtime_cash_receipts")


def test_live_reachability_claim_fails():
    fixture = _fixture()
    fixture["live_transition_policy"]["live_reachability_claimed"] = True
    fixture["forbidden_action_flags"]["live_reachability_enabled"] = True
    fixture["no_claim_flags"]["creates_live_reachability"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "live_reachability_claimed")
    _assert_failure_contains(failures, "live_reachability_enabled")
    _assert_failure_contains(failures, "creates_live_reachability")


def test_order_authority_claim_fails():
    fixture = _fixture()
    fixture["live_transition_policy"]["order_authority_claimed"] = True
    fixture["forbidden_action_flags"]["order_execution_authority_enabled"] = True
    fixture["no_claim_flags"]["creates_order_authority"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "order_authority_claimed")
    _assert_failure_contains(failures, "order_execution_authority_enabled")
    _assert_failure_contains(failures, "creates_order_authority")


def test_private_state_balance_or_account_fetch_claim_fails():
    fixture = _fixture()
    fixture["capital_cash_policy"]["private_state_fetch_claimed"] = True
    fixture["capital_cash_policy"]["balance_fetch_claimed"] = True
    fixture["capital_cash_policy"]["account_state_fetch_claimed"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "private_state_fetch_claimed")
    _assert_failure_contains(failures, "balance_fetch_claimed")
    _assert_failure_contains(failures, "account_state_fetch_claimed")


def test_blocker_reduction_claim_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["blocker_reduction_enabled"] = True
    fixture["no_claim_flags"]["claims_blocker_reduction"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "blocker_reduction_enabled")
    _assert_failure_contains(failures, "claims_blocker_reduction")


def test_profit_evidence_or_claim_fails():
    fixture = _fixture()
    fixture["forbidden_action_flags"]["profit_evidence_creation_enabled"] = True
    fixture["forbidden_action_flags"]["profit_claim_enabled"] = True
    fixture["no_claim_flags"]["creates_profit_evidence"] = True
    fixture["no_claim_flags"]["creates_profit_claim"] = True

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "profit_evidence_creation_enabled")
    _assert_failure_contains(failures, "profit_claim_enabled")
    _assert_failure_contains(failures, "creates_profit_evidence")
    _assert_failure_contains(failures, "creates_profit_claim")


def test_atomicrows_bundle_hash_sha_row_or_completion_authority_claim_fails():
    fixture = _fixture()
    fixture["atomicrows_authority_state"]["atomicrows_bundle_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_hash_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_sha_authority_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_row_creation_claimed"] = True
    fixture["atomicrows_authority_state"]["atomicrows_completion_claimed"] = True
    fixture["atomicrows_authority_state"]["claims_4183_row_completion"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_bundle_hash_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_sha_computation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_sha_authority_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_row_creation_enabled"] = True
    fixture["forbidden_action_flags"]["atomicrows_completion_claim_enabled"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle"] = True
    fixture["no_claim_flags"]["contains_atomicrows_bundle_hash"] = True
    fixture["no_claim_flags"]["computes_atomicrows_sha"] = True
    fixture["no_claim_flags"]["claims_atomicrows_sha_authority"] = True
    fixture["no_claim_flags"]["creates_atomicrows_rows"] = True
    fixture["no_claim_flags"]["creates_atomicrows_row_records"] = True
    fixture["no_claim_flags"]["claims_atomicrows_completion"] = True
    fixture["no_claim_flags"]["claims_4183_row_completion"] = True

    failures = _validate_fixture(fixture)

    for fragment in [
        "atomicrows_bundle_creation_claimed",
        "atomicrows_hash_creation_claimed",
        "atomicrows_sha_authority_claimed",
        "atomicrows_row_creation_claimed",
        "atomicrows_completion_claimed",
        "claims_4183_row_completion",
        "contains_atomicrows_bundle",
        "claims_atomicrows_sha_authority",
    ]:
        _assert_failure_contains(failures, fragment)


def test_actual_atomicrows_bundle_existing_at_canonical_path_fails(tmp_path):
    bundle_path = _canonical_bundle_path(tmp_path)
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text("", encoding="utf-8")

    failures = validate_static_surface(
        repo_root=tmp_path,
        schema_dir=SCHEMA_DIR,
        fixture_path=FIXTURE_PATH,
    )

    _assert_failure_contains(failures, "canonical AtomicRows bundle must remain absent")


def test_actual_atomicrows_sha_existing_at_canonical_path_fails(tmp_path):
    sha_path = _canonical_bundle_sha_path(tmp_path)
    sha_path.parent.mkdir(parents=True)
    sha_path.write_text("UNAUTHORIZED_TEST_HASH_PLACEHOLDER", encoding="utf-8")

    failures = validate_static_surface(
        repo_root=tmp_path,
        schema_dir=SCHEMA_DIR,
        fixture_path=FIXTURE_PATH,
    )

    _assert_failure_contains(
        failures,
        "canonical AtomicRows bundle hash must remain absent",
    )


def test_stage1_canary_schema_missing_risk_caps_owner_review_or_receipts_fails(
    tmp_path,
):
    schema_dir = tmp_path / "stage1_prediction_markets"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    canary_schema_path = schema_dir / "stage1_limited_live_canary_result_packet.schema.json"
    canary_schema = json.loads(canary_schema_path.read_text(encoding="utf-8"))
    canary_schema["properties"].pop("risk_caps_required")
    canary_schema["required"].remove("risk_caps_required")
    canary_schema["properties"].pop("owner_review_required")
    canary_schema["required"].remove("owner_review_required")
    canary_schema["properties"].pop("fail_closed_receipts_required")
    canary_schema["required"].remove("fail_closed_receipts_required")
    canary_schema_path.write_text(json.dumps(canary_schema), encoding="utf-8")

    failures = validate_static_surface(
        repo_root=Path("."),
        schema_dir=schema_dir,
        fixture_path=FIXTURE_PATH,
    )

    _assert_failure_contains(failures, "risk_caps_required")
    _assert_failure_contains(failures, "owner_review_required")
    _assert_failure_contains(failures, "fail_closed_receipts_required")


def test_schema_authority_change_to_runtime_claim_fails(tmp_path):
    schema_dir = tmp_path / "stage1_prediction_markets"
    shutil.copytree(SCHEMA_DIR, schema_dir)
    schema_path = schema_dir / "stage1_connector_fact_packet.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["properties"]["schema_authority_class"]["const"] = (
        "RUNTIME_PACKET_AUTHORITY"
    )
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    failures = validate_static_surface(
        repo_root=Path("."),
        schema_dir=schema_dir,
        fixture_path=FIXTURE_PATH,
    )

    _assert_failure_contains(failures, "schema_authority_class")


def test_every_forbidden_action_flag_fails_when_true():
    for flag in sorted(FORBIDDEN_ACTION_FLAGS):
        fixture = _fixture()
        fixture["forbidden_action_flags"][flag] = True

        failures = _validate_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_every_no_claim_flag_fails_when_true():
    for flag in sorted(NO_CLAIM_FLAGS):
        fixture = _fixture()
        fixture["no_claim_flags"][flag] = True

        failures = _validate_fixture(fixture)

        _assert_failure_contains(failures, flag)


def test_fixture_rejects_atomicrows_row_records():
    fixture = _fixture()
    fixture["row_records"] = [{"atomic_parameter_row_id": "atomic_parameter_row_0001"}]

    failures = _validate_fixture(fixture)

    _assert_failure_contains(failures, "row_records")


def test_validator_does_not_mutate_fixture_or_create_atomicrows_files(tmp_path):
    fixture = _fixture()
    frozen = copy.deepcopy(fixture)
    bundle_path = _canonical_bundle_path(tmp_path)
    sha_path = _canonical_bundle_sha_path(tmp_path)
    contract_path = (
        tmp_path
        / "docs"
        / "master_plan"
        / "atomicrows"
        / "AtomicRowsBundleBoundaryStateContract.yaml"
    )
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        "current_expected_state: POST_MATERIALIZATION_PRE_SHA\n",
        encoding="utf-8",
    )
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text("{}\n", encoding="utf-8")

    assert (
        validate_stage1_packet_schema_gate_fixture(
            fixture,
            repo_root=tmp_path,
            schema_dir=SCHEMA_DIR,
        )
        == []
    )

    assert fixture == frozen
    assert bundle_path.exists()
    assert not sha_path.exists()


def test_canonical_atomicrows_bundle_exists_and_hash_is_absent_in_repo():
    assert _canonical_bundle_path(Path(".")).exists()
    assert not _canonical_bundle_sha_path(Path(".")).exists()
