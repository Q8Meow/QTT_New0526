#!/usr/bin/env python3
"""Validation-scope reduction accounting for RP5B."""

from __future__ import annotations

from typing import Any


def build_validation_scope_reduction_rows(
    verification_rows: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    removed = [
        row
        for row in verification_rows
        if row.get("safe_to_remove_from_validation_now_flag") and row.get("final_action") in {"DELETE_ACTIVE_TREE_NOW", "ARCHIVE_NO_VALIDATION_SCAN_NOW"}
    ]
    archived_registry = [row for row in registry_rows if row.get("active_status") == "LEGACY_ARCHIVED"]
    active_registry = [row for row in registry_rows if str(row.get("active_status", "")).startswith("ACTIVE")]
    rows = [
        {
            "row_id": "RP5B_VALIDATION_SCOPE_REDUCTION_0001",
            "scope_change_type": "ACTIVE_REGISTRY_REPLACEMENT_VALIDATION",
            "old_validation_file_count": len(verification_rows),
            "new_validation_file_count": len(verification_rows) - len(removed),
            "removed_from_fast_preflight_count": 0,
            "removed_from_repo_wide_integrity_count": 0,
            "removed_from_generated_artifact_scan_count": len(removed),
            "archived_legacy_prefix_count": len(archived_registry),
            "active_prefix_count": len(active_registry),
            "replacement_validator_refs": [
                "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
                "tests/pr168_rp5b/test_active_artifact_registry_exists.py",
                "tests/pr168_rp5b/test_no_raw_legacy_decision_authority.py",
            ],
            "expected_validation_time_reduction_reason": "No RP5A-safe deletion/archive rows existed, so RP5B adds replacement active-registry validation without removing active coverage.",
        }
    ]
    summary = {
        "validation_scope_removed_count": len(removed),
        "validation_replacement_rule_count": len(rows),
        "expected_validation_scan_reduction_count": len(removed),
        "files_archived_by_registry_count": len(archived_registry),
    }
    return rows, summary
