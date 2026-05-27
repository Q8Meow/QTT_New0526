"""Deterministic PR154 report builder."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

from . import materializer
from . import taxonomy as tx


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _counter(records: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(record.get(key) or "") for record in records)
    return dict(sorted(counter.items()))


def _counter_from_values(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _receipt_summary(receipts: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    consumed = [receipt for receipt in receipts if receipt.get("consumed") is True]
    missing = [receipt for receipt in receipts if receipt.get("exists") is False]
    return {
        "artifact_count": len(receipts),
        "consumed_count": len(consumed),
        "missing_requested_artifact_paths": [
            str(receipt.get("artifact_path")) for receipt in missing
        ],
        "uses_path_status_and_validator_markers_only": True,
        "global_hash_fields_created": False,
    }


def _pr153s_consumption_receipt(
    records: list[Mapping[str, Any]],
    pr154_records: list[Mapping[str, Any]],
    pr153s_report: Mapping[str, Any],
) -> dict[str, Any]:
    source_ids = [str(record.get("target_id")) for record in records]
    bridge_source_ids = [str(record.get("source_pr153s_target_id")) for record in pr154_records]
    return {
        "source_report_path": "docs/master_plan/generated/PR153S_SourceValueCaptureClosureClassifier.report.json",
        "source_report_id": pr153s_report.get("report_id"),
        "source_validator_marker": pr153s_report.get("validator_marker"),
        "source_final_status_label": pr153s_report.get("final_status_label"),
        "pr153s_record_count": len(records),
        "pr154_record_count": len(pr154_records),
        "all_pr153s_records_consumed": sorted(source_ids) == sorted(bridge_source_ids),
        "missing_pr153s_target_ids": sorted(set(source_ids) - set(bridge_source_ids)),
        "fabricated_pr154_source_target_ids": sorted(set(bridge_source_ids) - set(source_ids)),
        "duplicate_pr153s_target_ids": sorted(
            key for key, count in Counter(source_ids).items() if count > 1
        ),
        "duplicate_pr154_source_target_ids": sorted(
            key for key, count in Counter(bridge_source_ids).items() if count > 1
        ),
        "materialization_routes_controlled_by_pr153s": True,
        "pr153s_materialization_route_summary": _counter(records, "materialization_readiness_route"),
    }


def _official_candidate_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    pr153 = [
        record
        for record in records
        if record["pr153s_closure_lane"]
        == "PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE"
    ]
    pr153r = [
        record
        for record in records
        if record["pr153s_closure_lane"]
        == "PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE"
    ]
    return {
        "owner_approved_fast_lane_enabled": True,
        "separate_later_acceptance_pr_required_for_complete_candidates": False,
        "pr153_candidates_inspected": len(pr153),
        "pr153_candidates_accepted_materialized": sum(
            1
            for record in pr153
            if record["materialization_decision"]
            == tx.MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE
        ),
        "pr153_candidates_blocked_with_exact_missing_fields": sum(
            1 for record in pr153 if not record["materialization_allowed"]
        ),
        "pr153r_retry_candidates_inspected": len(pr153r),
        "pr153r_retry_candidates_accepted_materialized": sum(
            1
            for record in pr153r
            if record["materialization_decision"]
            in {
                tx.MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE,
                tx.MATERIALIZED_EXISTING_ACCEPTED_SOURCE_VALUE,
            }
        ),
        "pr153r_retry_candidates_blocked_with_exact_missing_fields": sum(
            1 for record in pr153r if not record["materialization_allowed"]
        ),
        "candidate_values_left_blocked_only_for_later_acceptance_pr": 0,
        "incomplete_candidate_values_promoted": 0,
    }


def _owner_internal_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    internal = [
        record
        for record in records
        if record["pr153s_closure_lane"] == "INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE"
    ]
    materialized = [
        record
        for record in internal
        if record["materialization_decision"]
        == tx.MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT
    ]
    return {
        "internal_control_plane_targets_inspected": len(internal),
        "owner_authorized_internal_policy_defaults_materialized": len(materialized),
        "internal_control_plane_targets_blocked": len(internal) - len(materialized),
        "policy_default_key": tx.OWNER_INTERNAL_POLICY_DEFAULT_KEY,
        "policy_default_value": tx.OWNER_INTERNAL_POLICY_DEFAULT_VALUE,
        "policy_default_logic": tx.OWNER_INTERNAL_POLICY_DEFAULT_LOGIC,
        "external_facts_created": False,
        "risk_capital_sizing_values_created": False,
        "aggressive_live_exposure_defaults_created": False,
    }


def _owner_route_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    owner_route = [
        record
        for record in records
        if record["pr153s_closure_lane"] == "OWNER_PROVIDED_ROUTE_REQUIRED"
    ]
    blocked = [record for record in owner_route if not record["materialization_allowed"]]
    missing = [
        field
        for record in blocked
        for field in _list(record.get("missing_fields"))
    ]
    return {
        "owner_route_targets_inspected": len(owner_route),
        "owner_route_targets_materialized": len(owner_route) - len(blocked),
        "owner_route_targets_blocked": len(blocked),
        "missing_route_locator_value_field_summary": _counter_from_values(missing),
        "owner_route_hints_promoted_without_value_locator": 0,
    }


def _materialization_count_summary(records: list[Mapping[str, Any]]) -> dict[str, int]:
    materialized = [record for record in records if record["materialization_allowed"]]
    blocked = [record for record in records if not record["materialization_allowed"]]
    return {
        "total_pr154_records": len(records),
        "materialized_value_count": len(materialized),
        "accepted_official_source_materialized_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            == tx.MATERIALIZED_OFFICIAL_SOURCE_CANDIDATE
        ),
        "existing_accepted_source_materialized_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            == tx.MATERIALIZED_EXISTING_ACCEPTED_SOURCE_VALUE
        ),
        "owner_internal_materialized_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            == tx.MATERIALIZED_OWNER_APPROVED_INTERNAL_QTT_POLICY_DEFAULT
        ),
        "blocked_count": len(blocked),
        "blocked_pending_accepted_source_completion_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            in {
                tx.BLOCKED_INCOMPLETE_OFFICIAL_SOURCE_CANDIDATE,
                tx.BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET,
            }
        ),
        "blocked_pending_pr153r_completion_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            == tx.BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW
        ),
        "blocked_pending_split_reclassification_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            == tx.BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION
        ),
        "blocked_pending_private_doc_attestation_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            == tx.BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION
        ),
        "blocked_pending_owner_route_count": sum(
            1
            for record in records
            if record["materialization_decision"] == tx.BLOCKED_PENDING_OWNER_ROUTE_PACKET
        ),
        "blocked_pending_internal_owner_policy_count": sum(
            1
            for record in records
            if record["materialization_decision"]
            == tx.BLOCKED_PENDING_INTERNAL_OWNER_POLICY_VALUE
        ),
        "runtime_materialized_count": 0,
        "replay_paper_materialized_count": 0,
        "quantum_execution_materialized_count": 0,
        "live_order_profit_materialized_count": 0,
    }


def _completion_summary(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    blocked = [record for record in records if not record["materialization_allowed"]]
    return {
        "blocked_record_count": len(blocked),
        "required_next_task_by_count": _counter(blocked, "required_next_task"),
        "required_next_pr_or_phase_by_count": _counter(
            blocked,
            "required_next_pr_or_phase",
        ),
        "required_input_artifact_by_count": _counter(blocked, "required_input_artifact"),
        "missing_fields_by_count": _counter_from_values(
            [
                str(field)
                for record in blocked
                for field in _list(record.get("missing_fields"))
            ]
        ),
        "exact_unblock_condition_by_count": _counter(blocked, "exact_unblock_condition"),
        "all_blocked_records_have_codex_steps": all(
            bool(record.get("codex_actionable_completion_steps")) for record in blocked
        ),
    }


def _source_value_authority_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "authority_class_summary": _counter(records, "materialized_value_authority_class"),
        "value_source_class_summary": _counter(records, "materialized_value_source_class"),
        "accepted_source_decision_scope": {
            "pr153_complete_candidate_fast_lane_count": sum(
                1
                for record in records
                if record["acceptance_decision"] == tx.ACCEPTANCE_OWNER_FAST_LANE
            ),
            "owner_internal_policy_default_count": sum(
                1
                for record in records
                if record["acceptance_decision"] == tx.ACCEPTANCE_OWNER_INTERNAL_POLICY
            ),
        },
        "source_evidence_digest_metadata_materialized_as_default_value_count": 0,
    }


def _atomicrows_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "compatibility_class_summary": _counter(records, "atomicrows_compatibility_class"),
        "row_materialization_status_summary": _counter(
            records,
            "atomicrows_row_materialization_status",
        ),
        "all_pr153s_targets_have_bridge_records": True,
        "materialized_values_have_allowed_authority": all(
            record["materialized_value_authority_class"] in tx.AUTHORITY_CLASSES
            for record in records
            if record["materialization_allowed"]
        ),
        "blocked_records_have_exact_completion_paths": all(
            record["required_next_task"] and record["exact_unblock_condition"]
            for record in records
            if not record["materialization_allowed"]
        ),
        "incomplete_candidate_exposed_as_agent_consumable_default_count": 0,
        "bundle_created_by_pr154": False,
        "bundle_hash_or_sha_authority_created_by_pr154": False,
        "bundle_hash_path_referenced_by_pr154": False,
        "bundle_data_path_referenced_by_pr154": False,
        "row_family_mutated_by_pr154": False,
    }


def _agent_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "agent_consumption_readiness_summary": _counter(
            records,
            "agent_consumption_readiness_class",
        ),
        "agent_ready_record_count": sum(
            1
            for record in records
            if record["agent_consumption_readiness_class"]
            == tx.AGENT_CONSUMABLE_DEFAULT_READY
        ),
        "unauthorized_or_incomplete_values_excluded_count": sum(
            1
            for record in records
            if record["agent_consumption_readiness_class"]
            != tx.AGENT_CONSUMABLE_DEFAULT_READY
        ),
        "pr155_must_consume_precomputed_pr154_ledger_only": True,
        "source_retrieval_or_acceptance_calls_allowed_for_pr155_consumption": False,
    }


def _quantum_receipt(
    records: list[Mapping[str, Any]],
    quantum_receipts: tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    return {
        "quantum_forward_compatibility_class_summary": _counter(
            records,
            "quantum_forward_compatibility_class",
        ),
        "quantum_optimizer_default_route_summary": _counter(
            records,
            "quantum_optimizer_default_route",
        ),
        "quantum_execution_required_before_use_count": sum(
            1 for record in records if record["quantum_execution_required_before_use"]
        ),
        "quantum_context_artifacts": list(quantum_receipts),
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "quantum_optimizer_execution_created": False,
        "qaoa_execution_created": False,
        "vqe_execution_created": False,
        "annealing_execution_created": False,
        "qubo_or_ising_solver_execution_created": False,
        "optimizer_arbitration_created": False,
        "quantum_advantage_claim_created": False,
        "metadata_only_for_future_pr159_pr160_readiness": True,
    }


def _latency_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "low_latency_hot_path_eligibility_summary": _counter(
            records,
            "low_latency_hot_path_eligibility",
        ),
        "pr154_output_is_precomputed_control_plane_bridge_ledger": True,
        "live_pretrade_path_must_not_call_source_retrieval": True,
        "live_pretrade_path_must_not_call_source_acceptance": True,
        "live_pretrade_path_must_not_materialize_pr154_dynamically": True,
        "live_pretrade_path_consumes_only_future_pr155_agent_safe_registry": True,
        "unauthorized_values_blocked_before_hot_path": True,
        "incomplete_candidate_values_excluded_from_live_hot_path": True,
        "runtime_private_state_values_require_receipts": True,
        "replay_paper_quantum_values_require_evidence_gates": True,
        "live_reachability_created": False,
        "order_authority_created": False,
    }


def _no_authority_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    receipt: dict[str, Any] = tx.zero_authority_counters()
    receipt.update(
        {
            "runtime_live_order_authority_created_count": sum(
                1 for record in records if record["runtime_live_order_authority_created"]
            ),
            "profit_evidence_created_count": sum(
                1 for record in records if record["profit_evidence_created"]
            ),
            "source_retrieval_created": False,
            "source_acceptance_created_as_separate_later_pr_requirement": False,
            "connector_semantic_binding_created": False,
            "accepted_source_packet_created_by_pr154": False,
            "atomicrows_bundle_data_path_referenced": False,
            "atomicrows_bundle_hash_path_referenced": False,
            "source_evidence_digest_metadata_acknowledged_as_upstream_provenance": True,
            "source_evidence_digest_metadata_materialized_as_trading_default": False,
        }
    )
    return receipt


def _hidden_ambiguity_audit(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    ids = [str(record.get("pr154_record_id")) for record in records]
    source_ids = [str(record.get("source_pr153s_target_id")) for record in records]
    unknown = [
        str(record.get("source_pr153s_target_id"))
        for record in records
        if record.get("materialization_decision") == tx.BLOCKED_UNKNOWN_FAIL_CLOSED
    ]
    return {
        "duplicate_pr154_record_ids": sorted(
            key for key, count in Counter(ids).items() if count > 1
        ),
        "duplicate_source_pr153s_target_ids": sorted(
            key for key, count in Counter(source_ids).items() if count > 1
        ),
        "unknown_fail_closed_target_ids": sorted(unknown),
        "committed_report_unknown_fail_closed_count": len(unknown),
        "validation_must_fail_if_nonzero": True,
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    records, loaded = materializer.materialize_records(repo_root)
    pr153s_records = list(loaded.pr153s_records)
    decision_summary = materializer.count_by(
        records,
        "materialization_decision",
        tx.MATERIALIZATION_DECISIONS,
    )
    unknown_count = decision_summary[tx.BLOCKED_UNKNOWN_FAIL_CLOSED]
    final_status = tx.FINAL_STATUS_READY if unknown_count == 0 else tx.FINAL_STATUS_FAIL_CLOSED
    return {
        "report_id": tx.REPORT_ID,
        "validator_marker": tx.VALIDATOR_MARKER,
        "semantic_pr_label": tx.SEMANTIC_PR_LABEL,
        "purpose": tx.PURPOSE,
        "taxonomy_module_path": tx.TAXONOMY_MODULE_PATH,
        "consumed_artifacts_read_receipt": {
            "summary": _receipt_summary(loaded.consumed_artifact_receipts),
            "artifacts": list(loaded.consumed_artifact_receipts),
        },
        "orchestration_alignment_receipt": dict(
            loaded.pr153s_upstream.orchestration_alignment_receipt
        ),
        "pr153s_consumption_receipt": _pr153s_consumption_receipt(
            pr153s_records,
            records,
            loaded.pr153s_report,
        ),
        "official_candidate_fast_lane_acceptance_receipt": (
            _official_candidate_receipt(records)
        ),
        "owner_internal_policy_materialization_receipt": _owner_internal_receipt(
            records
        ),
        "owner_route_materialization_receipt": _owner_route_receipt(records),
        "authorized_value_source_manifest_receipt": {
            "source_classes": list(tx.VALUE_SOURCE_CLASSES),
            "authority_classes": list(tx.AUTHORITY_CLASSES),
            "owner_fast_lane_authorized_for_complete_candidates": True,
            "owner_internal_policy_default_authorized": True,
            "runtime_replay_paper_quantum_live_values_disallowed_in_pr154": True,
        },
        "source_value_authority_receipt": _source_value_authority_receipt(records),
        "materialization_count_summary": _materialization_count_summary(records),
        "materialization_decision_summary": decision_summary,
        "blocked_materialization_summary": _counter(
            [record for record in records if not record["materialization_allowed"]],
            "materialization_block_code",
        ),
        "completion_path_summary": _completion_summary(records),
        "accepted_source_materialization_receipt": _official_candidate_receipt(records),
        "atomicrows_compatibility_receipt": _atomicrows_receipt(records),
        "agent_consumption_readiness_receipt": _agent_receipt(records),
        "quantum_forward_compatibility_receipt": _quantum_receipt(
            records,
            loaded.quantum_artifact_receipts,
        ),
        "latency_and_day1_launch_readiness_receipt": _latency_receipt(records),
        "no_authority_creation_receipt": _no_authority_receipt(records),
        "hidden_ambiguity_audit": _hidden_ambiguity_audit(records),
        "deterministic_generation_receipt": {
            "utf8_final_newline": True,
            "json_indent": 2,
            "json_sort_keys": True,
            "wall_clock_timestamps_used": False,
            "local_absolute_paths_used": False,
            "runtime_git_branch_or_head_used": False,
            "random_values_used": False,
            "object_repr_or_python_object_id_used": False,
            "per_target_sort_key": [
                "platform_scope",
                "target_field_path",
                "source_pr153s_target_id",
                "pr154_record_id",
            ],
        },
        "per_target_materialization_records": records,
        "final_status_label": final_status,
    }


def write_report_file(repo_root: Path | str) -> Path:
    root = Path(repo_root).resolve()
    path = root / tx.REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(build_report(root)), encoding="utf-8", newline="\n")
    return path
