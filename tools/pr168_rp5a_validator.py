#!/usr/bin/env python3
"""Validator for PR168-RP5A legacy semantic audit artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from tools.build_pr168_rp5a_legacy_semantic_audit import (
    VALIDATION_SCOPE_EVIDENCE_FIELDS,
    VALIDATION_SCOPE_EVIDENCE_SCHEMA_VERSION,
    VALIDATION_SCOPE_MAIN_BASELINE_LABEL,
    VALIDATION_SCOPE_MAIN_COMPARISON_MODE,
    VALIDATION_SCOPE_MERGE_BASELINE_LABEL,
    VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE,
    VALIDATION_SCOPE_SNAPSHOT_CONTEXT,
    _validation_scope_delta,
)
from tools.ci_branch_context import current_branch_context
from tools.pr168_rp5a_config import (
    CHECKPOINT_PATH,
    DELETE_CLASSIFICATIONS,
    FILE_KIND_CURRENTIZATION,
    FILE_KIND_DOC,
    FILE_KIND_GENERATED_REPORT,
    FILE_KIND_GENERATED_SHARD,
    FILE_KIND_MANIFEST,
    FILE_KIND_TEST_SOURCE,
    FILE_KIND_TOOL_SOURCE,
    FILE_KIND_VALIDATOR,
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
from tools.validation_scope_registry import ST12A_BRANCH

VALIDATION_SCOPE_CHANGE_TYPES = frozenset(
    {
        "SEMANTIC_COMMAND_ADDITION_ONLY",
        "SEMANTIC_COMMAND_REMOVAL_DETECTED",
        "NONE",
    }
)
_DELETE_CLASSIFICATION_SUMMARY_FIELDS = {
    "DELETE_FROM_ACTIVE_TREE_SAFE": (
        "delete_from_active_tree_safe_draft_count"
    ),
    "DELETE_AFTER_QKU_FORMULA_IDENTITY_RECLAIM": (
        "delete_after_qku_formula_identity_reclaim_count"
    ),
    "KEEP_ACTIVE_CONSUMER": "keep_active_consumer_count",
    "KEEP_UNIQUE_QKU_FORMULA_SOURCE": (
        "keep_unique_qku_formula_source_count"
    ),
    "KEEP_TEST_FIXTURE": "keep_test_fixture_count",
    "KEEP_VALIDATION_DEPENDENCY": "keep_validation_dependency_count",
    "KEEP_LEGACY_SUMMARY_ONLY": "keep_legacy_summary_only_count",
    "ARCHIVE_NO_VALIDATION_SCAN": "archive_no_validation_scan_count",
    "REWRITE_CONSUMER_FIRST": "rewrite_consumer_first_count",
    "UNCLEAR_DO_NOT_DELETE": "unclear_do_not_delete_count",
}
_FILE_KIND_SUMMARY_FIELDS = {
    FILE_KIND_GENERATED_REPORT: "generated_reports_with_stale_terms_count",
    FILE_KIND_GENERATED_SHARD: "generated_shards_with_stale_terms_count",
    FILE_KIND_TOOL_SOURCE: "tools_with_stale_terms_count",
    FILE_KIND_TEST_SOURCE: "tests_with_stale_terms_count",
    FILE_KIND_VALIDATOR: "validators_with_stale_terms_count",
    FILE_KIND_DOC: "docs_with_stale_terms_count",
    FILE_KIND_CURRENTIZATION: "currentization_with_stale_terms_count",
    FILE_KIND_MANIFEST: "manifests_with_stale_terms_count",
}


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


def _scope_payload_failures(
    payload: Mapping[str, object],
    *,
    prefix: str,
) -> list[str]:
    failures: list[str] = []
    if (
        payload.get("validation_scope_evidence_schema_version")
        != VALIDATION_SCOPE_EVIDENCE_SCHEMA_VERSION
    ):
        failures.append(f"{prefix}_EVIDENCE_SCHEMA_VERSION_INVALID")
    if (
        payload.get("validation_scope_snapshot_context")
        != VALIDATION_SCOPE_SNAPSHOT_CONTEXT
    ):
        failures.append(f"{prefix}_SNAPSHOT_CONTEXT_INVALID")

    comparison_mode = payload.get("validation_scope_comparison_mode")
    baseline_label = payload.get("validation_scope_baseline_ref")
    expected_labels = {
        VALIDATION_SCOPE_MAIN_COMPARISON_MODE: (
            VALIDATION_SCOPE_MAIN_BASELINE_LABEL
        ),
        VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE: (
            VALIDATION_SCOPE_MERGE_BASELINE_LABEL
        ),
    }
    if comparison_mode not in expected_labels:
        failures.append(f"{prefix}_COMPARISON_MODE_INVALID")
    elif baseline_label != expected_labels[comparison_mode]:
        failures.append(f"{prefix}_BASELINE_LABEL_INVALID")

    baseline_count = payload.get(
        "validation_scope_baseline_command_count"
    )
    current_count = payload.get(
        "validation_scope_current_command_count"
    )
    added_count = payload.get("validation_scope_added_count")
    removed_count = payload.get("validation_scope_removed_count")
    for field, value, minimum in (
        ("BASELINE_COMMAND_COUNT", baseline_count, 1),
        ("CURRENT_COMMAND_COUNT", current_count, 1),
        ("ADDED_COUNT", added_count, 0),
        ("REMOVED_COUNT", removed_count, 0),
    ):
        if not _is_integer(value, minimum=minimum):
            failures.append(f"{prefix}_{field}_INVALID")
    if all(
        (
            _is_integer(baseline_count, minimum=1),
            _is_integer(current_count, minimum=1),
            _is_integer(added_count, minimum=0),
            _is_integer(removed_count, minimum=0),
        )
    ) and baseline_count - removed_count + added_count != current_count:
        failures.append(f"{prefix}_COMMAND_COUNT_DELTA_INCOHERENT")

    removed_refs = payload.get("validation_scope_removed_refs")
    if not isinstance(removed_refs, list):
        failures.append(f"{prefix}_REMOVED_REFS_INVALID")
        removed_refs = []
    removed_ref_multiplicities = [
        _removed_ref_multiplicity(value) for value in removed_refs
    ]
    if any(value is None for value in removed_ref_multiplicities):
        failures.append(f"{prefix}_REMOVED_REF_SIGNATURE_INVALID")
    represented_removed_count = sum(
        value
        for value in removed_ref_multiplicities
        if value is not None
    )
    if (
        _is_integer(removed_count, minimum=0)
        and represented_removed_count != removed_count
    ):
        failures.append(f"{prefix}_REMOVED_REF_COUNT_MISMATCH")

    inventory_failures = payload.get(
        "current_validation_inventory_failures"
    )
    inventory_failure_count = payload.get(
        "current_validation_inventory_failure_count"
    )
    if not isinstance(inventory_failures, list) or any(
        not isinstance(value, str) for value in inventory_failures
    ):
        failures.append(f"{prefix}_INVENTORY_FAILURES_INVALID")
        inventory_failures = []
    if not _is_integer(inventory_failure_count, minimum=0):
        failures.append(f"{prefix}_INVENTORY_FAILURE_COUNT_INVALID")
    elif inventory_failure_count != len(inventory_failures):
        failures.append(f"{prefix}_INVENTORY_FAILURE_COUNT_MISMATCH")

    expected_changed_flag = bool(
        (_is_integer(added_count, minimum=0) and added_count > 0)
        or (_is_integer(removed_count, minimum=0) and removed_count > 0)
    )
    if (
        not isinstance(payload.get("validation_scope_changed_flag"), bool)
        or payload.get("validation_scope_changed_flag")
        is not expected_changed_flag
    ):
        failures.append(f"{prefix}_CHANGED_FLAG_INCOHERENT")

    change_type = payload.get("validation_scope_change_type")
    if change_type not in VALIDATION_SCOPE_CHANGE_TYPES:
        failures.append(f"{prefix}_CHANGE_TYPE_INVALID")
    expected_change_type = (
        "SEMANTIC_COMMAND_REMOVAL_DETECTED"
        if _is_integer(removed_count, minimum=0) and removed_count > 0
        else (
            "SEMANTIC_COMMAND_ADDITION_ONLY"
            if _is_integer(added_count, minimum=0) and added_count > 0
            else "NONE"
        )
    )
    if (
        change_type in VALIDATION_SCOPE_CHANGE_TYPES
        and change_type != expected_change_type
    ):
        failures.append(f"{prefix}_CHANGE_TYPE_INCOHERENT")

    expected_no_removal = bool(
        _is_integer(removed_count, minimum=0)
        and removed_count == 0
        and isinstance(inventory_failures, list)
        and not inventory_failures
    )
    if (
        not isinstance(payload.get("no_legacy_scope_removal_flag"), bool)
        or payload.get("no_legacy_scope_removal_flag")
        is not expected_no_removal
    ):
        failures.append(f"{prefix}_NO_REMOVAL_FLAG_INCOHERENT")
    return failures


def _validation_scope_failures(
    no_delete: Mapping[str, object],
    final_summary: Mapping[str, object],
    live_validation_scope: Mapping[str, object] | None,
    branch: str,
) -> list[str]:
    failures: list[str] = []
    no_delete_records = no_delete.get("records")
    final_summary_records = final_summary.get("records")
    if not isinstance(no_delete_records, dict):
        failures.append("VALIDATION_SCOPE_NO_DELETION_RECORDS_INVALID")
        no_delete_records = {}
    if not isinstance(final_summary_records, dict):
        failures.append("VALIDATION_SCOPE_FINAL_SUMMARY_RECORDS_INVALID")
        final_summary_records = {}

    locations = (
        ("NO_DELETION_TOP", no_delete),
        ("NO_DELETION_RECORDS", no_delete_records),
        ("FINAL_SUMMARY_TOP", final_summary),
        ("FINAL_SUMMARY_RECORDS", final_summary_records),
    )
    for field in VALIDATION_SCOPE_EVIDENCE_FIELDS:
        canonical_value = no_delete.get(field)
        for location, payload in locations:
            if field not in payload:
                failures.append(
                    "VALIDATION_SCOPE_EVIDENCE_MISSING:"
                    f"{location}:{field}"
                )
            elif (
                field in no_delete
                and payload[field] != canonical_value
            ):
                failures.append(
                    "VALIDATION_SCOPE_EVIDENCE_PERSISTED_MISMATCH:"
                    f"{location}:{field}"
                )

    if all(field in no_delete for field in VALIDATION_SCOPE_EVIDENCE_FIELDS):
        persisted = {
            field: no_delete[field]
            for field in VALIDATION_SCOPE_EVIDENCE_FIELDS
        }
        failures.extend(
            _scope_payload_failures(persisted, prefix="PERSISTED_SCOPE")
        )
        persisted_removed_refs = persisted.get(
            "validation_scope_removed_refs"
        )
        persisted_inventory_failures = persisted.get(
            "current_validation_inventory_failures"
        )
        if persisted.get("validation_scope_removed_count") != 0:
            failures.append("PERSISTED_VALIDATION_SCOPE_REMOVED")
        if persisted_removed_refs != []:
            failures.append(
                "PERSISTED_VALIDATION_SCOPE_REMOVED_REFS_PRESENT"
            )
        if (
            persisted.get(
                "current_validation_inventory_failure_count"
            )
            != 0
        ):
            failures.append(
                "PERSISTED_VALIDATION_INVENTORY_FAILURE_COUNT_NONZERO"
            )
        if persisted_inventory_failures != []:
            failures.append("PERSISTED_VALIDATION_INVENTORY_FAILED")
        if persisted.get("no_legacy_scope_removal_flag") is not True:
            failures.append(
                "PERSISTED_NO_LEGACY_SCOPE_REMOVAL_FLAG_FALSE"
            )
    else:
        persisted = None

    if live_validation_scope is not None:
        failures.extend(
            _scope_payload_failures(
                live_validation_scope,
                prefix="LIVE_SCOPE",
            )
        )
        expected_mode, expected_label = (
            (
                VALIDATION_SCOPE_MAIN_COMPARISON_MODE,
                VALIDATION_SCOPE_MAIN_BASELINE_LABEL,
            )
            if branch == "main"
            else (
                VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE,
                VALIDATION_SCOPE_MERGE_BASELINE_LABEL,
            )
        )
        if (
            live_validation_scope.get("validation_scope_comparison_mode")
            != expected_mode
        ):
            failures.append("LIVE_VALIDATION_SCOPE_CONTEXT_MODE_INVALID")
        if (
            live_validation_scope.get("validation_scope_baseline_ref")
            != expected_label
        ):
            failures.append("LIVE_VALIDATION_SCOPE_CONTEXT_LABEL_INVALID")
        if live_validation_scope.get("validation_scope_removed_count") != 0:
            failures.append("LIVE_VALIDATION_SCOPE_REMOVED")
        if live_validation_scope.get("validation_scope_removed_refs") != []:
            failures.append(
                "LIVE_VALIDATION_SCOPE_REMOVED_REFS_PRESENT"
            )
        if (
            live_validation_scope.get(
                "current_validation_inventory_failure_count"
            )
            != 0
        ):
            failures.append(
                "LIVE_VALIDATION_INVENTORY_FAILURE_COUNT_NONZERO"
            )
        if (
            live_validation_scope.get(
                "current_validation_inventory_failures"
            )
            != []
        ):
            failures.append("LIVE_VALIDATION_INVENTORY_FAILED")
        if (
            live_validation_scope.get("no_legacy_scope_removal_flag")
            is not True
        ):
            failures.append("LIVE_NO_LEGACY_SCOPE_REMOVAL_FLAG_FALSE")
        if branch == ST12A_BRANCH and persisted is not None:
            for field in VALIDATION_SCOPE_EVIDENCE_FIELDS:
                if persisted[field] != live_validation_scope.get(field):
                    failures.append(
                        "VALIDATION_SCOPE_EVIDENCE_LIVE_MISMATCH:"
                        f"ST12A:{field}"
                    )
    return failures


def _final_summary_count_failures(
    final_summary: Mapping[str, object],
    final_summary_records: Mapping[str, object],
    field: str,
    expected: int,
    failure_code: str,
) -> list[str]:
    failures: list[str] = []
    if final_summary.get(field) != expected:
        failures.append(
            f"{failure_code}:TOP:{field}:"
            f"{final_summary.get(field)}:{expected}"
        )
    if final_summary_records.get(field) != expected:
        failures.append(
            f"{failure_code}:RECORDS:{field}:"
            f"{final_summary_records.get(field)}:{expected}"
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
    custody_rows = read_jsonl(shard_path("identity_custody_rows"))
    agent_rows = read_jsonl(shard_path("agent_touchpoint_rows"))
    blast_rows = read_jsonl(shard_path("blast_radius_rows"))
    validation_time_rows = read_jsonl(
        shard_path("validation_time_risk_rows")
    )
    delete_rows = read_jsonl(shard_path("delete_eligibility_rows"))
    consistency = read_json(report_path("PR168_RP5A_CrossGraphConsistency.report.json"))
    no_delete = read_json(report_path("PR168_RP5A_NoDeletionProof.report.json"))
    final_summary = read_json(report_path("PR168_RP5A_FinalSummary.report.json"))
    final_summary_records = final_summary.get("records")
    if not isinstance(final_summary_records, dict):
        final_summary_records = {}
    try:
        live_validation_scope = _validation_scope_delta()
    except Exception as exc:
        failures.append(
            "VALIDATION_SCOPE_LIVE_COMPARISON_FAILED:"
            f"{type(exc).__name__}:{exc}"
        )
        live_validation_scope = None
    failures.extend(
        _validation_scope_failures(
            no_delete,
            final_summary,
            live_validation_scope,
            current_branch_context(Path(__file__).resolve().parents[1]).branch,
        )
    )
    path_audit = read_json(report_path("PR168_RP5A_PathAudit.report.json"))
    input_report = read_json(report_path("PR168_RP5A_Input.report.json"))
    performance = read_json(report_path("PR168_RP5A_ScanPerformance.report.json"))
    legacy_pr = read_json(
        report_path("PR168_RP5A_LegacyPRSemanticAudit.report.json")
    )
    pr165 = read_json(report_path("PR168_RP5A_AgentCrosswalkTouchpoints.report.json"))
    delete_manifest = read_json(
        manifest_path_for_shard(shard_path("delete_eligibility_rows"))
    )
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

    if not pr165.get("documented_equivalent_crosswalk_present"):
        failures.append("PR165_D2_AGENT_CROSSWALK_MISSING")

    for row in path_audit.get("records", []):
        if row.get("physical_path_length", 0) >= HARD_FAIL_PHYSICAL_PATH_LENGTH:
            failures.append(f"PATH_HARD_FAIL:{row.get('file_path')}")
    for row in hit_rows[:1000]:
        if len(str(row.get("matched_text_short", ""))) > 200:
            failures.append(f"HIT_TEXT_TOO_LONG:{row.get('row_id')}")

    input_files_scanned = input_report.get("files_scanned_count")
    performance_files_scanned = performance.get("files_scanned_count")
    if (
        not _is_integer(input_files_scanned, minimum=0)
        or not _is_integer(performance_files_scanned, minimum=0)
    ):
        failures.append("FILES_SCANNED_DETAILED_OWNER_COUNT_INVALID")
    else:
        if input_files_scanned != performance_files_scanned:
            failures.append(
                "FILES_SCANNED_DETAILED_OWNER_COUNT_MISMATCH:"
                f"{input_files_scanned}:{performance_files_scanned}"
            )
        failures.extend(
            _final_summary_count_failures(
                final_summary,
                final_summary_records,
                "files_scanned_count",
                input_files_scanned,
                "FINAL_FILES_SCANNED_COUNT_MISMATCH",
            )
        )

    for field in (
        "github_prs_scanned_count",
        "github_prs_with_stale_terms_count",
    ):
        expected = legacy_pr.get(field)
        if not _is_integer(expected, minimum=0):
            failures.append(
                f"LEGACY_PR_DETAILED_OWNER_COUNT_INVALID:{field}"
            )
            continue
        failures.extend(
            _final_summary_count_failures(
                final_summary,
                final_summary_records,
                field,
                expected,
                "FINAL_LEGACY_PR_COUNT_MISMATCH",
            )
        )

    file_kind_counts = Counter(
        str(row.get("file_kind")) for row in file_rows
    )
    independently_derived_counts = {
        "stale_term_taxonomy_count": len(term_rows),
        "files_with_stale_terms_count": len(file_rows),
        **{
            summary_field: file_kind_counts[file_kind]
            for file_kind, summary_field
            in _FILE_KIND_SUMMARY_FIELDS.items()
        },
        "row_field_semantic_hit_count": len(hit_rows),
        "consumer_graph_row_count": len(consumer_rows),
        "active_consumer_file_count": len(
            {
                row["file_path"]
                for row in consumer_rows
                if row.get("active_consumer_flag")
            }
        ),
        "validation_dependency_row_count": len(validation_rows),
        "validation_dependent_file_count": len(
            {
                row["file_path_or_prefix"]
                for row in validation_rows
                if row.get("validation_dependency_type") != "NONE"
            }
        ),
        "qku_formula_identity_dependency_file_count": len(
            [row for row in identity_rows if row.get("identity_count")]
        ),
        "identity_custody_row_count": len(custody_rows),
        "agent_touchpoint_file_count": len(
            {
                row["file_path"]
                for row in agent_rows
                if row.get("active_agent_touchpoint_flag")
            }
        ),
        "blast_radius_row_count": len(blast_rows),
        "validation_time_risk_row_count": len(validation_time_rows),
    }
    for field, expected in independently_derived_counts.items():
        failures.extend(
            _final_summary_count_failures(
                final_summary,
                final_summary_records,
                field,
                expected,
                "FINAL_DETAILED_ROW_COUNT_MISMATCH",
            )
        )

    delete_classification_counts = Counter(
        str(row.get("classification")) for row in delete_rows
    )
    for classification, field in (
        _DELETE_CLASSIFICATION_SUMMARY_FIELDS.items()
    ):
        failures.extend(
            _final_summary_count_failures(
                final_summary,
                final_summary_records,
                field,
                delete_classification_counts[classification],
                "FINAL_DELETE_CLASSIFICATION_COUNT_MISMATCH",
            )
        )
    delete_manifest_row_count = delete_manifest.get("row_count")
    if not _is_integer(delete_manifest_row_count, minimum=0):
        failures.append("DELETE_MANIFEST_ROW_COUNT_INVALID")
    else:
        for location, payload in (
            ("TOP", final_summary),
            ("RECORDS", final_summary_records),
        ):
            values = [
                payload.get(field)
                for field
                in _DELETE_CLASSIFICATION_SUMMARY_FIELDS.values()
            ]
            if not all(
                _is_integer(value, minimum=0) for value in values
            ):
                failures.append(
                    "FINAL_DELETE_CLASSIFICATION_TOTAL_INVALID:"
                    f"{location}"
                )
            elif sum(values) != delete_manifest_row_count:
                failures.append(
                    "FINAL_DELETE_CLASSIFICATION_TOTAL_MISMATCH:"
                    f"{location}:{sum(values)}:"
                    f"{delete_manifest_row_count}"
                )

    for field in FORBIDDEN_OPERATION_COUNTERS:
        expected = no_delete.get(field)
        if _is_integer(expected, minimum=0):
            failures.extend(
                _final_summary_count_failures(
                    final_summary,
                    final_summary_records,
                    field,
                    expected,
                    "FINAL_NO_DELETION_COUNTER_MISMATCH",
                )
            )

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
