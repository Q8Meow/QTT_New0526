from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.atomicrows_parameter_default_value_materialization_gate import (
    materializer,
    report as report_builder,
    taxonomy as tx,
    validator,
)
from src.qtt.stage1_prediction_markets.controlled_official_source_capture_candidate_packets import (
    constants as pr153_c,
)
from src.qtt.stage1_prediction_markets.pr153s_source_value_capture_closure_classifier import (
    taxonomy as pr153s_tx,
)
from tools import run_validation_gates
from tools import validate_atomicrows_parameter_default_value_materialization_gate as pr154_cli


REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _report() -> dict:
    return report_builder.build_report(REPO_ROOT)


def _records() -> list[dict]:
    return _report()["per_target_materialization_records"]


def _records_by_lane(lane: str) -> list[dict]:
    return [record for record in _records() if record["pr153s_closure_lane"] == lane]


def _records_by_decision(decision: str) -> list[dict]:
    return [record for record in _records() if record["materialization_decision"] == decision]


def test_pr154_report_generation_is_deterministic_across_repeated_builds():
    first = report_builder.json_dump(report_builder.build_report(REPO_ROOT))
    second = report_builder.json_dump(report_builder.build_report(REPO_ROOT))
    payload = json.loads(first)

    assert first == second
    assert payload["deterministic_generation_receipt"]["wall_clock_timestamps_used"] is False
    assert payload["deterministic_generation_receipt"]["runtime_git_branch_or_head_used"] is False


def test_all_342_pr153s_targets_have_exactly_one_pr154_bridge_record_without_fabrication():
    pr153s = json.loads(
        (REPO_ROOT / pr153s_tx.REPORT_PATH).read_text(encoding="utf-8")
    )
    pr153s_ids = {
        record["target_id"] for record in pr153s["per_target_closure_records"]
    }
    records = _records()

    assert len(records) == pr153_c.PR153A_TOTAL_PR151_TARGETS
    assert {record["source_pr153s_target_id"] for record in records} == pr153s_ids
    assert _report()["pr153s_consumption_receipt"]["fabricated_pr154_source_target_ids"] == []
    assert _report()["pr153s_consumption_receipt"]["missing_pr153s_target_ids"] == []


def test_no_duplicate_pr154_identity_or_source_identity_exists():
    hidden = _report()["hidden_ambiguity_audit"]

    assert hidden["duplicate_pr154_record_ids"] == []
    assert hidden["duplicate_source_pr153s_target_ids"] == []
    assert hidden["committed_report_unknown_fail_closed_count"] == 0
    assert len({record["pr154_record_id"] for record in _records()}) == len(_records())


def test_complete_pr153_official_source_candidates_are_accepted_and_materialized():
    candidate_records = _records_by_lane(
        pr153s_tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE
    )

    assert len(candidate_records) == pr153_c.PR153A_CAPTURED_CANDIDATE_PACKET_COUNT
    assert all(record["materialization_allowed"] is True for record in candidate_records)
    assert all(
        record["materialization_decision"] == tx.MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE
        for record in candidate_records
    )
    assert all(record["materialized_value"] for record in candidate_records)
    assert all(record["candidate_value_promoted_to_materialized_value"] for record in candidate_records)
    assert all(record["accepted_source_packet_required"] is False for record in candidate_records)


def test_incomplete_official_source_candidate_is_blocked_with_exact_missing_fields():
    records, loaded = materializer.materialize_records(REPO_ROOT)
    first_candidate_record = next(
        record
        for record in loaded.pr153s_records
        if record["closure_lane"]
        == pr153s_tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE
    )
    candidate = dict(
        loaded.pr153s_upstream.pr153_candidates_by_id[first_candidate_record["target_id"]]
    )
    candidate["captured_candidate_text_or_value"] = None
    candidate["quote_span_or_machine_field_locator"] = None

    blocked = materializer._materialize_candidate(first_candidate_record, candidate)

    assert records
    assert blocked["materialization_allowed"] is False
    assert blocked["materialized_value"] is None
    assert blocked["materialization_decision"] == tx.BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE
    assert tx.MISSING_CAPTURED_VALUE in blocked["missing_fields"]
    assert tx.MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR in blocked["missing_fields"]
    assert blocked["required_next_task"] == "COMPLETE_OFFICIAL_SOURCE_CANDIDATE_PACKET"
    assert blocked["codex_actionable_completion_steps"]


def test_candidate_values_are_not_left_blocked_for_absent_separate_acceptance_pr():
    receipt = _report()["official_candidate_fast_lane_acceptance_receipt"]

    assert receipt["separate_later_acceptance_pr_required_for_complete_candidates"] is False
    assert receipt["pr153_candidates_accepted_materialized"] == 92
    assert receipt["candidate_values_left_blocked_only_for_later_acceptance_pr"] == 0
    assert receipt["incomplete_candidate_values_promoted"] == 0


def test_pr153r_retry_records_follow_fast_lane_policy_but_remain_blocked_when_incomplete():
    retry_records = _records_by_lane(
        pr153s_tx.CLOSURE_PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE
    )

    assert len(retry_records) == pr153_c.PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT
    assert all(record["materialization_allowed"] is False for record in retry_records)
    assert all(
        record["materialization_decision"] == tx.BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW
        for record in retry_records
    )
    assert all(tx.MISSING_CAPTURED_VALUE in record["missing_fields"] for record in retry_records)
    assert all(
        tx.MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR in record["missing_fields"]
        for record in retry_records
    )
    assert all(record["candidate_value_promoted_to_materialized_value"] is False for record in retry_records)


def test_split_private_doc_and_owner_route_lanes_have_required_completion_paths():
    split_records = _records_by_decision(tx.BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION)
    private_records = _records_by_decision(tx.BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION)
    owner_route_records = _records_by_decision(tx.BLOCKED_PENDING_OWNER_ROUTE_PACKET)

    assert len(split_records) == pr153_c.PR153A_TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED_COUNT
    assert len(private_records) == pr153_c.PR153A_PRIVATE_DOC_OR_ATTESTATION_REQUIRED_COUNT
    assert len(owner_route_records) == pr153_c.PR153A_OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE_COUNT
    assert all(record["required_next_task"] == "SPLIT_OR_RECLASSIFY_TARGET" for record in split_records)
    assert all(record["required_next_task"] == "OWNER_PRIVATE_DOC_ATTESTATION_PACKET" for record in private_records)
    assert all(record["required_next_task"] == "OWNER_ROUTE_LOCATOR_PACKET_COMPLETION" for record in owner_route_records)
    assert all(record["candidate_value_promoted_to_materialized_value"] is False for record in owner_route_records)
    assert all(tx.OWNER_ROUTE_LOCATOR_REQUIRED in record["missing_fields"] for record in owner_route_records)


def test_internal_control_plane_records_materialize_owner_approved_policy_default():
    internal_records = _records_by_lane(
        pr153s_tx.CLOSURE_INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE
    )

    assert len(internal_records) == pr153_c.PR153A_INTERNAL_CONTROL_PLANE_TARGET_COUNT
    assert all(record["materialization_allowed"] is True for record in internal_records)
    assert all(
        record["materialization_decision"]
        == tx.MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT
        for record in internal_records
    )
    assert all(record["materialized_value"] == tx.OWNER_INTERNAL_POLICY_DEFAULT_VALUE for record in internal_records)
    assert all(
        record["materialized_value_authority_class"]
        == tx.AUTHORITY_OWNER_INTERNAL_POLICY_DEFAULT
        for record in internal_records
    )
    receipt = _report()["owner_internal_policy_materialization_receipt"]
    assert receipt["risk_capital_sizing_values_created"] is False
    assert receipt["aggressive_live_exposure_defaults_created"] is False


def test_internal_policy_value_absence_has_exact_owner_policy_completion_path():
    template = _records_by_lane(
        pr153s_tx.CLOSURE_INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE
    )[0].copy()
    blocked = materializer._blocked_record(
        template,
        block_code=tx.BLOCKED_PENDING_INTERNAL_OWNER_POLICY_VALUE,
        missing_fields=(tx.INTERNAL_OWNER_POLICY_VALUE_REQUIRED,),
        owner_internal_policy_required=True,
    )

    assert blocked["materialization_allowed"] is False
    assert blocked["required_next_task"] == "CREATE_OWNER_INTERNAL_POLICY_VALUE_LEDGER_ENTRY"
    assert blocked["required_input_artifact"] == "OWNER_INTERNAL_POLICY_VALUE_PACKET"
    assert "exact value/type/unit/scale" in blocked["exact_unblock_condition"]


def test_blocked_records_have_null_payload_and_blocked_authority_metadata():
    blocked_records = [record for record in _records() if not record["materialization_allowed"]]

    assert blocked_records
    for record in blocked_records:
        assert record["materialized_value"] is None
        assert record["materialized_value_type"] == tx.VALUE_TYPE_NONE
        assert record["materialized_value_source_class"] == tx.VALUE_SOURCE_NONE
        assert record["materialized_value_authority_class"] == tx.AUTHORITY_BLOCKED
        assert record["agent_consumption_readiness_class"] != tx.AGENT_CONSUMABLE_DEFAULT_READY
        assert record["live_pretrade_consumption_allowed"] is False


def test_forbidden_connector_runtime_replay_paper_quantum_live_profit_authorities_are_zero():
    counts = _report()["materialization_count_summary"]
    receipt = _report()["no_authority_creation_receipt"]
    quantum = _report()["quantum_forward_compatibility_receipt"]

    assert counts["runtime_materialized_count"] == 0
    assert counts["replay_paper_materialized_count"] == 0
    assert counts["quantum_execution_materialized_count"] == 0
    assert counts["live_order_profit_materialized_count"] == 0
    assert receipt["connector_unlock_count"] == 0
    assert receipt["runtime_private_state_receipt_value_count"] == 0
    assert receipt["replay_result_count"] == 0
    assert receipt["paper_result_count"] == 0
    assert receipt["profit_evidence_count"] == 0
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_optimizer_execution_created"] is False


def test_no_qtt_or_global_or_atomicrows_hash_authority_and_no_bundle_paths_are_created():
    serialized = report_builder.json_dump(_report())
    receipt = _report()["no_authority_creation_receipt"]
    atomicrows = _report()["atomicrows_compatibility_receipt"]

    assert "AtomicRows.bundle." + "jsonl" not in serialized
    assert "AtomicRows.bundle." + "sha" + "256" not in serialized
    assert receipt["qtt_sha_freeze_checksum_authority_count"] == 0
    assert receipt["global_repository_digest_authority_count"] == 0
    assert receipt["atomicrows_bundle_hash_sha_authority_count"] == 0
    assert atomicrows["bundle_created_by_pr154"] is False
    assert atomicrows["bundle_hash_or_sha_authority_created_by_pr154"] is False


def test_pr136_orchestration_and_pr153s_routes_are_consumed_as_path_status_not_hashes():
    consumed = _report()["consumed_artifacts_read_receipt"]
    orchestration = _report()["orchestration_alignment_receipt"]

    assert consumed["summary"]["uses_path_status_and_validator_markers_only"] is True
    assert consumed["summary"]["global_hash_fields_created"] is False
    assert orchestration["pr136_route_triage_consumed"] is True
    assert orchestration["pr136_section_crosswalk_requested_alias_exists"] is False
    assert orchestration["pr136_section_crosswalk_canonical_successor_consumed"] is True
    for record in _records():
        assert record["pr153s_materialization_route"]


def test_pr154_taxonomy_is_centralized_and_report_uses_known_decisions():
    assert _report()["taxonomy_module_path"] == tx.TAXONOMY_MODULE_PATH
    for record in _records():
        assert record["acceptance_decision"] in tx.ACCEPTANCE_DECISIONS
        assert record["materialization_decision"] in tx.MATERIALIZATION_DECISIONS
        assert record["atomicrows_compatibility_class"] in tx.ATOMICROWS_COMPATIBILITY_CLASSES


def test_agent_readiness_blocks_unauthorized_values_and_pr155_consumes_precomputed_ledger():
    agent = _report()["agent_consumption_readiness_receipt"]

    assert agent["agent_ready_record_count"] == 230
    assert agent["unauthorized_or_incomplete_values_excluded_count"] == 112
    assert agent["pr155_must_consume_precomputed_pr154_ledger_only"] is True
    assert agent["source_retrieval_or_acceptance_calls_allowed_for_pr155_consumption"] is False


def test_quantum_forward_metadata_is_metadata_only_and_never_execution_evidence():
    quantum = _report()["quantum_forward_compatibility_receipt"]

    assert quantum["metadata_only_for_future_pr159_pr160_readiness"] is True
    assert quantum["qaoa_execution_created"] is False
    assert quantum["vqe_execution_created"] is False
    assert quantum["annealing_execution_created"] is False
    assert quantum["qubo_or_ising_solver_execution_created"] is False
    assert quantum["optimizer_arbitration_created"] is False


def test_atomicrows_compatibility_receipt_is_bridge_ledger_only_no_bundle_or_row_family():
    receipt = _report()["atomicrows_compatibility_receipt"]

    assert receipt["all_pr153s_targets_have_bridge_records"] is True
    assert receipt["blocked_records_have_exact_completion_paths"] is True
    assert receipt["incomplete_candidate_exposed_as_agent_consumable_default_count"] == 0
    assert receipt["row_family_mutated_by_pr154"] is False


def test_source_evidence_digest_metadata_is_not_materialized_as_default_value():
    receipt = _report()["source_value_authority_receipt"]
    no_authority = _report()["no_authority_creation_receipt"]

    assert receipt["source_evidence_digest_metadata_materialized_as_default_value_count"] == 0
    assert no_authority["source_evidence_digest_metadata_acknowledged_as_upstream_provenance"] is True
    assert no_authority["source_evidence_digest_metadata_materialized_as_trading_default"] is False
    assert all(
        record["materialized_value_source_field_path"]
        != "source_packet_digest_metadata.source_packet_integrity_digest"
        for record in _records()
    )


def test_every_blocked_record_has_non_empty_completion_fields_and_codex_steps():
    for record in [record for record in _records() if not record["materialization_allowed"]]:
        assert record["required_next_task"]
        assert record["required_next_pr_or_phase"]
        assert record["responsible_authority"]
        assert record["required_input_artifact"]
        assert record["exact_unblock_condition"]
        assert record["materialization_retry_route"]
        assert record["codex_actionable_completion_steps"]


def test_low_latency_receipt_excludes_live_hot_path_dynamic_materialization():
    latency = _report()["latency_and_day1_launch_readiness_receipt"]

    assert latency["pr154_output_is_precomputed_control_plane_bridge_ledger"] is True
    assert latency["live_pretrade_path_must_not_call_source_retrieval"] is True
    assert latency["live_pretrade_path_must_not_call_source_acceptance"] is True
    assert latency["live_pretrade_path_must_not_materialize_pr154_dynamically"] is True
    assert latency["live_reachability_created"] is False
    assert latency["order_authority_created"] is False


def test_pr154_validator_accepts_tracked_report_and_cli_emits_marker(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(validator, "_changed_paths", lambda repo_root: [])

    failures = validator.validate_repository_artifacts(REPO_ROOT)
    assert failures == []

    assert pr154_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0
    assert capsys.readouterr().out.strip() == tx.VALIDATOR_MARKER


def test_pr154_changed_path_guard_still_rejects_atomicrows_generated_gate_reports(
    monkeypatch,
):
    generated_report_paths = [
        "docs/master_plan/generated/AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json",
        "docs/master_plan/generated/AtomicRowsBundleRowFamilySourceFiles.report.json",
        "docs/master_plan/generated/AtomicRowsBundleShaFreezeAuthorityGate.report.json",
        "docs/master_plan/generated/AtomicRowsFullBundleRowExpansionPlan.report.json",
    ]

    monkeypatch.setattr(
        validator,
        "_changed_paths",
        lambda repo_root: generated_report_paths,
    )

    assert validator.validate_repository_artifacts(REPO_ROOT) == sorted(
        f"PR154_CHANGED_PATH_OUT_OF_SCOPE: {path}"
        for path in generated_report_paths
    )


def test_run_validation_gates_includes_pr154_after_pr153s_without_tracked_write():
    commands = run_validation_gates.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr153s_index = command_names.index(
        "validate_pr153s_source_value_capture_closure_classifier.py"
    )
    pr154_index = command_names.index(
        "validate_atomicrows_parameter_default_value_materialization_gate.py"
    )
    next_index = command_names.index("validate_qtt_agent_role_operating_charter_registry.py")

    assert pr153s_index < pr154_index < next_index
    assert commands[pr154_index] == [
        run_validation_gates.sys.executable,
        str(Path("tools") / "validate_atomicrows_parameter_default_value_materialization_gate.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr154_index]
