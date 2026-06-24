#!/usr/bin/env python3
"""Validator for PR168-RP5A legacy semantic audit artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from tools.pr168_rp5a_config import (
    CHECKPOINT_PATH,
    DELETE_CLASSIFICATIONS,
    FORBIDDEN_OPERATION_COUNTERS,
    HARD_FAIL_PHYSICAL_PATH_LENGTH,
    MAX_CONSUMER_REFS_PER_FILE,
    MAX_FILES_SCANNED,
    MAX_IDENTITY_REFS_PER_FILE,
    MAX_LINE_HITS_PER_FILE,
    MAX_MATCHED_FILES,
    MAX_STRUCTURED_JSON_BYTES,
    MAX_TOTAL_LINE_HITS,
    MAX_TOTAL_ROWS_PER_SHARD,
    MAX_WALL_SECONDS,
    REPORT_NAMES,
    ROW_SHARDS,
    generated_ref,
    manifest_path_for_shard,
    report_path,
    shard_path,
)
from tools.pr168_rp5a_report_writer import read_json, read_jsonl


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
            if payload.get("max_total_rows_per_shard") != MAX_TOTAL_ROWS_PER_SHARD:
                failures.append(f"MANIFEST_ROW_CAP_MISSING:{generated_ref(path)}")
            if payload.get("row_count_within_bound_flag") is not True:
                failures.append(f"MANIFEST_ROW_CAP_EXCEEDED:{generated_ref(path)}")

    if failures:
        return failures

    preflight = read_json(report_path("PR168_RP5A_Preflight.report.json"))
    if not preflight.get("pr240_closed_not_merged_preflight_passed"):
        failures.append("PR240_NOT_CLOSED_NOT_MERGED")
    if not preflight.get("recovery1_branch_not_active"):
        failures.append("RECOVERY1_BRANCH_ACTIVE")

    term_rows = read_jsonl(shard_path("term_taxonomy_rows"))
    term_texts = {row["term_text_or_regex"] for row in term_rows}
    for required in ("formula repair", "QKU repair", "negative formula", "no-trade dominated formula", "global formula ban", "source truth", "LIVE_CANDIDATE", "REAL_NEGATIVE"):
        if required not in term_texts:
            failures.append(f"TERM_TAXONOMY_MISSING:{required}")
    if len(term_rows) < 40:
        failures.append("TERM_TAXONOMY_TOO_SMALL")

    file_rows = read_jsonl(shard_path("legacy_file_semantic_rows"))
    hit_rows = read_jsonl(shard_path("row_field_semantic_hit_rows"))
    consumer_rows = read_jsonl(shard_path("consumer_graph_rows"))
    validation_rows = read_jsonl(shard_path("validation_dependency_rows"))
    identity_rows = read_jsonl(shard_path("qku_formula_identity_dependency_rows"))
    agent_rows = read_jsonl(shard_path("agent_touchpoint_rows"))
    delete_rows = read_jsonl(shard_path("delete_eligibility_rows"))
    consistency = read_json(report_path("PR168_RP5A_CrossGraphConsistency.report.json"))
    no_delete = read_json(report_path("PR168_RP5A_NoDeletionProof.report.json"))
    final_summary = read_json(report_path("PR168_RP5A_FinalSummary.report.json"))
    path_audit = read_json(report_path("PR168_RP5A_PathAudit.report.json"))
    performance = read_json(report_path("PR168_RP5A_ScanPerformance.report.json"))
    pr165 = read_json(report_path("PR168_RP5A_AgentCrosswalkTouchpoints.report.json"))
    budget_exhausted = performance.get("scan_budget_status") == "SCAN_BUDGET_EXHAUSTED"

    if not file_rows and not budget_exhausted:
        failures.append("NO_FILE_SEMANTIC_ROWS")
    if not hit_rows and not budget_exhausted:
        failures.append("NO_ROW_FIELD_HITS")
    if not read_jsonl(shard_path("legacy_pr_semantic_rows")):
        failures.append("NO_PR_SEMANTIC_ROWS")
    if not read_jsonl(shard_path("wrong_concept_term_rows")):
        failures.append("NO_WRONG_CONCEPT_ROWS")
    if not read_jsonl(shard_path("future_rp5b_plan_rows")):
        failures.append("NO_FUTURE_RP5B_ROWS")
    if not read_jsonl(shard_path("blast_radius_rows")):
        failures.append("NO_BLAST_RADIUS_ROWS")
    if not read_jsonl(shard_path("validation_time_risk_rows")):
        failures.append("NO_VALIDATION_TIME_RISK_ROWS")

    file_paths = {row["file_path"] for row in file_rows}
    for row in file_rows:
        if not row.get("file_path") or not row.get("matched_terms") or not row.get("matched_line_numbers_or_json_paths"):
            failures.append(f"BAD_FILE_ROW:{row.get('file_path')}")
        if not row.get("active_consumer_status_ref"):
            failures.append(f"MISSING_CONSUMER_STATUS:{row.get('file_path')}")
        if not row.get("validation_dependency_status_ref"):
            failures.append(f"MISSING_VALIDATION_STATUS:{row.get('file_path')}")
        if not row.get("identity_dependency_status_ref"):
            failures.append(f"MISSING_IDENTITY_STATUS:{row.get('file_path')}")
        if not row.get("agent_touchpoint_ref"):
            failures.append(f"MISSING_AGENT_STATUS:{row.get('file_path')}")
        if row.get("recommended_classification_draft") not in DELETE_CLASSIFICATIONS:
            failures.append(f"BAD_CLASSIFICATION_DRAFT:{row.get('file_path')}")

    for graph_name, rows, key in (
        ("consumer", consumer_rows, "file_path"),
        ("validation", validation_rows, "file_path_or_prefix"),
        ("identity", identity_rows, "file_path"),
        ("agent", agent_rows, "file_path"),
        ("delete", delete_rows, "file_path"),
    ):
        graph_files = {row[key] for row in rows}
        missing = sorted(file_paths - graph_files)
        if missing:
            failures.append(f"{graph_name.upper()}_GRAPH_MISSING_FILES:{missing[:5]}")

    delete_by_file = Counter(row["file_path"] for row in delete_rows)
    for file_path in file_paths:
        if delete_by_file[file_path] != 1:
            failures.append(f"DELETE_CLASSIFICATION_NOT_EXACTLY_ONE:{file_path}")
    for row in delete_rows:
        if row.get("delete_now_flag"):
            failures.append(f"DELETE_NOW_TRUE:{row.get('file_path')}")
        if row.get("classification") not in DELETE_CLASSIFICATIONS:
            failures.append(f"DELETE_BAD_CLASSIFICATION:{row.get('file_path')}")

    if not consistency.get("consistent_flag"):
        failures.append("CROSS_GRAPH_CONSISTENCY_FAILED")
    for key, expected in FORBIDDEN_OPERATION_COUNTERS.items():
        if no_delete.get(key) != expected:
            failures.append(f"NO_DELETION_FORBIDDEN_COUNTER:{key}:{no_delete.get(key)}")
        if final_summary.get(key) != expected:
            failures.append(f"FINAL_FORBIDDEN_COUNTER:{key}:{final_summary.get(key)}")
    if no_delete.get("validation_scope_removed_count") != 0:
        failures.append("VALIDATION_SCOPE_REMOVED")
    if not no_delete.get("no_legacy_scope_removal_flag"):
        failures.append("NO_LEGACY_SCOPE_REMOVAL_FLAG_FALSE")
    if no_delete.get("validation_scope_changed_flag") and no_delete.get("validation_scope_change_type") != "ADD_RP5A_SCOPE_ONLY":
        failures.append("BAD_VALIDATION_SCOPE_CHANGE_TYPE")

    if not pr165.get("documented_equivalent_crosswalk_present"):
        failures.append("PR165_D2_AGENT_CROSSWALK_MISSING")

    for row in path_audit.get("records", []):
        if row.get("physical_path_length", 0) >= HARD_FAIL_PHYSICAL_PATH_LENGTH:
            failures.append(f"PATH_HARD_FAIL:{row.get('file_path')}")
    for row in hit_rows[:1000]:
        if len(str(row.get("matched_text_short", ""))) > 200:
            failures.append(f"HIT_TEXT_TOO_LONG:{row.get('row_id')}")

    if final_summary.get("files_with_stale_terms_count") != len(file_rows):
        failures.append("FINAL_FILE_COUNT_MISMATCH")
    if final_summary.get("row_field_semantic_hit_count") != len(hit_rows):
        failures.append("FINAL_HIT_COUNT_MISMATCH")
    if final_summary.get("deleted_file_count") != 0 or final_summary.get("moved_file_count") != 0:
        failures.append("FINAL_DELETE_MOVE_NONZERO")
    if performance.get("max_line_hits_per_file") != MAX_LINE_HITS_PER_FILE:
        failures.append("SCAN_PERFORMANCE_BAD_LINE_CAP")
    if performance.get("max_total_line_hits") != MAX_TOTAL_LINE_HITS and not performance.get("quick_selftest_flag"):
        failures.append("SCAN_PERFORMANCE_BAD_TOTAL_LINE_HIT_CAP")
    if performance.get("max_wall_seconds") != MAX_WALL_SECONDS and not performance.get("quick_selftest_flag"):
        failures.append("SCAN_PERFORMANCE_BAD_WALL_BUDGET")
    if performance.get("max_files_scanned") != MAX_FILES_SCANNED and not performance.get("quick_selftest_flag"):
        failures.append("SCAN_PERFORMANCE_BAD_FILE_BUDGET")
    if performance.get("max_matched_files") != MAX_MATCHED_FILES and not performance.get("quick_selftest_flag"):
        failures.append("SCAN_PERFORMANCE_BAD_MATCHED_FILE_BUDGET")
    if performance.get("max_consumer_refs_per_file") != MAX_CONSUMER_REFS_PER_FILE:
        failures.append("SCAN_PERFORMANCE_BAD_CONSUMER_CAP")
    if performance.get("max_identity_refs_per_file") != MAX_IDENTITY_REFS_PER_FILE:
        failures.append("SCAN_PERFORMANCE_BAD_IDENTITY_CAP")
    if performance.get("max_structured_json_bytes") != MAX_STRUCTURED_JSON_BYTES:
        failures.append("SCAN_PERFORMANCE_BAD_STRUCTURED_JSON_CAP")
    if performance.get("max_total_rows_per_shard") != MAX_TOTAL_ROWS_PER_SHARD:
        failures.append("SCAN_PERFORMANCE_BAD_SHARD_CAP")
    if performance.get("peak_memory_strategy") != "RG_TEMP_FILE_TWO_PASS_BOUNDED_HITS":
        failures.append("SCAN_PERFORMANCE_BAD_MEMORY_STRATEGY")
    if performance.get("consumer_graph_scan_mode") != "BOUNDED_STATUS_ONLY_NO_ALL_PAIRS":
        failures.append("SCAN_PERFORMANCE_BAD_CONSUMER_MODE")
    if not performance.get("rg_used_flag"):
        failures.append("SCAN_PERFORMANCE_RG_NOT_USED")
    if performance.get("checkpoint_path") != generated_ref(CHECKPOINT_PATH):
        failures.append("SCAN_PERFORMANCE_BAD_CHECKPOINT_PATH")
    if performance.get("checkpoint_committed_flag") is not False:
        failures.append("SCAN_PERFORMANCE_CHECKPOINT_COMMITTED")
    if performance.get("matched_files_count") != len(file_rows):
        failures.append("SCAN_PERFORMANCE_MATCHED_FILE_COUNT_MISMATCH")
    if performance.get("scan_budget_status") not in {"SCAN_BUDGET_OK", "SCAN_BUDGET_EXHAUSTED"}:
        failures.append("SCAN_PERFORMANCE_BAD_BUDGET_STATUS")
    if budget_exhausted and final_summary.get("delete_from_active_tree_safe_draft_count") != 0:
        failures.append("BUDGET_EXHAUSTED_WITH_DELETE_SAFE_DRAFTS")
    return failures


def run_validation() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise AssertionError("\n".join(failures))
    return {
        "validation": "PR168_RP5A_LEGACY_SEMANTIC_AUDIT_OK",
        "reports_checked": len(REPORT_NAMES),
        "row_shards_checked": len(ROW_SHARDS),
    }
