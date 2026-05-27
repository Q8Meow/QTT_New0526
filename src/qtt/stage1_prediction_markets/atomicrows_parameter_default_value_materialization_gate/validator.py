"""PR154 repository validator."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from tools.ci_branch_context import (
    current_branch_context,
    is_explicit_downstream_repair_changed_path,
    is_pr_or_later_branch,
)

from src.qtt.stage1_prediction_markets.pr153s_source_value_capture_closure_classifier import (
    taxonomy as pr153s_tx,
)

from . import report as report_builder
from . import taxonomy as tx


REQUIRED_REPORT_KEYS = (
    "report_id",
    "validator_marker",
    "semantic_pr_label",
    "purpose",
    "consumed_artifacts_read_receipt",
    "orchestration_alignment_receipt",
    "pr153s_consumption_receipt",
    "official_candidate_fast_lane_acceptance_receipt",
    "owner_internal_policy_materialization_receipt",
    "owner_route_materialization_receipt",
    "authorized_value_source_manifest_receipt",
    "source_value_authority_receipt",
    "materialization_count_summary",
    "materialization_decision_summary",
    "blocked_materialization_summary",
    "completion_path_summary",
    "accepted_source_materialization_receipt",
    "atomicrows_compatibility_receipt",
    "agent_consumption_readiness_receipt",
    "quantum_forward_compatibility_receipt",
    "latency_and_day1_launch_readiness_receipt",
    "no_authority_creation_receipt",
    "hidden_ambiguity_audit",
    "deterministic_generation_receipt",
    "per_target_materialization_records",
    "final_status_label",
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
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sorted(value for value, count in counts.items() if count > 1)


def _git_stdout(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _changed_paths(repo_root: Path) -> list[str]:
    status_rc, status_out, _status_err = _git_stdout(
        repo_root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )
    if status_rc != 0:
        return ["<git-status-unavailable>"]
    paths: list[str] = []
    records = [record for record in status_out.split("\0") if record]
    index = 0
    while index < len(records):
        line = records[index]
        if not line.strip():
            index += 1
            continue
        code = line[:2]
        path = line[3:] if len(line) > 3 and line[2] == " " else line[2:].strip()
        paths.append(path.replace("\\", "/"))
        index += 2 if code[:1] in {"R", "C"} or code[1:] in {"R", "C"} else 1
    return sorted(set(paths))


def _branch_allows_pr154_changed_paths(branch: str) -> bool:
    return branch == tx.PR154_BRANCH or is_pr_or_later_branch(
        branch,
        154,
        allow_main=False,
        allow_repair=False,
    )


def _is_allowed_changed_path(path: str, branch: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized == ".tmp" or normalized.startswith(".tmp/"):
        return True
    if is_explicit_downstream_repair_changed_path(branch, normalized):
        return True
    return normalized in tx.CHANGED_PATHS and _branch_allows_pr154_changed_paths(branch)


def _forbidden_bundle_data_path() -> str:
    return "AtomicRows.bundle." + "jsonl"


def _forbidden_bundle_hash_path() -> str:
    return "AtomicRows.bundle." + "sha" + "256"


def _serialized_forbidden_failures(payload: Mapping[str, Any]) -> list[str]:
    serialized = report_builder.json_dump(payload)
    failures: list[str] = []
    if _forbidden_bundle_data_path() in serialized:
        failures.append("PR154_FORBIDDEN_ATOMICROWS_BUNDLE_DATA_PATH_REFERENCED")
    if _forbidden_bundle_hash_path() in serialized:
        failures.append("PR154_FORBIDDEN_ATOMICROWS_BUNDLE_HASH_PATH_REFERENCED")
    return failures


def _validate_changed_paths(repo_root: Path) -> list[str]:
    branch = current_branch_context(repo_root).branch
    failures: list[str] = []
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR154_GIT_STATUS_UNAVAILABLE")
            continue
        if not _is_allowed_changed_path(path, branch):
            failures.append(f"PR154_CHANGED_PATH_OUT_OF_SCOPE: {path}")
        if path == "docs/master_plan/QTT_MasterPlan_Current.md":
            failures.append("PR154_MASTER_PLAN_MUTATION_DETECTED")
        if path == "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl":
            failures.append("PR154_ATOMICROWS_BUNDLE_MUTATION_DETECTED")
        if path == "docs/master_plan/atomic_rows/AtomicRows.bundle." + "sha" + "256":
            failures.append("PR154_ATOMICROWS_BUNDLE_HASH_AUTHORITY_DETECTED")
    return sorted(set(failures))


def validate_report_payload(
    payload: Mapping[str, Any],
    repo_root: Path | str,
) -> list[str]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    for key in REQUIRED_REPORT_KEYS:
        if key not in payload:
            failures.append(f"PR154_REQUIRED_REPORT_KEY_MISSING: {key}")

    if payload.get("report_id") != tx.REPORT_ID:
        failures.append("PR154_REPORT_ID_MISMATCH")
    if payload.get("validator_marker") != tx.VALIDATOR_MARKER:
        failures.append("PR154_VALIDATOR_MARKER_MISMATCH")
    if payload.get("semantic_pr_label") != tx.SEMANTIC_PR_LABEL:
        failures.append("PR154_SEMANTIC_LABEL_MISMATCH")

    pr153s_report = _read_json(root / pr153s_tx.REPORT_PATH)
    pr153s_records = _list(pr153s_report.get("per_target_closure_records"))
    pr153s_ids = {str(_mapping(record).get("target_id")) for record in pr153s_records}
    records = _list(payload.get("per_target_materialization_records"))
    source_ids = [str(_mapping(record).get("source_pr153s_target_id")) for record in records]
    record_ids = [str(_mapping(record).get("pr154_record_id")) for record in records]
    if len(records) != len(pr153s_records):
        failures.append("PR154_RECORD_COUNT_MISMATCH")
    if set(source_ids) != pr153s_ids:
        failures.append("PR154_SOURCE_IDS_DO_NOT_MATCH_PR153S")
    duplicate_record_ids = _duplicate_values(record_ids)
    duplicate_source_ids = _duplicate_values(source_ids)
    if duplicate_record_ids:
        failures.append("PR154_DUPLICATE_RECORD_IDS: " + ",".join(duplicate_record_ids))
    if duplicate_source_ids:
        failures.append("PR154_DUPLICATE_SOURCE_PR153S_TARGET_IDS: " + ",".join(duplicate_source_ids))

    sorted_records = sorted(records, key=lambda row: (
        str(_mapping(row).get("platform_scope") or ""),
        str(_mapping(row).get("target_field_path") or ""),
        str(_mapping(row).get("source_pr153s_target_id") or ""),
        str(_mapping(row).get("pr154_record_id") or ""),
    ))
    if records != sorted_records:
        failures.append("PR154_RECORDS_NOT_SORTED")

    for index, raw_record in enumerate(records):
        record = _mapping(raw_record)
        for key in tx.REQUIRED_RECORD_FIELDS:
            if key not in record:
                failures.append(f"PR154_RECORD_REQUIRED_KEY_MISSING:{index}:{key}")
        if record.get("acceptance_decision") not in tx.ACCEPTANCE_DECISIONS:
            failures.append(
                f"PR154_ACCEPTANCE_DECISION_INVALID:{record.get('pr154_record_id')}"
            )
        if record.get("materialization_decision") not in tx.MATERIALIZATION_DECISIONS:
            failures.append(
                f"PR154_MATERIALIZATION_DECISION_INVALID:{record.get('pr154_record_id')}"
            )
        if record.get("materialized_value_type") not in tx.VALUE_TYPES:
            failures.append(f"PR154_VALUE_TYPE_INVALID:{record.get('pr154_record_id')}")
        if record.get("materialized_value_source_class") not in tx.VALUE_SOURCE_CLASSES:
            failures.append(f"PR154_VALUE_SOURCE_CLASS_INVALID:{record.get('pr154_record_id')}")
        if record.get("materialized_value_authority_class") not in tx.AUTHORITY_CLASSES:
            failures.append(f"PR154_AUTHORITY_CLASS_INVALID:{record.get('pr154_record_id')}")
        if record.get("atomicrows_compatibility_class") not in tx.ATOMICROWS_COMPATIBILITY_CLASSES:
            failures.append(f"PR154_ATOMICROWS_CLASS_INVALID:{record.get('pr154_record_id')}")
        if record.get("agent_consumption_readiness_class") not in tx.AGENT_READINESS_CLASSES:
            failures.append(f"PR154_AGENT_READINESS_INVALID:{record.get('pr154_record_id')}")
        if record.get("quantum_forward_compatibility_class") not in tx.QUANTUM_FORWARD_CLASSES:
            failures.append(f"PR154_QUANTUM_CLASS_INVALID:{record.get('pr154_record_id')}")

        materialized = record.get("materialization_allowed") is True
        if materialized:
            if record.get("materialized_value") is None:
                failures.append(f"PR154_MATERIALIZED_RECORD_NULL_VALUE:{record.get('pr154_record_id')}")
            if record.get("materialized_value_authority_class") == tx.AUTHORITY_BLOCKED:
                failures.append(f"PR154_MATERIALIZED_RECORD_BLOCKED_AUTHORITY:{record.get('pr154_record_id')}")
            if record.get("agent_consumption_readiness_class") != tx.AGENT_CONSUMABLE_DEFAULT_READY:
                failures.append(f"PR154_MATERIALIZED_RECORD_NOT_AGENT_READY:{record.get('pr154_record_id')}")
        else:
            if record.get("materialized_value") is not None:
                failures.append(f"PR154_BLOCKED_RECORD_NON_NULL_VALUE:{record.get('pr154_record_id')}")
            if record.get("materialized_value_type") != tx.VALUE_TYPE_NONE:
                failures.append(f"PR154_BLOCKED_RECORD_VALUE_TYPE_NOT_NONE:{record.get('pr154_record_id')}")
            if record.get("materialized_value_source_class") != tx.VALUE_SOURCE_NONE:
                failures.append(f"PR154_BLOCKED_RECORD_VALUE_SOURCE_NOT_NONE:{record.get('pr154_record_id')}")
            if record.get("materialized_value_authority_class") != tx.AUTHORITY_BLOCKED:
                failures.append(f"PR154_BLOCKED_RECORD_AUTHORITY_NOT_BLOCKED:{record.get('pr154_record_id')}")
            if not record.get("materialization_block_code"):
                failures.append(f"PR154_BLOCKED_RECORD_MISSING_BLOCK_CODE:{record.get('pr154_record_id')}")
            if not _list(record.get("missing_fields")):
                failures.append(f"PR154_BLOCKED_RECORD_MISSING_FIELDS_EMPTY:{record.get('pr154_record_id')}")
            for field in _list(record.get("missing_fields")):
                if field not in tx.MISSING_FIELD_CODES:
                    failures.append(f"PR154_UNKNOWN_MISSING_FIELD:{record.get('pr154_record_id')}:{field}")
            for key in (
                "required_next_task",
                "required_next_pr_or_phase",
                "responsible_authority",
                "required_input_artifact",
                "exact_unblock_condition",
                "materialization_retry_route",
            ):
                if not record.get(key):
                    failures.append(f"PR154_BLOCKED_COMPLETION_FIELD_EMPTY:{record.get('pr154_record_id')}:{key}")
            if not _list(record.get("codex_actionable_completion_steps")):
                failures.append(f"PR154_BLOCKED_CODEX_STEPS_EMPTY:{record.get('pr154_record_id')}")
            if record.get("agent_consumption_readiness_class") == tx.AGENT_CONSUMABLE_DEFAULT_READY:
                failures.append(f"PR154_BLOCKED_RECORD_AGENT_READY:{record.get('pr154_record_id')}")

        for field in (
            "atomicrows_bundle_mutation_created",
            "atomicrows_bundle_hash_authority_created",
            "live_pretrade_consumption_allowed",
            "runtime_live_order_authority_created",
            "profit_evidence_created",
        ):
            if record.get(field) is not False:
                failures.append(f"PR154_FORBIDDEN_RECORD_FLAG_TRUE:{record.get('pr154_record_id')}:{field}")

    counts = _mapping(payload.get("materialization_count_summary"))
    if counts.get("total_pr154_records") != len(records):
        failures.append("PR154_COUNT_SUMMARY_TOTAL_MISMATCH")
    if counts.get("materialized_value_count", 0) <= 0:
        failures.append("PR154_EXPECTED_POSITIVE_MATERIALIZATION_COUNT")
    if counts.get("accepted_official_source_materialized_count") != 92:
        failures.append("PR154_EXPECTED_92_OFFICIAL_CANDIDATES_MATERIALIZED")
    if counts.get("owner_internal_materialized_count") != 138:
        failures.append("PR154_EXPECTED_138_INTERNAL_POLICY_DEFAULTS_MATERIALIZED")
    if counts.get("blocked_pending_pr153r_completion_count") != 34:
        failures.append("PR154_EXPECTED_34_PR153R_BLOCKED")
    if counts.get("blocked_pending_split_reclassification_count") != 33:
        failures.append("PR154_EXPECTED_33_SPLIT_BLOCKED")
    if counts.get("blocked_pending_private_doc_attestation_count") != 6:
        failures.append("PR154_EXPECTED_6_PRIVATE_DOC_BLOCKED")
    if counts.get("blocked_pending_owner_route_count") != 39:
        failures.append("PR154_EXPECTED_39_OWNER_ROUTE_BLOCKED")
    for key in (
        "runtime_materialized_count",
        "replay_paper_materialized_count",
        "quantum_execution_materialized_count",
        "live_order_profit_materialized_count",
    ):
        if counts.get(key) != 0:
            failures.append(f"PR154_FORBIDDEN_MATERIALIZED_COUNT_NONZERO:{key}")

    hidden = _mapping(payload.get("hidden_ambiguity_audit"))
    if hidden.get("committed_report_unknown_fail_closed_count") != 0:
        failures.append("PR154_UNKNOWN_FAIL_CLOSED_RECORDS_PRESENT")

    atomicrows = _mapping(payload.get("atomicrows_compatibility_receipt"))
    for key in (
        "bundle_created_by_pr154",
        "bundle_hash_or_sha_authority_created_by_pr154",
        "bundle_hash_path_referenced_by_pr154",
        "bundle_data_path_referenced_by_pr154",
        "row_family_mutated_by_pr154",
    ):
        if atomicrows.get(key) is not False:
            failures.append(f"PR154_ATOMICROWS_FORBIDDEN_FLAG_TRUE:{key}")

    no_authority = _mapping(payload.get("no_authority_creation_receipt"))
    for key, expected in tx.zero_authority_counters().items():
        if no_authority.get(key) != expected:
            failures.append(f"PR154_FORBIDDEN_AUTHORITY_COUNTER_NONZERO:{key}")
    for key in (
        "source_retrieval_created",
        "source_acceptance_created_as_separate_later_pr_requirement",
        "connector_semantic_binding_created",
        "accepted_source_packet_created_by_pr154",
        "atomicrows_bundle_data_path_referenced",
        "atomicrows_bundle_hash_path_referenced",
        "source_evidence_digest_metadata_materialized_as_trading_default",
    ):
        if no_authority.get(key) is not False:
            failures.append(f"PR154_NO_AUTHORITY_FLAG_TRUE:{key}")

    quantum = _mapping(payload.get("quantum_forward_compatibility_receipt"))
    for key in (
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "quantum_optimizer_execution_created",
        "qaoa_execution_created",
        "vqe_execution_created",
        "annealing_execution_created",
        "qubo_or_ising_solver_execution_created",
        "optimizer_arbitration_created",
        "quantum_advantage_claim_created",
    ):
        if quantum.get(key) is not False:
            failures.append(f"PR154_QUANTUM_EXECUTION_FLAG_TRUE:{key}")

    if payload.get("final_status_label") != tx.FINAL_STATUS_READY:
        failures.append("PR154_FINAL_STATUS_NOT_READY")

    rebuilt = report_builder.build_report(root)
    if report_builder.json_dump(dict(payload)) != report_builder.json_dump(rebuilt):
        failures.append("PR154_REPORT_STALE_OR_NONDETERMINISTIC")
    failures.extend(_serialized_forbidden_failures(payload))
    return sorted(set(failures))


def validate_repository_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    report_path = root / tx.REPORT_PATH
    if not report_path.exists():
        return [f"PR154_REPORT_MISSING: {tx.REPORT_PATH.as_posix()}"]
    try:
        payload = _read_json(report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"PR154_REPORT_INVALID: {exc}"]
    failures = validate_report_payload(payload, root)
    failures.extend(_validate_changed_paths(root))
    return sorted(set(failures))


def validate(report: Mapping[str, Any], repo_root: Path | str) -> list[str]:
    return validate_report_payload(report, repo_root)
