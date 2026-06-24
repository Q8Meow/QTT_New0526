#!/usr/bin/env python3
"""Cross-graph consistency checks for PR168-RP5A."""

from __future__ import annotations


def build_consistency_report_rows(
    delete_rows: list[dict[str, object]],
    consumer_rows: list[dict[str, object]],
    validation_rows: list[dict[str, object]],
    identity_rows: list[dict[str, object]],
    agent_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    active_consumer = {str(row["file_path"]) for row in consumer_rows if row.get("active_consumer_flag")}
    validation_dep = {str(row["file_path_or_prefix"]) for row in validation_rows if row.get("validation_dependency_type") != "NONE"}
    unique_identity = {str(row["file_path"]) for row in identity_rows if row.get("unique_identity_possible_flag") and not row.get("duplicate_elsewhere_proven_flag")}
    active_agent = {str(row["file_path"]) for row in agent_rows if row.get("active_agent_touchpoint_flag")}
    rows: list[dict[str, object]] = []
    for index, row in enumerate(delete_rows, start=1):
        file_path = str(row["file_path"])
        classification = str(row["classification"])
        failures: list[str] = []
        if row.get("delete_now_flag"):
            failures.append("DELETE_NOW_FLAG_TRUE")
        if classification == "DELETE_FROM_ACTIVE_TREE_SAFE":
            if file_path in active_consumer:
                failures.append("ACTIVE_CONSUMER_CANNOT_DELETE_SAFE")
            if file_path in validation_dep:
                failures.append("VALIDATION_DEPENDENCY_CANNOT_DELETE_SAFE")
            if file_path in unique_identity:
                failures.append("UNIQUE_IDENTITY_CANNOT_DELETE_SAFE")
            if file_path in active_agent:
                failures.append("ACTIVE_AGENT_TOUCHPOINT_CANNOT_DELETE_SAFE")
        if classification not in {
            "DELETE_FROM_ACTIVE_TREE_SAFE",
            "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM",
            "KEEP_ACTIVE_CONSUMER",
            "KEEP_UNIQUE_QKU_FORMULA_SOURCE",
            "KEEP_TEST_FIXTURE",
            "KEEP_VALIDATION_DEPENDENCY",
            "KEEP_LEGACY_SUMMARY_ONLY",
            "ARCHIVE_NO_VALIDATION_SCAN",
            "REWRITE_CONSUMER_FIRST",
            "UNCLEAR_DO_NOT_DELETE",
        }:
            failures.append("UNKNOWN_CLASSIFICATION")
        rows.append(
            {
                "row_id": f"RP5A_CONSISTENCY_{index:07d}",
                "file_path": file_path,
                "classification": classification,
                "consistency_failures": failures,
                "consistent_flag": not failures,
            }
        )
    return rows
