#!/usr/bin/env python3
"""Validation dependency graph builder for PR168-RP5A."""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path

from tools.pr168_rp5a_config import classify_file_kind, normalize_repo_path


def _entries_matching(path: str):
    try:
        from tools.validation_inventory import entries_matching_path

        return list(entries_matching_path(path))
    except Exception:
        return []


def _generated_scan_dependency(path: str) -> bool:
    return path.startswith("docs/master_plan/generated/") and (
        path.endswith(".json") or path.endswith(".jsonl") or path.endswith(".manifest.json")
    )


def build_validation_dependency_rows(matched_files: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    row_number = 0
    for file_path in matched_files:
        entries = _entries_matching(file_path)
        for entry in entries:
            row_number += 1
            dep_type = "TEST_FIXTURE" if classify_file_kind(file_path) == "TEST_SOURCE" else "REQUIRED_FILE"
            matched_globs = [glob for glob in entry.required_when_files_match if fnmatchcase(normalize_repo_path(file_path), glob)]
            rows.append(
                {
                    "row_id": f"RP5A_VALIDATION_{row_number:07d}",
                    "file_path_or_prefix": file_path,
                    "validation_component": entry.validator_id,
                    "validation_dependency_type": dep_type,
                    "dependency_file_path": ",".join(matched_globs[:5]) or entry.validator_id,
                    "line_or_json_path": None,
                    "break_risk_if_removed": "HIGH" if entry.fail_closed_if_touched else "MEDIUM",
                    "can_be_removed_from_validation_future_pr_flag": False,
                    "requires_currentization_if_changed_flag": bool(entry.pr152_tracked),
                    "recommended_future_cleanup_step": "KEEP_VALIDATION_DEPENDENCY_OR_UPDATE_VALIDATOR_IN_RP5B",
                }
            )
        if _generated_scan_dependency(file_path):
            row_number += 1
            rows.append(
                {
                    "row_id": f"RP5A_VALIDATION_{row_number:07d}",
                    "file_path_or_prefix": file_path,
                    "validation_component": "repo_generated_artifact_glob_scan",
                    "validation_dependency_type": "GLOB_SCANNED",
                    "dependency_file_path": "docs/master_plan/generated/**/*.json*",
                    "line_or_json_path": None,
                    "break_risk_if_removed": "MEDIUM",
                    "can_be_removed_from_validation_future_pr_flag": True,
                    "requires_currentization_if_changed_flag": file_path.endswith(".report.json"),
                    "recommended_future_cleanup_step": "RP5B_CAN_REDUCE_SCAN_ONLY_AFTER_REPLACEMENT_OR_SUMMARY",
                }
            )
        if not entries and not _generated_scan_dependency(file_path):
            row_number += 1
            rows.append(
                {
                    "row_id": f"RP5A_VALIDATION_{row_number:07d}",
                    "file_path_or_prefix": file_path,
                    "validation_component": "none_detected",
                    "validation_dependency_type": "NONE",
                    "dependency_file_path": None,
                    "line_or_json_path": None,
                    "break_risk_if_removed": "LOW",
                    "can_be_removed_from_validation_future_pr_flag": True,
                    "requires_currentization_if_changed_flag": False,
                    "recommended_future_cleanup_step": "NO_VALIDATION_DEPENDENCY_FOUND",
                }
            )
    return sorted(rows, key=lambda row: (str(row["file_path_or_prefix"]), str(row["validation_component"])))


def build_validation_time_risk_rows(matched_files: list[str], repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    prefixes = sorted({str(Path(path).parent).replace("\\", "/") for path in matched_files if path.startswith("docs/master_plan/generated/")})
    all_targets = [(path, [path]) for path in matched_files] + [(prefix, [path for path in matched_files if path.startswith(prefix + "/")]) for prefix in prefixes]
    for index, (target, files) in enumerate(all_targets, start=1):
        approx_bytes = 0
        for file_path in files:
            try:
                approx_bytes += (repo_root / file_path).stat().st_size
            except OSError:
                pass
        rows.append(
            {
                "row_id": f"RP5A_VALIDATION_TIME_{index:07d}",
                "file_path_or_prefix": target,
                "file_count_under_prefix": len(files),
                "approx_bytes_under_prefix": approx_bytes,
                "validation_glob_scan_flag": target.startswith("docs/master_plan/generated/"),
                "repo_wide_scan_flag": True,
                "generated_artifact_scan_flag": target.startswith("docs/master_plan/generated/"),
                "future_rp5b_validation_reduction_candidate_flag": target.startswith("docs/master_plan/generated/"),
                "requires_replacement_or_summary_before_removal_flag": True,
            }
        )
    return rows
