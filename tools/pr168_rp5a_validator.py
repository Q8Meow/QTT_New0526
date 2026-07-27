#!/usr/bin/env python3
"""Validator for PR168-RP5A legacy semantic audit artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from tools.build_pr168_rp5a_legacy_semantic_audit import (
    VALIDATION_SCOPE_BASELINE_REF,
    VALIDATION_SCOPE_COMPARISON_MODE,
    VALIDATION_SCOPE_EVIDENCE_FIELDS,
    _validation_scope_delta,
)
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

VALIDATION_SCOPE_CHANGE_TYPES = frozenset(
    {"SEMANTIC_COMMAND_ADDITION_ONLY", "NONE"}
)


def _is_integer(value: object, *, minimum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= minimum
    )


def _removed_ref_multiplicity(value: object) -> int | None:
    if not isinstance(value, dict):
        return None
    if (
        not isinstance(value.get("phase"), str)
        or not value["phase"]
        or not isinstance(value.get("validator_id"), str)
        or not value["validator_id"]
        or not isinstance(value.get("canonical_command"), list)
        or not value["canonical_command"]
        or any(
            not isinstance(part, str)
            for part in value["canonical_command"]
        )
        or not _is_integer(value.get("multiplicity"), minimum=1)
    ):
        return None
    return int(value["multiplicity"])


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
    no_delete_records = no_delete.get("records")
    final_summary_records = final_summary.get("records")
    if not isinstance(no_delete_records, dict):
        failures.append("VALIDATION_SCOPE_NO_DELETION_RECORDS_INVALID")
        no_delete_records = {}
    if not isinstance(final_summary_records, dict):
        failures.append("VALIDATION_SCOPE_FINAL_SUMMARY_RECORDS_INVALID")
        final_summary_records = {}
    try:
        live_validation_scope = _validation_scope_delta()
    except Exception as exc:
        failures.append(
            "VALIDATION_SCOPE_LIVE_COMPARISON_FAILED:"
            f"{type(exc).__name__}:{exc}"
        )
        live_validation_scope = None
    for field in VALIDATION_SCOPE_EVIDENCE_FIELDS:
        locations = (
            ("NO_DELETION_TOP", no_delete),
            ("NO_DELETION_RECORDS", no_delete_records),
            ("FINAL_SUMMARY_TOP", final_summary),
            ("FINAL_SUMMARY_RECORDS", final_summary_records),
        )
        for location, payload in locations:
            if field not in payload:
                failures.append(
                    "VALIDATION_SCOPE_EVIDENCE_MISSING:"
                    f"{location}:{field}"
                )
            elif (
                live_validation_scope is not None
                and payload[field] != live_validation_scope[field]
            ):
                failures.append(
                    "VALIDATION_SCOPE_EVIDENCE_LIVE_MISMATCH:"
                    f"{location}:{field}"
                )
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
    if no_delete.get("validation_scope_comparison_mode") != VALIDATION_SCOPE_COMPARISON_MODE:
        failures.append("VALIDATION_SCOPE_COMPARISON_MODE_INVALID")
    if no_delete.get("validation_scope_baseline_ref") != VALIDATION_SCOPE_BASELINE_REF:
        failures.append("VALIDATION_SCOPE_BASELINE_REF_INVALID")
    baseline_command_count = no_delete.get("validation_scope_baseline_command_count")
    current_command_count = no_delete.get("validation_scope_current_command_count")
    added_count = no_delete.get("validation_scope_added_count")
    removed_count = no_delete.get("validation_scope_removed_count")
    if not _is_integer(baseline_command_count, minimum=1):
        failures.append("VALIDATION_SCOPE_BASELINE_COMMAND_COUNT_INVALID")
    if not _is_integer(current_command_count, minimum=1):
        failures.append("VALIDATION_SCOPE_CURRENT_COMMAND_COUNT_INVALID")
    if not _is_integer(added_count, minimum=0):
        failures.append("VALIDATION_SCOPE_ADDED_COUNT_INVALID")
    if not _is_integer(removed_count, minimum=0):
        failures.append("VALIDATION_SCOPE_REMOVED_COUNT_INVALID")
    removed_refs = no_delete.get("validation_scope_removed_refs")
    if not isinstance(removed_refs, list):
        failures.append("VALIDATION_SCOPE_REMOVED_REFS_INVALID")
        removed_refs = []
    removed_ref_multiplicities = [
        _removed_ref_multiplicity(value) for value in removed_refs
    ]
    if any(value is None for value in removed_ref_multiplicities):
        failures.append("VALIDATION_SCOPE_REMOVED_REF_SIGNATURE_INVALID")
    represented_removed_count = sum(
        value
        for value in removed_ref_multiplicities
        if value is not None
    )
    if (
        _is_integer(removed_count, minimum=0)
        and represented_removed_count != removed_count
    ):
        failures.append("VALIDATION_SCOPE_REMOVED_REF_COUNT_MISMATCH")
    inventory_failures = no_delete.get("current_validation_inventory_failures")
    inventory_failure_count = no_delete.get(
        "current_validation_inventory_failure_count"
    )
    if not isinstance(inventory_failures, list) or any(
        not isinstance(value, str) for value in inventory_failures
    ):
        failures.append("CURRENT_VALIDATION_INVENTORY_FAILURES_INVALID")
        inventory_failures = []
    if not _is_integer(inventory_failure_count, minimum=0):
        failures.append("CURRENT_VALIDATION_INVENTORY_FAILURE_COUNT_INVALID")
    elif inventory_failure_count != len(inventory_failures):
        failures.append("CURRENT_VALIDATION_INVENTORY_FAILURE_COUNT_MISMATCH")
    if inventory_failures:
        failures.append("CURRENT_VALIDATION_INVENTORY_FAILED")
    if removed_refs:
        failures.append("VALIDATION_SCOPE_REMOVED_REFS_PRESENT")
    if no_delete.get("validation_scope_removed_count") != 0:
        failures.append("VALIDATION_SCOPE_REMOVED")
    if not no_delete.get("no_legacy_scope_removal_flag"):
        failures.append("NO_LEGACY_SCOPE_REMOVAL_FLAG_FALSE")
    change_type = no_delete.get("validation_scope_change_type")
    if change_type not in VALIDATION_SCOPE_CHANGE_TYPES:
        failures.append("BAD_VALIDATION_SCOPE_CHANGE_TYPE")
    expected_change_type = (
        "SEMANTIC_COMMAND_ADDITION_ONLY"
        if _is_integer(added_count, minimum=0) and added_count > 0
        else "NONE"
    )
    if change_type in VALIDATION_SCOPE_CHANGE_TYPES and change_type != expected_change_type:
        failures.append("VALIDATION_SCOPE_CHANGE_TYPE_COUNT_MISMATCH")
    expected_changed_flag = bool(
        (_is_integer(added_count, minimum=0) and added_count > 0)
        or (_is_integer(removed_count, minimum=0) and removed_count > 0)
    )
    if no_delete.get("validation_scope_changed_flag") is not expected_changed_flag:
        failures.append("VALIDATION_SCOPE_CHANGED_FLAG_MISMATCH")

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
    if performance.get("peak_memory_strategy") not in {
        "RG_TEMP_FILE_TWO_PASS_BOUNDED_HITS",
        "GIT_GREP_TEMP_FILE_TWO_PASS_BOUNDED_HITS",
        "PYTHON_FALLBACK_STREAMING_BOUNDED_LINE_SCAN",
    }:
        failures.append("SCAN_PERFORMANCE_BAD_MEMORY_STRATEGY")
    if performance.get("consumer_graph_scan_mode") != "BOUNDED_STATUS_ONLY_NO_ALL_PAIRS":
        failures.append("SCAN_PERFORMANCE_BAD_CONSUMER_MODE")
    scan_engine_count = sum(
        bool(performance.get(flag))
        for flag in ("rg_used_flag", "git_grep_used_flag", "python_fallback_used_flag")
    )
    if scan_engine_count != 1:
        failures.append("SCAN_PERFORMANCE_SCAN_ENGINE_STATE_INVALID")
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
