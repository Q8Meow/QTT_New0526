"""Deterministic PR153S report builder."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

from . import classifier
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


def _receipt_summary(path_records: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    consumed = [record for record in path_records if record.get("consumed") is True]
    missing = [record for record in path_records if record.get("exists") is False]
    return {
        "artifact_count": len(path_records),
        "consumed_count": len(consumed),
        "missing_requested_artifact_paths": [
            str(record["artifact_path"]) for record in missing
        ],
        "uses_path_status_and_validator_markers_only": True,
        "global_hash_fields_created": False,
    }


def _accepted_artifact_count(pr153r_report: Mapping[str, Any]) -> int:
    return int(pr153r_report.get("accepted_source_packet_artifact_count") or 0)


def _target_count_summary(records: list[Mapping[str, Any]], pr153_report: Mapping[str, Any]) -> dict[str, Any]:
    denominator = _mapping(pr153_report.get("corrected_denominator_summary"))
    return {
        "total_targets_count": len(records),
        "true_external_public_source_value_denominator": denominator.get(
            "true_external_public_source_value_capture_target_count"
        ),
        "captured_candidate_packets_count": denominator.get("captured_candidate_packet_count"),
        "pr153r_retry_targets_count": denominator.get(
            "remaining_external_public_capture_retry_target_count"
        ),
        "internal_control_plane_targets_count": denominator.get(
            "internal_control_plane_target_count"
        ),
        "split_reclassification_targets_count": denominator.get(
            "target_split_or_reclassification_required_count"
        ),
        "private_doc_attestation_targets_count": denominator.get(
            "private_doc_or_attestation_required_count"
        ),
        "owner_provided_candidate_route_targets_count": denominator.get(
            "owner_provided_value_candidate_route_count"
        ),
        "accepted_source_ready_existing_packet_only_count": sum(
            1
            for record in records
            if record.get("closure_lane")
            == tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY
        ),
        "unknown_fail_closed_count": sum(
            1
            for record in records
            if record.get("closure_lane") == tx.CLOSURE_UNKNOWN_FAIL_CLOSED
        ),
        "canonical_arithmetic_342_all_targets": (
            int(denominator.get("captured_candidate_packet_count") or 0)
            + int(denominator.get("remaining_external_public_capture_retry_target_count") or 0)
            + int(denominator.get("internal_control_plane_target_count") or 0)
            + int(denominator.get("target_split_or_reclassification_required_count") or 0)
            + int(denominator.get("private_doc_or_attestation_required_count") or 0)
            + int(denominator.get("owner_provided_value_candidate_route_count") or 0)
        ),
        "canonical_arithmetic_126_public_external_denominator": (
            int(denominator.get("captured_candidate_packet_count") or 0)
            + int(denominator.get("remaining_external_public_capture_retry_target_count") or 0)
        ),
        "counts_derived_from_upstream_pr153_denominator_summary": True,
    }


def _identity_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    keys = [str(record.get("canonical_identity_key") or "") for record in records]
    ids = [str(record.get("target_id") or "") for record in records]
    key_counts = Counter(keys)
    id_counts = Counter(ids)
    missing_key_records = [
        str(record.get("target_id"))
        for record in records
        if not record.get("canonical_identity_key")
        or any(part == "" for part in str(record["canonical_identity_key"]).split("|"))
    ]
    return {
        "identity_fields_preference_order": [
            "platform_scope",
            "target_field_path",
            "upstream_target_id",
            "target_id",
        ],
        "identity_fields_available_for_all_records": not missing_key_records,
        "identity_fallback_used": False,
        "index_only_identity_used": False,
        "missing_identity_record_ids": sorted(missing_key_records),
        "duplicate_identity_keys": sorted(
            key for key, count in key_counts.items() if count > 1
        ),
        "duplicate_target_ids": sorted(key for key, count in id_counts.items() if count > 1),
        "stable_sort_key": [
            "platform_scope",
            "target_field_path",
            "upstream_target_id",
            "target_id",
        ],
    }


def _public_external_denominator_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    captured = sum(
        1
        for record in records
        if record.get("closure_lane")
        == tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE
    )
    retry = sum(
        1
        for record in records
        if record.get("closure_lane")
        == tx.CLOSURE_PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE
    )
    accepted = sum(
        1
        for record in records
        if record.get("closure_lane")
        == tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY
    )
    return {
        "captured_public_external_candidate_count": captured,
        "pr153r_retry_public_external_candidate_count": retry,
        "accepted_public_external_existing_packet_count": accepted,
        "true_external_public_source_value_denominator": captured + retry + accepted,
        "internal_control_plane_counted_as_missing_public_source": False,
        "private_doc_attestation_counted_as_public_source_failure": False,
        "owner_route_counted_as_accepted_public_source": False,
    }


def _no_authority_receipt(pr153r_report: Mapping[str, Any]) -> dict[str, Any]:
    receipt = tx.zero_authority_counters()
    receipt.update(
        {
            "accepted_source_packet_existing_upstream_count": int(
                pr153r_report.get("accepted_source_packet_count") or 0
            ),
            "accepted_source_packet_artifact_count_existing_upstream": _accepted_artifact_count(
                pr153r_report
            ),
            "source_evidence_digest_metadata_allowed_when_target_field_scoped": True,
            "source_evidence_digest_metadata_copied_into_pr153s_records": False,
            "source_evidence_digest_metadata_count_from_pr153r_upstream": int(
                pr153r_report.get("source_packet_digest_metadata_count") or 0
            ),
            "source_retrieval_created": False,
            "source_acceptance_created": False,
            "connector_semantic_binding_created": False,
            "runtime_live_order_profit_authority_created": False,
            "replay_paper_execution_created": False,
            "quantum_backend_simulator_optimizer_execution_created": False,
            "atomicrows_bundle_hash_path_referenced": False,
            "atomicrows_bundle_data_path_referenced": False,
        }
    )
    return receipt


def _pr154_contract_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    allowed_records = [
        record for record in records if record.get("pr154_materialization_allowed") is True
    ]
    return {
        "contract_id": tx.PR154_CONSUMER_POLICY_ID,
        "pr154_materialization_allowed_count": len(allowed_records),
        "pr154_materialization_blocked_count": len(records) - len(allowed_records),
        "candidate_values_materialized_as_accepted_facts": False,
        "owner_route_values_materialized_as_facts": False,
        "private_doc_values_used_without_attestation": False,
        "split_targets_used_before_reclassification": False,
        "runtime_values_used_without_receipt": False,
        "quantum_values_used_without_execution_evidence": False,
        "consumer_guard_fields": list(tx.PR154_CONSUMER_GUARD_FIELDS),
        "route_counts": _counter(records, "materialization_readiness_route"),
    }


def _atomicrows_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "compatibility_class_summary": _counter(records, "atomicrows_compatibility_class"),
        "row_values_created_by_pr153s": 0,
        "bundle_created_by_pr153s": False,
        "bundle_hash_or_sha_authority_created_by_pr153s": False,
        "bundle_hash_path_referenced_by_pr153s": False,
        "bundle_data_path_referenced_by_pr153s": False,
        "row_family_mutated_by_pr153s": False,
        "future_pr154_readiness_ledger_only": True,
    }


def _quantum_receipt(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "quantum_forward_compatibility_class_summary": _counter(
            records,
            "quantum_forward_compatibility_class",
        ),
        "quantum_execution_required_before_value_count": sum(
            1 for record in records if record.get("quantum_execution_required_before_value")
        ),
        "quantum_backend_execution_created": False,
        "quantum_simulator_execution_created": False,
        "qaoa_execution_created": False,
        "vqe_execution_created": False,
        "annealing_execution_created": False,
        "qubo_or_ising_solver_execution_created": False,
        "optimizer_arbitration_created": False,
        "quantum_advantage_claim_created": False,
        "metadata_only_for_future_pr159_pr160_readiness": True,
    }


def _latency_receipt() -> dict[str, Any]:
    return {
        "source_retrieval_control_plane_only": True,
        "source_acceptance_control_plane_only": True,
        "live_pretrade_path_consumes_precomputed_authorized_values_only": True,
        "pr154_pr155_must_not_call_source_retrieval_in_hot_path": True,
        "pr154_pr155_must_not_call_source_acceptance_in_hot_path": True,
        "candidate_values_blocked_from_live_hot_path": True,
        "internal_owner_policy_values_require_authority_before_use": True,
        "runtime_private_state_values_require_receipts_before_use": True,
        "replay_paper_quantum_values_require_evidence_gates_before_use": True,
        "live_reachability_created": False,
        "order_authority_created": False,
    }


def _hidden_ambiguity_audit(
    records: list[Mapping[str, Any]],
    reconstruction_failures: tuple[str, ...],
) -> dict[str, Any]:
    identity = _identity_receipt(records)
    unknown = [
        str(record.get("target_id"))
        for record in records
        if record.get("closure_lane") == tx.CLOSURE_UNKNOWN_FAIL_CLOSED
    ]
    return {
        "reconstruction_failures": list(reconstruction_failures),
        "duplicate_identity_keys": identity["duplicate_identity_keys"],
        "duplicate_target_ids": identity["duplicate_target_ids"],
        "unknown_fail_closed_target_ids": sorted(unknown),
        "ambiguous_lane_assignment_count": len(unknown),
        "committed_report_unknown_fail_closed_count": len(unknown),
        "validation_must_fail_if_nonzero": True,
    }


def build_report(repo_root: Path | str) -> dict[str, Any]:
    records, upstream = classifier.classify_targets(repo_root)
    closure_summary = classifier.count_by(records, "closure_lane", tx.CLOSURE_LANES)
    materialization_summary = classifier.count_by(
        records,
        "materialization_readiness_route",
        tx.MATERIALIZATION_ROUTES,
    )
    accepted_count = sum(
        1
        for record in records
        if record.get("closure_lane") == tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY
    )
    unknown_count = closure_summary[tx.CLOSURE_UNKNOWN_FAIL_CLOSED]
    final_status = tx.FINAL_STATUS_READY if unknown_count == 0 else tx.FINAL_STATUS_FAIL_CLOSED

    return {
        "report_id": tx.REPORT_ID,
        "validator_marker": tx.VALIDATOR_MARKER,
        "semantic_pr_label": tx.SEMANTIC_PR_LABEL,
        "purpose": tx.PURPOSE,
        "taxonomy_module_path": tx.TAXONOMY_MODULE_PATH,
        "consumed_artifacts_read_receipt": {
            "summary": _receipt_summary(upstream.consumed_artifact_receipts),
            "artifacts": list(upstream.consumed_artifact_receipts),
        },
        "orchestration_alignment_receipt": dict(upstream.orchestration_alignment_receipt),
        "upstream_input_reconstruction_receipt": {
            "target_universe_source": (
                "PR151 official_source_retrieval_target_queue canonical target records"
            ),
            "pr151_target_count": len(upstream.pr151_targets),
            "pr153_candidate_packet_count": len(upstream.pr153_candidates_by_id),
            "pr153_owner_blocker_queue_count": len(upstream.pr153_owner_queue_by_id),
            "pr153r_retry_record_count": len(upstream.pr153r_records_by_id),
            "per_target_records_created": len(records),
            "fabricated_target_records_created": 0,
            "source_capture_candidate_packets_used_as_accepted_values": False,
            "owner_route_material_used_as_fact": False,
            "reconstruction_failures": list(upstream.reconstruction_failures),
        },
        "target_identity_resolution_receipt": _identity_receipt(records),
        "target_count_summary": _target_count_summary(records, upstream.pr153_report),
        "closure_lane_summary": closure_summary,
        "materialization_readiness_summary": materialization_summary,
        "per_target_closure_records": records,
        "public_external_source_denominator_receipt": (
            _public_external_denominator_receipt(records)
        ),
        "pr154_materialization_consumer_contract_receipt": _pr154_contract_receipt(records),
        "atomicrows_compatibility_receipt": _atomicrows_receipt(records),
        "quantum_forward_compatibility_receipt": _quantum_receipt(records),
        "latency_and_day1_launch_readiness_receipt": _latency_receipt(),
        "no_authority_creation_receipt": _no_authority_receipt(upstream.pr153r_report),
        "hidden_ambiguity_audit": _hidden_ambiguity_audit(
            records,
            upstream.reconstruction_failures,
        ),
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
                "upstream_target_id",
                "target_id",
            ],
        },
        "accepted_source_ready_existing_packet_only_count": accepted_count,
        "final_status_label": final_status,
    }


def write_report_file(repo_root: Path | str) -> Path:
    root = Path(repo_root).resolve()
    report = build_report(root)
    path = root / tx.REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(report), encoding="utf-8")
    return path
