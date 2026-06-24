#!/usr/bin/env python3
"""Bounded active-consumer status graph for PR168-RP5A."""

from __future__ import annotations

from tools.pr168_rp5a_config import MAX_CONSUMER_REFS_PER_FILE, classify_file_kind


def _status_from_context(
    file_path: str,
    *,
    validation_rows: list[dict[str, object]],
) -> tuple[str, str, str | None, list[str], bool, str]:
    kind = classify_file_kind(file_path)
    validation_examples = [
        str(row.get("validation_component"))
        for row in validation_rows
        if row.get("file_path_or_prefix") == file_path and row.get("validation_dependency_type") != "NONE"
    ][:MAX_CONSUMER_REFS_PER_FILE]
    if kind == "TEST_SOURCE":
        return (
            "tests",
            "TEST_FIXTURE",
            file_path,
            [file_path, *validation_examples][:MAX_CONSUMER_REFS_PER_FILE],
            True,
            "KEEP_TEST_FIXTURE",
        )
    if kind == "VALIDATOR":
        return (
            "validator file path reads",
            "DIRECT_IMPORT",
            file_path,
            [file_path, *validation_examples][:MAX_CONSUMER_REFS_PER_FILE],
            True,
            "KEEP_VALIDATION_DEPENDENCY",
        )
    if kind == "TOOL_SOURCE":
        return (
            "tool imports",
            "DIRECT_IMPORT",
            file_path,
            [file_path, *validation_examples][:MAX_CONSUMER_REFS_PER_FILE],
            True,
            "KEEP_ACTIVE_CONSUMER",
        )
    if validation_examples:
        return (
            "validator file path reads",
            "GLOB_SCAN",
            validation_examples[0],
            validation_examples,
            True,
            "KEEP_VALIDATION_DEPENDENCY",
        )
    if kind in {"GENERATED_REPORT", "GENERATED_SHARD", "MANIFEST"}:
        return (
            "generated reports",
            "UNKNOWN",
            None,
            [],
            False,
            "NO_EXHAUSTIVE_CONSUMER_SCAN_UNCLEAR_IF_DELETED",
        )
    if kind == "DOC":
        return (
            "PR body / docs only",
            "DOC_REF",
            None,
            [],
            False,
            "KEEP_LEGACY_SUMMARY_ONLY",
        )
    return ("unknown", "UNKNOWN", None, [], False, "UNCLEAR_DO_NOT_DELETE")


def build_consumer_graph(
    matched_files: list[str],
    repo_root=None,
    *,
    validation_rows: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    validation_rows = [] if validation_rows is None else validation_rows
    rows: list[dict[str, object]] = []
    for index, matched_path in enumerate(matched_files, start=1):
        (
            consumer_type,
            strength,
            consumer_file,
            examples,
            active,
            recommended,
        ) = _status_from_context(matched_path, validation_rows=validation_rows)
        break_risk = "HIGH" if active else "UNKNOWN" if strength == "UNKNOWN" else "LOW"
        rows.append(
            {
                "row_id": f"RP5A_CONSUMER_{index:07d}",
                "file_path": matched_path,
                "consumer_type": consumer_type,
                "consumer_file_path": consumer_file,
                "consumer_line_or_json_path": None,
                "consumer_purpose": "bounded dependency-status row; no exhaustive all-pairs reference expansion",
                "consumer_strength": strength,
                "active_consumer_flag": active,
                "consumer_break_risk_if_deleted": break_risk,
                "recommended_action": recommended,
                "consumer_examples_limited": examples[:MAX_CONSUMER_REFS_PER_FILE],
                "consumer_examples_capped_flag": len(examples) >= MAX_CONSUMER_REFS_PER_FILE,
                "consumer_graph_scan_mode": "BOUNDED_STATUS_ONLY_NO_ALL_PAIRS",
                "max_consumer_refs_per_file": MAX_CONSUMER_REFS_PER_FILE,
            }
        )
    return rows
