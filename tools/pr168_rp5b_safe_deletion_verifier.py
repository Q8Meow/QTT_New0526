#!/usr/bin/env python3
"""Conservative RP5B cleanup candidate and deletion verifier."""

from __future__ import annotations

from typing import Any

from tools.pr168_rp5b_config import (
    ARCHIVE_ACTIONS,
    CLEANUP_CANDIDATE_CLASSIFICATIONS,
    DELETE_ACTIONS,
    FINAL_ACTIONS,
    PROTECTED_CLASSIFICATIONS,
    REPO_ROOT,
    classify_file_kind,
    is_generated_artifact,
    normalize_repo_path,
)


def _by_path(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {normalize_repo_path(row.get(key, "")): row for row in rows if row.get(key)}


def build_cleanup_candidate_rows(
    delete_rows: list[dict[str, Any]],
    consumer_rows: list[dict[str, Any]],
    validation_rows: list[dict[str, Any]],
    identity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    consumers = _by_path(consumer_rows, "file_path")
    validators = _by_path(validation_rows, "file_path_or_prefix")
    identities = _by_path(identity_rows, "file_path")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(delete_rows, start=1):
        file_path = normalize_repo_path(str(row.get("file_path", "")))
        classification = str(row.get("classification", "UNCLEAR_DO_NOT_DELETE"))
        consumer = consumers.get(file_path, {})
        validation = validators.get(file_path, {})
        identity = identities.get(file_path, {})
        rows.append(
            {
                "row_id": f"RP5B_CLEANUP_CANDIDATE_{index:07d}",
                "file_path": file_path,
                "rp5a_classification": classification,
                "rp5a_refs": [row.get("row_id")],
                "file_kind": classify_file_kind(file_path),
                "matched_stale_terms": row.get("stale_term_refs", []),
                "active_consumer_status_from_rp5a": "ACTIVE_CONSUMER" if consumer.get("active_consumer_flag") else "NO_ACTIVE_CONSUMER_DETECTED",
                "validation_dependency_status_from_rp5a": str(validation.get("validation_dependency_type", "NONE")),
                "identity_dependency_status_from_rp5a": "UNIQUE_IDENTITY_POSSIBLE" if identity.get("unique_identity_possible_flag") else "NO_UNIQUE_IDENTITY_DETECTED",
                "cleanup_candidate_scope": "RP5B_DELETION_OR_ARCHIVE_CANDIDATE" if classification in CLEANUP_CANDIDATE_CLASSIFICATIONS else "RP5B_PROTECTED_NON_DELETION_LEDGER",
                "rp5b_reverification_required_flag": True,
            }
        )
    return rows


def _final_action_for(
    *,
    classification: str,
    file_kind: str,
    file_exists: bool,
    file_is_generated: bool,
    file_is_source_code: bool,
    file_is_test: bool,
    file_is_validator: bool,
    active_consumer: bool,
    validation_dependency: bool,
    unique_identity: bool,
) -> str:
    if classification == "UNCLEAR_DO_NOT_DELETE":
        return "UNCLEAR_DO_NOT_DELETE"
    if classification == "KEEP_ACTIVE_CONSUMER" or active_consumer:
        return "KEEP_ACTIVE_CONSUMER"
    if classification == "KEEP_VALIDATION_DEPENDENCY" or validation_dependency:
        return "KEEP_VALIDATION_DEPENDENCY"
    if classification == "KEEP_UNIQUE_QKU_FORMULA_SOURCE" or unique_identity:
        return "KEEP_UNIQUE_IDENTITY_SOURCE"
    if classification == "KEEP_TEST_FIXTURE" or file_is_test:
        return "KEEP_TEST_FIXTURE"
    if file_is_source_code or file_is_validator:
        return "KEEP_SOURCE_CODE"
    if classification == "REWRITE_CONSUMER_FIRST":
        return "REWRITE_CONSUMER_FIRST"
    if classification == "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM":
        return "DEFER_TO_RP5C_IDENTITY_RECLAIM"
    if classification == "ARCHIVE_NO_VALIDATION_SCAN" and file_exists and file_is_generated:
        return "ARCHIVE_NO_VALIDATION_SCAN_NOW"
    if classification == "DELETE_FROM_ACTIVE_TREE_SAFE" and file_exists and file_is_generated:
        return "DELETE_ACTIVE_TREE_NOW"
    if classification == "KEEP_LEGACY_SUMMARY_ONLY":
        return "DEFER_TO_RP5D_EXECUTABILITY" if not file_is_generated else "ARCHIVE_NO_VALIDATION_SCAN_NOW"
    if file_kind == "UNKNOWN":
        return "UNCLEAR_DO_NOT_DELETE"
    return "UNCLEAR_DO_NOT_DELETE"


def build_safe_deletion_verification_rows(
    candidate_rows: list[dict[str, Any]],
    consumer_rows: list[dict[str, Any]],
    validation_rows: list[dict[str, Any]],
    identity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    consumers = _by_path(consumer_rows, "file_path")
    validators = _by_path(validation_rows, "file_path_or_prefix")
    identities = _by_path(identity_rows, "file_path")
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_rows, start=1):
        file_path = normalize_repo_path(candidate["file_path"])
        path = REPO_ROOT / file_path
        file_kind = classify_file_kind(file_path)
        consumer = consumers.get(file_path, {})
        validation = validators.get(file_path, {})
        identity = identities.get(file_path, {})
        file_exists = path.exists()
        file_is_generated = is_generated_artifact(file_path)
        file_is_source_code = file_kind == "TOOL_SOURCE"
        file_is_test = file_kind == "TEST_SOURCE"
        file_is_validator = file_kind == "VALIDATOR"
        active_consumer = bool(consumer.get("active_consumer_flag"))
        validation_dependency = str(validation.get("validation_dependency_type", "NONE")) != "NONE"
        unique_identity = bool(identity.get("unique_identity_possible_flag")) or candidate.get("rp5a_classification") == "KEEP_UNIQUE_QKU_FORMULA_SOURCE"
        final_action = _final_action_for(
            classification=str(candidate["rp5a_classification"]),
            file_kind=file_kind,
            file_exists=file_exists,
            file_is_generated=file_is_generated,
            file_is_source_code=file_is_source_code,
            file_is_test=file_is_test,
            file_is_validator=file_is_validator,
            active_consumer=active_consumer,
            validation_dependency=validation_dependency,
            unique_identity=unique_identity,
        )
        if final_action not in FINAL_ACTIONS:
            final_action = "UNCLEAR_DO_NOT_DELETE"
        identity_preservation_required = final_action in DELETE_ACTIONS and unique_identity
        identity_preservation_completed = False
        safe_to_delete = (
            final_action in DELETE_ACTIONS
            and file_exists
            and file_is_generated
            and not active_consumer
            and not validation_dependency
            and not unique_identity
            and not file_is_source_code
            and not file_is_test
            and not file_is_validator
        )
        safe_to_archive = (
            final_action in ARCHIVE_ACTIONS
            and file_exists
            and file_is_generated
            and not active_consumer
            and not validation_dependency
            and not unique_identity
            and not file_is_source_code
            and not file_is_test
            and not file_is_validator
        )
        if final_action in DELETE_ACTIONS and not safe_to_delete:
            final_action = "UNCLEAR_DO_NOT_DELETE" if str(candidate["rp5a_classification"]) in PROTECTED_CLASSIFICATIONS else "DEFER_TO_RP5C_IDENTITY_RECLAIM"
        rows.append(
            {
                "row_id": f"RP5B_SAFE_DELETE_{index:07d}",
                "file_path": file_path,
                "rp5a_classification": candidate["rp5a_classification"],
                "rp5a_refs": candidate.get("rp5a_refs", []),
                "file_exists_now_flag": file_exists,
                "file_is_generated_flag": file_is_generated,
                "file_is_source_code_flag": file_is_source_code,
                "file_is_test_flag": file_is_test,
                "file_is_validator_flag": file_is_validator,
                "active_consumer_found_now_flag": active_consumer,
                "validation_dependency_found_now_flag": validation_dependency,
                "contains_unique_qku_formula_identity_now_flag": unique_identity,
                "identity_preservation_required_flag": identity_preservation_required,
                "identity_preservation_completed_flag": identity_preservation_completed,
                "safe_to_delete_now_flag": safe_to_delete,
                "safe_to_archive_now_flag": safe_to_archive,
                "safe_to_remove_from_validation_now_flag": bool((safe_to_delete or safe_to_archive) and not validation_dependency),
                "operator_review_required_flag": str(candidate["rp5a_classification"]) == "UNCLEAR_DO_NOT_DELETE",
                "final_action": final_action,
            }
        )
    return rows


def build_legacy_keep_reason_rows(verification_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(verification_rows, start=1):
        if row["final_action"] in DELETE_ACTIONS:
            continue
        future_route = "NONE"
        if row["final_action"] == "KEEP_UNIQUE_IDENTITY_SOURCE":
            future_route = "PR168_RP5C"
        elif row["final_action"] == "DEFER_TO_RP5C_IDENTITY_RECLAIM":
            future_route = "PR168_RP5C"
        elif row["final_action"] == "DEFER_TO_RP5D_EXECUTABILITY":
            future_route = "PR168_RP5D"
        elif row["final_action"] == "UNCLEAR_DO_NOT_DELETE":
            future_route = "MANUAL_REVIEW"
        rows.append(
            {
                "row_id": f"RP5B_KEEP_REASON_{index:07d}",
                "file_path": row["file_path"],
                "keep_reason": row["final_action"],
                "rp5a_classification": row["rp5a_classification"],
                "rp5b_final_action": row["final_action"],
                "active_consumer_reason": "active consumer detected" if row["active_consumer_found_now_flag"] else "none detected",
                "validation_dependency_reason": "validation dependency detected" if row["validation_dependency_found_now_flag"] else "none detected",
                "identity_dependency_reason": "unique identity possible" if row["contains_unique_qku_formula_identity_now_flag"] else "none detected",
                "future_pr_route": future_route,
            }
        )
    return rows
