#!/usr/bin/env python3
"""Delete eligibility draft classifier for PR168-RP5A."""

from __future__ import annotations

from tools.pr168_rp5a_config import classify_file_kind


def build_delete_eligibility_rows(
    matched_files: list[str],
    file_term_map: dict[str, dict[str, object]],
    consumer_rows: list[dict[str, object]],
    validation_rows: list[dict[str, object]],
    identity_rows: list[dict[str, object]],
    agent_rows: list[dict[str, object]],
    blast_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    active_consumer = {str(row["file_path"]) for row in consumer_rows if row.get("active_consumer_flag")}
    unknown_consumer = {
        str(row["file_path"])
        for row in consumer_rows
        if row.get("consumer_strength") == "UNKNOWN"
        or row.get("consumer_break_risk_if_deleted") == "UNKNOWN"
    }
    validation_dep = {str(row["file_path_or_prefix"]) for row in validation_rows if row.get("validation_dependency_type") != "NONE"}
    identity_dep = {str(row["file_path"]) for row in identity_rows if row.get("unique_identity_possible_flag")}
    agent_dep = {str(row["file_path"]) for row in agent_rows if row.get("active_agent_touchpoint_flag")}
    blast_ref = {str(row["file_path"]): row["row_id"] for row in blast_rows}
    rows: list[dict[str, object]] = []
    for index, file_path in enumerate(matched_files, start=1):
        kind = classify_file_kind(file_path)
        if kind == "TEST_SOURCE":
            classification = "KEEP_TEST_FIXTURE"
            reason = "test source carries expectations or fixture coverage"
            future_pr = "UNKNOWN"
        elif file_path in validation_dep:
            classification = "KEEP_VALIDATION_DEPENDENCY"
            reason = "current validation inventory or generated scan depends on this file"
            future_pr = "PR168_RP5B"
        elif file_path in active_consumer:
            classification = "KEEP_ACTIVE_CONSUMER"
            reason = "literal active consumer reference found"
            future_pr = "PR168_RP5B"
        elif file_path in identity_dep and kind in {"GENERATED_REPORT", "GENERATED_SHARD", "MANIFEST"}:
            classification = "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM"
            reason = "generated artifact may contain unique QKU/formula identity custody"
            future_pr = "PR168_RP5C"
        elif file_path in identity_dep:
            classification = "KEEP_UNIQUE_QKU_FORMULA_SOURCE"
            reason = "non-generated file may contain unique identity source"
            future_pr = "PR168_RP5C"
        elif file_path in agent_dep:
            classification = "REWRITE_CONSUMER_FIRST"
            reason = "agent-route or no-orphan touchpoint needs replacement before cleanup"
            future_pr = "PR168_RP5B"
        elif file_path in unknown_consumer:
            classification = "UNCLEAR_DO_NOT_DELETE"
            reason = "consumer graph is bounded status-only and dependency status remains unclear"
            future_pr = "UNKNOWN"
        elif kind in {"GENERATED_REPORT", "GENERATED_SHARD", "MANIFEST"}:
            classification = "DELETE_FROM_ACTIVE_TREE_SAFE"
            reason = "future-only draft: generated stale artifact has no detected consumer, validation dependency, identity, or agent touchpoint"
            future_pr = "PR168_RP5B"
        elif kind == "DOC":
            classification = "KEEP_LEGACY_SUMMARY_ONLY"
            reason = "documentation should be summarized or normalized rather than silently deleted"
            future_pr = "PR168_RP5B"
        else:
            classification = "UNCLEAR_DO_NOT_DELETE"
            reason = "dependency or identity status is insufficiently clear"
            future_pr = "UNKNOWN"
        rows.append(
            {
                "row_id": f"RP5A_DELETE_{index:07d}",
                "file_path": file_path,
                "classification": classification,
                "classification_reason": reason,
                "stale_term_refs": sorted(file_term_map[file_path].get("matched_term_ids", [])),
                "consumer_graph_refs": [row["row_id"] for row in consumer_rows if row["file_path"] == file_path][:50],
                "validation_dependency_refs": [row["row_id"] for row in validation_rows if row["file_path_or_prefix"] == file_path][:50],
                "identity_dependency_refs": [row["row_id"] for row in identity_rows if row["file_path"] == file_path][:50],
                "agent_touchpoint_refs": [row["row_id"] for row in agent_rows if row["file_path"] == file_path][:50],
                "blast_radius_refs": [blast_ref.get(file_path)] if blast_ref.get(file_path) else [],
                "future_cleanup_pr": future_pr,
                "delete_now_flag": False,
                "delete_in_future_allowed_after_conditions": _future_conditions(classification),
                "operator_review_required_flag": classification in {"UNCLEAR_DO_NOT_DELETE", "REWRITE_CONSUMER_FIRST", "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM"},
            }
        )
    return rows


def _future_conditions(classification: str) -> str:
    if classification == "DELETE_FROM_ACTIVE_TREE_SAFE":
        return "RP5B may delete after operator review confirms no new consumer appeared."
    if classification == "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM":
        return "RP5C immutable library reclaim must happen before deletion."
    if classification == "REWRITE_CONSUMER_FIRST":
        return "Rewrite active consumers to canonical active layer first."
    return "Deletion not allowed under current RP5A classification."
