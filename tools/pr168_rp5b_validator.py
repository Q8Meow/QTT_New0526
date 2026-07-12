#!/usr/bin/env python3
"""Validator for PR168-RP5B active registry cleanup artifacts."""

from __future__ import annotations

from collections import Counter
import subprocess
from typing import Any

from tools.pr168_rp5b_config import (
    DELETE_ACTIONS,
    HARD_FAIL_PHYSICAL_PATH_LENGTH,
    HARD_ZERO_FINAL_SUMMARY_FIELDS,
    PROTECTED_CLASSIFICATIONS,
    REPORT_NAMES,
    REPO_ROOT,
    ROW_SHARDS,
    ZERO_DELETION_RESULT_NOTE,
    generated_ref,
    manifest_path_for_shard,
    normalize_repo_path,
    report_path,
    shard_path,
)
from tools.pr168_rp5b_report_writer import read_json, read_jsonl


def _deleted_files_from_git_output(args: list[str], output: str) -> set[str]:
    deleted: set[str] = set()
    for line in output.splitlines():
        if not line:
            continue
        if args[1] == "diff" and line.startswith("D"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                deleted.add(normalize_repo_path(parts[1]))
        if args[1] == "status" and line[:2] in {" D", "D ", "DD"}:
            deleted.add(normalize_repo_path(line[3:]))
    return deleted


def _git_deleted_files() -> set[str]:
    deleted: set[str] = set()
    for args in (
        ["git", "diff", "--name-status", "--diff-filter=D", "origin/main...HEAD"],
        ["git", "status", "--short", "--untracked-files=all"],
    ):
        completed = subprocess.run(
            args,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            continue
        deleted.update(_deleted_files_from_git_output(args, completed.stdout))
    return deleted


def _deletion_failures(
    candidate_rows: list[dict[str, Any]],
    verification_rows: list[dict[str, Any]],
    preservation_rows: list[dict[str, Any]],
    deleted_rows: list[dict[str, Any]],
    actual_deleted: set[str],
) -> list[str]:
    failures: list[str] = []
    if len(candidate_rows) != len(verification_rows):
        failures.append("CANDIDATE_VERIFICATION_COUNT_MISMATCH")

    candidate_path_counts = Counter(
        normalize_repo_path(str(row["file_path"])) for row in candidate_rows
    )
    verification_path_counts = Counter(
        normalize_repo_path(str(row["file_path"])) for row in verification_rows
    )
    candidate_paths = set(candidate_path_counts)
    verification_paths = set(verification_path_counts)
    if candidate_paths != verification_paths:
        failures.append(
            "CANDIDATE_VERIFICATION_PATH_MISMATCH:"
            f"candidate_only={sorted(candidate_paths - verification_paths)} "
            f"verification_only={sorted(verification_paths - candidate_paths)}"
        )
    candidate_duplicates = sorted(
        path for path, count in candidate_path_counts.items() if count != 1
    )
    verification_duplicates = sorted(
        path for path, count in verification_path_counts.items() if count != 1
    )
    if candidate_duplicates:
        failures.append(f"CANDIDATE_DUPLICATE_PATHS:{candidate_duplicates}")
    if verification_duplicates:
        failures.append(f"VERIFICATION_DUPLICATE_PATHS:{verification_duplicates}")
    if candidate_path_counts != verification_path_counts:
        failures.append(
            "CANDIDATE_VERIFICATION_PATH_MULTIPLICITY_MISMATCH:"
            f"candidate={sorted(candidate_path_counts.items())} "
            f"verification={sorted(verification_path_counts.items())}"
        )

    for row in candidate_rows[:100]:
        if row.get("rp5b_reverification_required_flag") is not True:
            failures.append(f"CANDIDATE_REVERIFY_FLAG_FALSE:{row.get('file_path')}")

    verification_by_file = {
        normalize_repo_path(str(row["file_path"])): row for row in verification_rows
    }
    manifest_deleted = {
        normalize_repo_path(str(row.get("file_path")))
        for row in deleted_rows
        if row.get("git_action") == "DELETE"
    }
    for row in verification_rows:
        file_path = normalize_repo_path(str(row["file_path"]))
        selected_for_deletion = (
            row.get("final_action") in DELETE_ACTIONS or file_path in manifest_deleted
        )
        if (
            row.get("rp5a_classification") in PROTECTED_CLASSIFICATIONS
            and selected_for_deletion
        ):
            failures.append(f"PROTECTED_FILE_SELECTED_FOR_DELETE:{file_path}")
        if selected_for_deletion and row.get(
            "contains_unique_qku_formula_identity_now_flag"
        ):
            matching = [
                preserve
                for preserve in preservation_rows
                if normalize_repo_path(str(preserve.get("source_file_path", ""))) == file_path
            ]
            if not matching:
                failures.append(f"DELETED_IDENTITY_WITHOUT_PRESERVATION:{file_path}")
        if selected_for_deletion and not row.get("safe_to_delete_now_flag"):
            failures.append(f"DELETE_ACTION_WITHOUT_SAFE_FLAG:{file_path}")

    governed_paths = candidate_paths | verification_paths
    governed_actual_deleted = {
        normalize_repo_path(path) for path in actual_deleted
    } & governed_paths
    if manifest_deleted != governed_actual_deleted:
        failures.append(
            "DELETED_MANIFEST_GIT_MISMATCH:"
            f"manifest={sorted(manifest_deleted)} git={sorted(governed_actual_deleted)}"
        )
    for path in sorted(manifest_deleted):
        source_row = verification_by_file.get(path, {})
        if not source_row:
            failures.append(f"DELETED_WITHOUT_VERIFICATION:{path}")
            continue
        if source_row.get("final_action") not in DELETE_ACTIONS:
            failures.append(
                f"DELETED_WITHOUT_DELETE_ACTION:{path}:"
                f"{source_row.get('final_action')}"
            )
    return failures


def _failures() -> list[str]:
    failures: list[str] = []
    for name in REPORT_NAMES:
        if not report_path(name).is_file():
            failures.append(f"MISSING_REPORT:{name}")
    for key in ROW_SHARDS:
        path = shard_path(key)
        manifest = manifest_path_for_shard(path)
        if not path.is_file():
            failures.append(f"MISSING_SHARD:{generated_ref(path)}")
        if not manifest.is_file():
            failures.append(f"MISSING_MANIFEST:{generated_ref(manifest)}")
        if path.is_file() and manifest.is_file():
            rows = read_jsonl(path)
            payload = read_json(manifest)
            if payload.get("row_count") != len(rows):
                failures.append(f"MANIFEST_ROW_COUNT_MISMATCH:{generated_ref(path)}")
            if payload.get("row_count_within_bound_flag") is not True:
                failures.append(f"MANIFEST_ROW_CAP_EXCEEDED:{generated_ref(path)}")
    if failures:
        return failures

    preflight = read_json(report_path("PR168_RP5B_Preflight.report.json"))
    if not preflight.get("pr241_merged_preflight_passed"):
        failures.append("PR241_NOT_VERIFIED_MERGED")
    if not preflight.get("pr240_closed_not_merged_preflight_passed"):
        failures.append("PR240_NOT_VERIFIED_CLOSED_UNMERGED")

    integrity = read_json(report_path("PR168_RP5B_RP5AInputIntegrity.report.json"))
    if not integrity.get("rp5a_input_integrity_passed"):
        failures.append("RP5A_INPUT_INTEGRITY_FAILED")
    if not integrity.get("rp5a_no_deletion_zero_flag"):
        failures.append("RP5A_NO_DELETION_PROOF_NOT_ZERO")

    candidate_rows = read_jsonl(shard_path("cleanup_candidate_rows"))
    verification_rows = read_jsonl(shard_path("safe_deletion_verification_rows"))
    preservation_rows = read_jsonl(shard_path("qku_formula_identity_preservation_rows"))
    registry_rows = read_jsonl(shard_path("active_artifact_registry_rows"))
    semantic_rows = read_jsonl(shard_path("legacy_semantic_supersession_rows"))
    no_raw_rows = read_jsonl(shard_path("no_raw_legacy_decision_authority_rows"))
    deleted_rows = read_jsonl(shard_path("deleted_from_active_tree_rows"))
    keep_rows = read_jsonl(shard_path("legacy_keep_reason_rows"))
    validation_scope_rows = read_jsonl(shard_path("validation_scope_reduction_rows"))
    path_rows = read_jsonl(shard_path("path_audit_rows"))
    agent_rows = read_jsonl(shard_path("agent_route_preservation_rows"))
    final_summary = read_json(report_path("PR168_RP5B_FinalSummary.report.json"))
    no_raw_report = read_json(report_path("PR168_RP5B_NoRawLegacyDecisionAuthority.report.json"))

    failures.extend(
        _deletion_failures(
            candidate_rows,
            verification_rows,
            preservation_rows,
            deleted_rows,
            _git_deleted_files(),
        )
    )

    if not keep_rows and verification_rows:
        failures.append("KEEP_REASON_LEDGER_EMPTY")
    if len(registry_rows) < 10:
        failures.append("ACTIVE_REGISTRY_TOO_SMALL")
    for row in registry_rows:
        if not row.get("downstream_refs"):
            failures.append(f"ACTIVE_REGISTRY_MISSING_DOWNSTREAM:{row.get('artifact_id')}")
        if str(row.get("no_orphan_status", "")).startswith("MISSING"):
            failures.append(f"ACTIVE_REGISTRY_ORPHAN:{row.get('artifact_path')}")
        if row.get("active_status", "").startswith("LEGACY") and "TRADING_DECISION_DIRECT" not in row.get("forbidden_consumers", []):
            failures.append(f"LEGACY_REGISTRY_ROW_ALLOWS_DIRECT_TRADING:{row.get('artifact_id')}")

    interpretations = {row.get("canonical_future_interpretation") for row in semantic_rows}
    required_interpretations = {
        "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING",
        "QKU_EXECUTION_ROUTE_OR_TRADE_PLAN_BINDING",
        "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY",
        "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY",
        "PRESERVED_NEEDS_EXECUTION_CONTRACT",
        "AUTHORITY_BOUNDARY_LABEL_ONLY_UNTIL_LAUNCH_GATES",
    }
    missing_interpretations = sorted(required_interpretations - interpretations)
    if missing_interpretations:
        failures.append(f"SEMANTIC_SUPERSESSION_MISSING:{missing_interpretations}")
    if no_raw_report.get("raw_legacy_decision_authority_violation_count") != 0:
        failures.append("RAW_LEGACY_DECISION_AUTHORITY_VIOLATIONS")
    if not no_raw_rows:
        failures.append("NO_RAW_LEGACY_RULE_ROWS_EMPTY")

    for row in validation_scope_rows:
        if not row.get("replacement_validator_refs"):
            failures.append(f"VALIDATION_SCOPE_NO_REPLACEMENT:{row.get('row_id')}")
    if not agent_rows or not all(row.get("preserved_flag") for row in agent_rows):
        failures.append("AGENT_ROUTE_PRESERVATION_FAILED")
    for row in path_rows:
        if int(row.get("physical_path_length", 0)) >= HARD_FAIL_PHYSICAL_PATH_LENGTH:
            failures.append(f"PATH_HARD_FAIL:{row.get('file_path')}")

    for field in HARD_ZERO_FINAL_SUMMARY_FIELDS:
        if final_summary.get(field) != 0:
            failures.append(f"FINAL_HARD_ZERO_NONZERO:{field}:{final_summary.get(field)}")
    if final_summary.get("source_files_deleted_count") != 0:
        failures.append("SOURCE_FILES_DELETED")
    if final_summary.get("test_files_deleted_count") != 0:
        failures.append("TEST_FILES_DELETED")
    if final_summary.get("validator_files_deleted_count") != 0:
        failures.append("VALIDATOR_FILES_DELETED")
    if final_summary.get("raw_legacy_decision_authority_violation_count") != 0:
        failures.append("FINAL_RAW_LEGACY_VIOLATIONS")
    if final_summary.get("unique_qku_formula_identity_lost_count") != 0:
        failures.append("UNIQUE_IDENTITY_LOST")
    if final_summary.get("files_deleted_count") == 0 and final_summary.get("files_archived_by_registry_count") == 0:
        if final_summary.get("cleanup_result_note") != ZERO_DELETION_RESULT_NOTE:
            failures.append("FINAL_SUMMARY_MISSING_ZERO_DELETION_NOTE")
    return failures


def run_validation() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise AssertionError("\n".join(failures))
    return {
        "validation": "PR168_RP5B_ACTIVE_REGISTRY_SAFE_CLEANUP_OK",
        "reports_checked": len(REPORT_NAMES),
        "row_shards_checked": len(ROW_SHARDS),
    }
