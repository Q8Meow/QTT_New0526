from __future__ import annotations

import copy
from pathlib import Path

from src.qtt.stage1_prediction_markets.replay_paper import (
    historical_dataset_digest_and_loader as hd,
)
from src.qtt.stage1_prediction_markets.replay_paper import historical_dataset_policy as policy
from tools import validate_historical_dataset_policy_literal_drift as drift


REPO_ROOT = Path(__file__).resolve().parents[2]


def _fixture() -> dict:
    return hd.load_json(REPO_ROOT / hd.FIXTURE_PATH)


def _report(name: str) -> dict:
    return hd.load_json(REPO_ROOT / hd.REPORT_DIR / name)


def _first_digest() -> dict:
    return copy.deepcopy(_fixture()["artifacts"]["historical_dataset_digests"][0])


def _codes(failures) -> set[str]:
    return {failure.code for failure in failures}


def test_pr135_happy_path_emits_marker():
    failures = hd.validate_all(REPO_ROOT)
    assert failures == []
    assert hd.marker_for_failures(failures) == policy.VALIDATOR_MARKER


def test_owner_verified_inputs_required():
    receipt = _report("PR135OwnerVerifiedInputs.report.json")
    receipt["repo_pr_state"] = "OPEN"
    assert policy.BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT in _codes(
        hd.validate_owner_verified_inputs(receipt)
    )


def test_owner_verified_placeholders_block():
    receipt = _report("PR135OwnerVerifiedInputs.report.json")
    receipt["url"] = "OWNER_VERIFIED_VALUE_REQUIRED"
    assert policy.BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT in _codes(
        hd.validate_owner_verified_inputs(receipt)
    )


def test_read_receipt_required_files_present():
    receipt = _report("PR135HistoricalDatasetDigestAndLoaderReadReceipt.report.json")
    assert receipt["required_files_read"] == list(policy.REQUIRED_READ_FILES)
    assert receipt["missing_files"] == []
    assert receipt["read_before_editing_confirmed"] is True


def test_roadmap_blueprint_extraction_maps_roadmap_pr117():
    report = _report("PR135RoadmapBlueprintExtraction.report.json")
    assert report["roadmap_pr_number"] == policy.PRODUCER_ROADMAP_PR
    assert report["roadmap_pr117_found"] is True
    assert report["roadmap_pr135_explicitly_not_used"] is True


def test_route_triage_maps_repo_pr135_to_roadmap_pr117_only():
    report = _report("PR135RouteTriage.report.json")
    assert report["repo_pr_number"] == policy.PRODUCER_REPO_PR
    assert report["roadmap_pr_number"] == policy.PRODUCER_ROADMAP_PR
    assert report["explicit_non_scope_roadmap_pr135"] is True


def test_same_number_inference_is_forbidden():
    report = _report("PR135RouteTriage.report.json")
    report["same_number_inference_used"] = True
    report["roadmap_pr_number"] = policy.PRODUCER_REPO_PR
    assert policy.BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE in _codes(
        hd.validate_route_triage(report)
    )


def test_pr134_currentization_required():
    report = _report("PR135RouteTriage.report.json")
    report["currentization_first_subtask_completed"] = False
    assert policy.BLOCKED_MISSING_PR134_CURRENTIZATION in _codes(
        hd.validate_route_triage(report)
    )


def test_policy_manifest_exists():
    manifest = _report("PR135HistoricalDatasetPolicyManifest.report.json")
    assert manifest["validator_marker"] == policy.VALIDATOR_MARKER
    assert manifest["policy_module_path"] == policy.POLICY_MODULE_PATH


def test_policy_schema_defs_match_policy_module():
    defs = hd.load_json(REPO_ROOT / policy.POLICY_SCHEMA_DEFS_PATH)["$defs"]
    assert defs["canonical_venue_id"]["enum"] == list(policy.CANONICAL_VENUE_IDS)
    assert defs["validator_marker"]["const"] == policy.VALIDATOR_MARKER


def test_policy_literal_drift_blocks(tmp_path):
    drift_file = tmp_path / "drift_fixture.py"
    drift_file.write_text(
        "DUPLICATED = "
        + repr([policy.INPUT_LOCK_STATES[0], policy.INPUT_LOCK_STATES[1]])
        + "\n",
        encoding="utf-8",
    )
    failures = drift.validate_policy_literal_drift(
        repo_root=REPO_ROOT,
        extra_paths=(drift_file,),
        write_report=False,
    )
    assert failures


def test_no_scattered_block_code_definitions():
    assert drift.validate_policy_literal_drift(repo_root=REPO_ROOT, write_report=False) == []


def test_market_index_uses_policy_refs_not_block_code_definitions():
    report = _report("PR135MarketSpecificSectionIndex.report.json")
    for row in report["market_scopes"]:
        assert row["policy_manifest_ref"] == policy.POLICY_MANIFEST_PATH
        assert "block_code_definitions" not in row


def test_crosswalk_uses_policy_refs_not_block_code_definitions():
    report = _report("PR135MasterPlanSectionCrosswalk.report.json")
    assert all("policy_block_code_refs" in row for row in report["rows"])
    assert all("block_code_definitions" not in row for row in report["rows"])


def test_command_matrix_uses_policy_refs_not_block_code_definitions():
    report = _report("PR135CommandActionMatrix.report.json")
    assert all("policy_block_code_refs" in row for row in report["actions"])
    assert all("block_code_definitions" not in row for row in report["actions"])


def test_missing_runtime_resolver_handoff_blocks():
    record = _first_digest()
    record["runtime_resolver_snapshot_handoff_ref"] = ""
    assert policy.BLOCKED_MISSING_RUNTIME_RESOLVER_HANDOFF in _codes(
        hd.validate_dataset_records([record])
    )


def test_missing_candidate_set_snapshot_lock_blocks():
    record = _first_digest()
    record["versioned_candidate_set_snapshot_lock_ref"] = ""
    assert policy.BLOCKED_MISSING_CANDIDATE_SET_SNAPSHOT_LOCK in _codes(
        hd.validate_dataset_records([record])
    )


def test_missing_replay_paper_input_identity_blocks():
    record = _first_digest()
    record["replay_paper_input_identity_ref"] = ""
    assert policy.BLOCKED_MISSING_REPLAY_PAPER_INPUT_IDENTITY in _codes(
        hd.validate_dataset_records([record])
    )


def test_missing_source_lineage_blocks():
    record = _first_digest()
    record["source_lineage_ref"] = ""
    assert policy.BLOCKED_MISSING_SOURCE_LINEAGE in _codes(
        hd.validate_dataset_records([record])
    )


def test_dataset_digest_is_deterministic():
    assert hd.build_fixture() == hd.build_fixture()


def test_dataset_digest_changes_when_fixture_content_changes():
    payload = hd.build_artifacts()["canonical_fixture_payloads"][0]
    changed = copy.deepcopy(payload)
    changed["synthetic_rows"][0]["value_basis"] = "CHANGED_SYNTHETIC_FIXTURE_VALUE"
    assert hd.sha256_hex(payload) != hd.sha256_hex(changed)


def test_digest_excludes_run_timestamp_noise():
    payload = hd.build_artifacts()["canonical_fixture_payloads"][0]
    changed = copy.deepcopy(payload)
    changed["run_timestamp_utc"] = "2099-01-01T00:00:00Z"
    assert hd.sha256_hex(payload) == hd.sha256_hex(changed)


def test_duplicate_dataset_ids_block():
    record_a = _first_digest()
    record_b = _first_digest()
    assert policy.BLOCKED_DUPLICATE_DATASET_DIGEST_ID in _codes(
        hd.validate_dataset_records([record_a, record_b])
    )


def test_mutable_dataset_blocks():
    record = _first_digest()
    record["immutable_after_creation_flag"] = False
    assert policy.BLOCKED_MUTABLE_DATASET in _codes(hd.validate_dataset_records([record]))


def test_live_data_attempt_blocks():
    record = _first_digest()
    record["live_data_used_flag"] = True
    assert policy.BLOCKED_LIVE_DATA_ATTEMPT in _codes(hd.validate_dataset_records([record]))


def test_source_retrieval_attempt_blocks():
    record = _first_digest()
    record["source_retrieval_created_flag"] = True
    assert policy.BLOCKED_SOURCE_RETRIEVAL_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_source_acceptance_attempt_blocks():
    record = _first_digest()
    record["source_acceptance_created_flag"] = True
    assert policy.BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_connector_binding_attempt_blocks():
    record = _first_digest()
    record["connector_binding_created_flag"] = True
    assert policy.BLOCKED_CONNECTOR_BINDING_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_credential_resolution_attempt_blocks():
    record = _first_digest()
    record["credential_resolution_created_flag"] = True
    assert policy.BLOCKED_CREDENTIAL_RESOLUTION_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_private_state_fetch_attempt_blocks():
    record = _first_digest()
    record["private_state_fetch_created_flag"] = True
    assert policy.BLOCKED_PRIVATE_STATE_FETCH_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_runtime_cash_authority_attempt_blocks():
    record = _first_digest()
    record["runtime_cash_authority_created_flag"] = True
    assert policy.BLOCKED_RUNTIME_CASH_AUTHORITY_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_replay_execution_attempt_blocks():
    record = _first_digest()
    record["replay_execution_created_flag"] = True
    assert policy.BLOCKED_REPLAY_EXECUTION_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_paper_execution_attempt_blocks():
    record = _first_digest()
    record["paper_execution_created_flag"] = True
    assert policy.BLOCKED_PAPER_EXECUTION_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_replay_result_attempt_blocks():
    record = _first_digest()
    record["replay_result_created_flag"] = True
    assert policy.BLOCKED_REPLAY_RESULT_ATTEMPT in _codes(hd.validate_dataset_records([record]))


def test_paper_result_attempt_blocks():
    record = _first_digest()
    record["paper_result_created_flag"] = True
    assert policy.BLOCKED_PAPER_RESULT_ATTEMPT in _codes(hd.validate_dataset_records([record]))


def test_feature_signal_ranking_attempt_blocks():
    record = _first_digest()
    record["feature_vector_created_flag"] = True
    record["trading_signal_created_flag"] = True
    record["ranking_scoring_arbitration_created_flag"] = True
    codes = _codes(hd.validate_dataset_records([record]))
    assert policy.BLOCKED_FEATURE_VECTOR_ATTEMPT in codes
    assert policy.BLOCKED_TRADING_SIGNAL_ATTEMPT in codes
    assert policy.BLOCKED_RANKING_SCORING_ARBITRATION_ATTEMPT in codes


def test_order_authority_attempt_blocks():
    record = _first_digest()
    record["order_authority_created_flag"] = True
    assert policy.BLOCKED_ORDER_AUTHORITY_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_profit_evidence_attempt_blocks():
    record = _first_digest()
    record["profit_evidence_created_flag"] = True
    assert policy.BLOCKED_PROFIT_EVIDENCE_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_latency_or_execution_superiority_claim_blocks():
    record = _first_digest()
    record["latency_superiority_evidence_created_flag"] = True
    assert policy.BLOCKED_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM in _codes(
        hd.validate_dataset_records([record])
    )


def test_quantum_execution_attempt_blocks():
    record = _first_digest()
    record["quantum_execution_created_flag"] = True
    assert policy.BLOCKED_QUANTUM_EXECUTION_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_quantum_optimizer_input_attempt_blocks():
    record = _first_digest()
    record["quantum_optimizer_input_created_flag"] = True
    assert policy.BLOCKED_QUANTUM_OPTIMIZER_INPUT_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_quantum_advantage_claim_blocks():
    record = _first_digest()
    record["quantum_advantage_claim_created_flag"] = True
    assert policy.BLOCKED_QUANTUM_ADVANTAGE_CLAIM_ATTEMPT in _codes(
        hd.validate_dataset_records([record])
    )


def test_quantum_metadata_is_metadata_only():
    for record in _fixture()["artifacts"]["historical_dataset_quantum_metadata"]:
        assert record["no_quantum_optimizer_input_flag"] is True
        assert record["no_quantum_advantage_claim_flag"] is True


def test_atomicrows_pre_bridge_metadata_only():
    for record in _fixture()["artifacts"]["historical_dataset_atomicrows_pre_bridge_metadata"]:
        assert record["atomicrows_bundle_created_flag"] is False
        assert record["atomicrows_bundle_sha_created_flag"] is False
        assert record["atomicrows_rows_created_flag"] is False


def test_atomicrows_bundle_and_sha_paths_not_created_or_edited():
    assert hd.validate_protected_artifacts(REPO_ROOT) == []


def test_noncanonical_forecastex_identity_blocks():
    record = _first_digest()
    record["venue_scope"] = policy.FORBIDDEN_VENUE_IDENTITIES[0]
    assert policy.BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY in _codes(
        hd.validate_dataset_records([record])
    )


def test_versioned_candidate_set_snapshot_lock_not_global_freeze():
    record = _first_digest()
    record["global_candidate_freeze_flag"] = True
    assert policy.BLOCKED_GLOBAL_PERMANENT_CANDIDATE_FREEZE_LANGUAGE in _codes(
        hd.validate_dataset_records([record])
    )


def test_market_specific_section_index_has_all_four_scopes():
    scopes = [row["canonical_venue_id"] for row in _report("PR135MarketSpecificSectionIndex.report.json")["market_scopes"]]
    assert tuple(scopes) == policy.CANONICAL_VENUE_IDS


def test_master_plan_crosswalk_has_required_sections():
    rows = _report("PR135MasterPlanSectionCrosswalk.report.json")["rows"]
    assert len(rows) >= 12
    assert any("Roadmap PR117" in row["section_title_or_anchor"] for row in rows)


def test_command_action_matrix_has_no_network_or_github_actions():
    for row in _report("PR135CommandActionMatrix.report.json")["actions"]:
        assert row["network_allowed"] is False
        assert row["github_allowed"] is False


def test_source_evidence_packet_is_not_external_fact_authority():
    manifest = _report("PR135HistoricalDatasetPolicyManifest.report.json")
    assert (
        policy.OWNER_DEFINITIONS_PACKET_NOT_EXTERNAL_FACT_AUTHORITY
        in manifest["source_boundary_constants"]
    )


def test_fixture_shape_only_not_venue_fact_truth():
    fixture = _fixture()
    assert fixture["fixture_shape_only_not_venue_fact_truth_flag"] is True
    assert fixture["source_boundary_language"] == policy.SOURCE_BOUNDARY_LANGUAGE


def test_validator_marker_only_on_full_pass():
    assert hd.marker_for_failures([]) == policy.VALIDATOR_MARKER
    assert hd.marker_for_failures([hd.ValidationFailure("x", "y", "z")]) == ""
