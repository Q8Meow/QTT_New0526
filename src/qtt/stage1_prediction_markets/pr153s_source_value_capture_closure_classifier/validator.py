"""PR153S repository validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from . import classifier
from . import inputs
from . import report as report_builder
from . import taxonomy as tx


REQUIRED_REPORT_KEYS = (
    "report_id",
    "validator_marker",
    "semantic_pr_label",
    "purpose",
    "consumed_artifacts_read_receipt",
    "orchestration_alignment_receipt",
    "upstream_input_reconstruction_receipt",
    "target_identity_resolution_receipt",
    "target_count_summary",
    "closure_lane_summary",
    "materialization_readiness_summary",
    "per_target_closure_records",
    "public_external_source_denominator_receipt",
    "pr154_materialization_consumer_contract_receipt",
    "atomicrows_compatibility_receipt",
    "quantum_forward_compatibility_receipt",
    "latency_and_day1_launch_readiness_receipt",
    "no_authority_creation_receipt",
    "hidden_ambiguity_audit",
    "deterministic_generation_receipt",
    "final_status_label",
)

REQUIRED_RECORD_KEYS = (
    "target_id",
    "upstream_target_id",
    "canonical_identity_key",
    "platform_scope",
    "market_scope_if_available",
    "target_field_path",
    "parameter_family_or_target_family",
    "source_authority_class",
    "closure_lane",
    "closure_lane_basis",
    "materialization_readiness_route",
    "materialization_route_basis",
    "required_next_action",
    "blocker_codes",
    "upstream_artifact_refs",
    "public_external_denominator_member",
    "candidate_packet_present",
    "pr153_candidate_member",
    "pr153r_retry_member",
    "accepted_source_packet_present",
    "internal_control_plane_member",
    "split_or_reclassification_member",
    "private_doc_attestation_member",
    "owner_route_member",
    "runtime_receipt_route_member",
    "replay_paper_route_member",
    "quantum_evidence_route_member",
    "pr154_materialization_allowed",
    "pr154_materialization_block_reason",
    "pr154_required_authority_before_value",
    "pr154_allowed_value_source_class",
    "atomicrows_compatibility_class",
    "atomicrows_materialization_boundary",
    "quantum_forward_compatibility_class",
    "quantum_execution_required_before_value",
    "runtime_receipt_required_before_value",
    "replay_paper_required_before_value",
    "live_order_authority_created",
    *tx.PR154_CONSUMER_GUARD_FIELDS,
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _duplicate_values(values: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    for value in values:
        seen[value] = seen.get(value, 0) + 1
    return sorted(value for value, count in seen.items() if count > 1)


def _serialized_forbidden_path_failures(payload: Mapping[str, Any]) -> list[str]:
    serialized = report_builder.json_dump(payload)
    forbidden_data_path = "AtomicRows.bundle." + "jsonl"
    forbidden_hash_path = "AtomicRows.bundle." + "sha" + "256"
    failures: list[str] = []
    if forbidden_data_path in serialized:
        failures.append("PR153S_FORBIDDEN_ATOMICROWS_BUNDLE_DATA_PATH_REFERENCED")
    if forbidden_hash_path in serialized:
        failures.append("PR153S_FORBIDDEN_ATOMICROWS_BUNDLE_HASH_PATH_REFERENCED")
    return failures


def validate_report_payload(
    payload: Mapping[str, Any],
    repo_root: Path | str,
) -> list[str]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    for key in REQUIRED_REPORT_KEYS:
        if key not in payload:
            failures.append(f"PR153S_REQUIRED_REPORT_KEY_MISSING: {key}")

    if payload.get("report_id") != tx.REPORT_ID:
        failures.append("PR153S_REPORT_ID_MISMATCH")
    if payload.get("validator_marker") != tx.VALIDATOR_MARKER:
        failures.append("PR153S_VALIDATOR_MARKER_MISMATCH")
    if payload.get("semantic_pr_label") != tx.SEMANTIC_PR_LABEL:
        failures.append("PR153S_SEMANTIC_LABEL_MISMATCH")

    upstream = inputs.load_inputs(root)
    records = _list(payload.get("per_target_closure_records"))
    if len(records) != len(upstream.pr151_targets):
        failures.append("PR153S_TARGET_COUNT_MISMATCH")
    pr151_ids = {str(item.get("retrieval_target_id")) for item in upstream.pr151_targets}
    record_ids = {str(_mapping(record).get("target_id")) for record in records}
    if record_ids != pr151_ids:
        failures.append("PR153S_TARGET_IDS_DO_NOT_MATCH_PR151")

    ids = [str(_mapping(record).get("target_id")) for record in records]
    identity_keys = [
        str(_mapping(record).get("canonical_identity_key")) for record in records
    ]
    duplicate_ids = _duplicate_values(ids)
    duplicate_identity_keys = _duplicate_values(identity_keys)
    if duplicate_ids:
        failures.append("PR153S_DUPLICATE_TARGET_IDS: " + ",".join(duplicate_ids))
    if duplicate_identity_keys:
        failures.append(
            "PR153S_DUPLICATE_CANONICAL_IDENTITY_KEYS: "
            + ",".join(duplicate_identity_keys)
        )

    for index, raw_record in enumerate(records):
        record = _mapping(raw_record)
        for key in REQUIRED_RECORD_KEYS:
            if key not in record:
                failures.append(f"PR153S_RECORD_REQUIRED_KEY_MISSING:{index}:{key}")
        lane = str(record.get("closure_lane") or "")
        route = str(record.get("materialization_readiness_route") or "")
        if lane not in tx.CLOSURE_LANES:
            failures.append(f"PR153S_UNKNOWN_CLOSURE_LANE:{record.get('target_id')}:{lane}")
            continue
        if route not in tx.MATERIALIZATION_ROUTES:
            failures.append(
                f"PR153S_UNKNOWN_MATERIALIZATION_ROUTE:{record.get('target_id')}:{route}"
            )
        policy = tx.lane_policy(lane)
        if route != policy["route"]:
            failures.append(
                f"PR153S_ROUTE_DOES_NOT_MATCH_LANE_POLICY:{record.get('target_id')}"
            )
        if record.get("source_authority_class") != policy["authority"]:
            failures.append(
                f"PR153S_AUTHORITY_DOES_NOT_MATCH_LANE_POLICY:{record.get('target_id')}"
            )
        if record.get("required_next_action") != policy["next_action"]:
            failures.append(
                f"PR153S_NEXT_ACTION_DOES_NOT_MATCH_LANE_POLICY:{record.get('target_id')}"
            )
        if record.get("atomicrows_compatibility_class") != policy["atomicrows_class"]:
            failures.append(
                f"PR153S_ATOMICROWS_CLASS_DOES_NOT_MATCH_LANE_POLICY:{record.get('target_id')}"
            )
        for code in _list(record.get("blocker_codes")):
            if code not in tx.BLOCKER_CODES:
                failures.append(
                    f"PR153S_UNKNOWN_BLOCKER_CODE:{record.get('target_id')}:{code}"
                )
        if lane != tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY:
            if record.get("pr154_materialization_allowed") is not False:
                failures.append(
                    f"PR153S_UNAUTHORIZED_MATERIALIZATION_ALLOWED:{record.get('target_id')}"
                )
            if not record.get("pr154_materialization_block_reason"):
                failures.append(
                    f"PR153S_MISSING_BLOCK_REASON:{record.get('target_id')}"
                )
        if record.get("accepted_source_packet_present") is True and lane != (
            tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY
        ):
            failures.append(
                f"PR153S_ACCEPTED_SOURCE_FLAG_WITHOUT_ACCEPTED_LANE:{record.get('target_id')}"
            )
        if record.get("live_order_authority_created") is not False:
            failures.append(
                f"PR153S_LIVE_ORDER_AUTHORITY_CREATED:{record.get('target_id')}"
            )
        if record.get("quantum_forward_compatibility_class") not in (
            tx.QUANTUM_FORWARD_COMPATIBILITY_CLASSES
        ):
            failures.append(
                f"PR153S_UNKNOWN_QUANTUM_CLASS:{record.get('target_id')}"
            )

    closure_summary = _mapping(payload.get("closure_lane_summary"))
    materialization_summary = _mapping(payload.get("materialization_readiness_summary"))
    for lane in tx.CLOSURE_LANES:
        if lane not in closure_summary:
            failures.append(f"PR153S_CLOSURE_SUMMARY_MISSING_LANE:{lane}")
    for route in tx.MATERIALIZATION_ROUTES:
        if route not in materialization_summary:
            failures.append(f"PR153S_MATERIALIZATION_SUMMARY_MISSING_ROUTE:{route}")
    if sum(int(value) for value in closure_summary.values()) != len(records):
        failures.append("PR153S_CLOSURE_SUMMARY_TOTAL_MISMATCH")
    if sum(int(value) for value in materialization_summary.values()) != len(records):
        failures.append("PR153S_MATERIALIZATION_SUMMARY_TOTAL_MISMATCH")
    if closure_summary.get(tx.CLOSURE_UNKNOWN_FAIL_CLOSED) != 0:
        failures.append("PR153S_UNKNOWN_FAIL_CLOSED_TARGETS_PRESENT")

    denominator = _mapping(upstream.pr153_report.get("corrected_denominator_summary"))
    counts = _mapping(payload.get("target_count_summary"))
    expected_pairs = {
        "total_targets_count": denominator.get("total_PR151_targets"),
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
    }
    for key, expected in expected_pairs.items():
        if counts.get(key) != expected:
            failures.append(f"PR153S_TARGET_COUNT_SUMMARY_MISMATCH:{key}")

    if counts.get("canonical_arithmetic_342_all_targets") != counts.get(
        "total_targets_count"
    ):
        failures.append("PR153S_CANONICAL_342_ARITHMETIC_MISMATCH")
    if counts.get("canonical_arithmetic_126_public_external_denominator") != counts.get(
        "true_external_public_source_value_denominator"
    ):
        failures.append("PR153S_CANONICAL_126_ARITHMETIC_MISMATCH")
    if _mapping(payload.get("public_external_source_denominator_receipt")).get(
        "true_external_public_source_value_denominator"
    ) != counts.get("true_external_public_source_value_denominator"):
        failures.append("PR153S_PUBLIC_EXTERNAL_DENOMINATOR_RECEIPT_MISMATCH")

    no_authority = _mapping(payload.get("no_authority_creation_receipt"))
    for key, expected in tx.zero_authority_counters().items():
        if no_authority.get(key) != expected:
            failures.append(f"PR153S_FORBIDDEN_AUTHORITY_COUNTER_NONZERO:{key}")
    if no_authority.get("source_acceptance_created") is not False:
        failures.append("PR153S_SOURCE_ACCEPTANCE_CREATED")
    if no_authority.get("source_retrieval_created") is not False:
        failures.append("PR153S_SOURCE_RETRIEVAL_CREATED")

    atomicrows = _mapping(payload.get("atomicrows_compatibility_receipt"))
    for key in (
        "bundle_created_by_pr153s",
        "bundle_hash_or_sha_authority_created_by_pr153s",
        "bundle_hash_path_referenced_by_pr153s",
        "bundle_data_path_referenced_by_pr153s",
        "row_family_mutated_by_pr153s",
    ):
        if atomicrows.get(key) is not False:
            failures.append(f"PR153S_ATOMICROWS_FORBIDDEN_FLAG_TRUE:{key}")
    if atomicrows.get("row_values_created_by_pr153s") != 0:
        failures.append("PR153S_ATOMICROWS_ROW_VALUES_CREATED")

    quantum = _mapping(payload.get("quantum_forward_compatibility_receipt"))
    for key in (
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "qaoa_execution_created",
        "vqe_execution_created",
        "annealing_execution_created",
        "qubo_or_ising_solver_execution_created",
        "optimizer_arbitration_created",
        "quantum_advantage_claim_created",
    ):
        if quantum.get(key) is not False:
            failures.append(f"PR153S_QUANTUM_EXECUTION_FLAG_TRUE:{key}")

    hidden = _mapping(payload.get("hidden_ambiguity_audit"))
    if hidden.get("committed_report_unknown_fail_closed_count") != 0:
        failures.append("PR153S_HIDDEN_AMBIGUITY_UNKNOWN_COUNT_NONZERO")
    if _list(hidden.get("reconstruction_failures")):
        failures.append("PR153S_RECONSTRUCTION_FAILURES_PRESENT")

    if payload.get("final_status_label") not in tx.FINAL_STATUS_LABELS:
        failures.append("PR153S_FINAL_STATUS_LABEL_INVALID")
    if payload.get("final_status_label") != tx.FINAL_STATUS_READY:
        failures.append("PR153S_FINAL_STATUS_NOT_READY")

    rebuilt = report_builder.build_report(root)
    if report_builder.json_dump(dict(payload)) != report_builder.json_dump(rebuilt):
        failures.append("PR153S_REPORT_STALE_OR_NONDETERMINISTIC")
    failures.extend(_serialized_forbidden_path_failures(payload))
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    report_path = root / tx.REPORT_PATH
    if not report_path.exists():
        return [f"PR153S_REPORT_MISSING: {tx.REPORT_PATH.as_posix()}"]
    try:
        payload = _read_json(report_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"PR153S_REPORT_INVALID: {exc}"]
    return validate_report_payload(payload, root)


def validate(report: Mapping[str, Any], repo_root: Path | str) -> list[str]:
    return validate_report_payload(report, repo_root)
