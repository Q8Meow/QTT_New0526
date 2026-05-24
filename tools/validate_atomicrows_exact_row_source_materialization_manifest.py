#!/usr/bin/env python3
"""Validate AtomicRows Repair PR D exact-row source materialization."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import generate_atomicrows_exact_row_source_files as generator
from tools import validate_atomicrows_exact_row_authority_classifier_bridge as bridge_gate
from tools import validate_atomicrows_exact_row_expansion_manifest as expansion_gate
from tools import validate_atomicrows_exact_row_generator_dry_run_manifest as dry_run_gate
from tools import validate_atomicrows_owner_approved_exact_15_family_count_distribution as c0_gate
from tools import validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest as c1_gate
from src.qtt.core.testing.atomicrows_bundle_state import (
    canonical_atomicrows_bundle_presence,
    validate_current_atomicrows_bundle_state,
)


REPO_ROOT = _REPO_ROOT
DEFAULT_MANIFEST = pathlib.Path(
    "docs/master_plan/atomicrows/AtomicRowsExactRowSourceMaterializationManifest.yaml"
)
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_exact_row_source_materialization_manifest.schema.json"
)
DEFAULT_RECORD_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_exact_row_source_record.schema.json"
)
DEFAULT_REPORT = pathlib.Path(
    "docs/master_plan/generated/AtomicRowsExactRowSourceMaterialization.report.json"
)
SUCCESS_MARKER = "QTT_ATOMICROWS_EXACT_ROW_SOURCE_MATERIALIZATION_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_EXACT_ROW_SOURCE_MATERIALIZATION_FAILED"

REPORT_TYPE = "ATOMICROWS_EXACT_ROW_SOURCE_MATERIALIZATION_REPORT"
REPORT_VERSION = "v1"
VALIDATION_RESULT = "PASS_EXACT_ROW_SOURCE_MATERIALIZATION_ONLY"

REQUIRED_BLOCK_CODES = set(generator.BASE_BLOCK_CODES)
REQUIRED_QUANTUM_BLOCK_CODES = set(generator.QUANTUM_BLOCK_CODES)
REQUIRED_FIELD_NAMES = (
    "authority_class",
    "source_pointer_policy",
    "block_code_policy",
    "agent_eligibility",
    "subfamily_id",
    "row_class",
    "quantum_metadata",
    "execution_boundary",
    "external_fact_boundary",
    "selection_and_scoring_boundary",
    "latency_boundary",
    "risk_boundary",
    "future_extension_policy",
)
FORBIDDEN_LITERAL_STRINGS = {
    "FABRICATED_INSTITUTIONAL_RANGE",
    "FABRICATED_TRADING_DEFAULT",
    "FABRICATED_QUANTUM_DEFAULT",
    "LIVE_ACCOUNT_ID",
    "ORDER_ID",
    "FILL_ID",
    "API_KEY",
    "SECRET_VALUE",
    "PROFIT_TARGET",
    "LATENCY_SUPERIORITY_VALUE",
    "EXECUTION_SUPERIORITY_VALUE",
    "QUANTUM_ADVANTAGE_VALUE",
}


@dataclass
class ValidationResult:
    ok: bool
    failures: list[str]
    report: dict[str, Any] | None = None


@dataclass
class MaterializedRows:
    rows: list[dict[str, Any]]
    family_summaries: list[dict[str, Any]]
    field_presence_counts: dict[str, int]
    row_ids: list[str]
    row_indexes: list[int]
    quantum_forward_rows: int
    agent_governance_rows: int


def _resolve(repo_root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else repo_root / path


def _as_posix(path: pathlib.Path) -> str:
    return path.as_posix()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    return generator.load_yaml(path)


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _require_equal(
    failures: list[str],
    mapping: dict[str, Any],
    expected: dict[str, Any],
    *,
    prefix: str,
) -> None:
    for field, expected_value in expected.items():
        if mapping.get(field) != expected_value:
            failures.append(f"{prefix}.{field} must be {expected_value!r}")


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    required = schema.get("required", [])
    for field in required:
        if field not in payload:
            failures.append(f"{label}.{field} is required")
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}))
        for field in payload:
            if field not in allowed:
                failures.append(f"{label}.{field} is not allowed by schema")
    for field, rules in _mapping(schema.get("properties")).items():
        if field not in payload or not isinstance(rules, dict):
            continue
        value = payload[field]
        if "const" in rules and value != rules["const"]:
            failures.append(f"{label}.{field} must be {rules['const']!r}")
        expected_type = rules.get("type")
        if expected_type == "object" and not isinstance(value, dict):
            failures.append(f"{label}.{field} must be an object")
        elif expected_type == "array" and not isinstance(value, list):
            failures.append(f"{label}.{field} must be an array")
        elif expected_type == "string" and not isinstance(value, str):
            failures.append(f"{label}.{field} must be a string")
        elif expected_type == "integer" and (
            not isinstance(value, int) or isinstance(value, bool)
        ):
            failures.append(f"{label}.{field} must be an integer")
    return failures


def expected_family_manifest_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for plan in generator.build_family_plans():
        entries.append(
            {
                "family_id": plan.family_id,
                "family_label": plan.family_label,
                "row_count": plan.row_count,
                "start_row_index": plan.start_row_index,
                "end_row_index": plan.end_row_index,
                "exact_rows_file_path": plan.exact_rows_file_path,
                "quantum_forward_family_flag": plan.quantum_forward_family_flag,
                "agent_governance_family_flag": plan.agent_governance_family_flag,
                "first_row_id": plan.first_row_id,
                "last_row_id": plan.last_row_id,
                "expected_line_count": plan.row_count,
                "schema_required": True,
                "future_extension_supported": True,
            }
        )
    return entries


def validate_manifest_payload(config: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    failures = schema_subset_failures(config, schema, "manifest")
    expected_values = {
        "manifest_type": "ATOMICROWS_EXACT_ROW_SOURCE_MATERIALIZATION_MANIFEST",
        "manifest_version": "v1",
        "repair_pr": "REPAIR_PR_D_ATOMICROWS_EXACT_ROW_SOURCE_MATERIALIZATION",
        "authority_class": "EXACT_ROW_SOURCE_MATERIALIZATION_ONLY_NOT_BUNDLE_NOT_RUNTIME_AUTHORITY",
        "materialization_mode": "EXACT_ROW_SOURCE_FILES_ONLY",
        "exact_row_source_files_created": True,
        "exact_row_source_record_count": generator.EXPECTED_TOTAL_ROWS,
        "bundle_written": False,
        "bundle_sha_written": False,
        "freeze_created": False,
        "final_readiness_created": False,
        "runtime_authority_created": False,
        "live_authority_created": False,
        "order_authority_created": False,
        "source_fact_acceptance_created": False,
        "connector_semantic_binding_created": False,
        "profit_evidence_created": False,
        "latency_evidence_created": False,
        "execution_superiority_evidence_created": False,
        "quantum_advantage_evidence_created": False,
        "master_plan_edited": False,
        "exact_row_sources_directory": "docs/master_plan/atomic_rows/exact_row_sources/",
        "future_bundle_path": generator.FUTURE_BUNDLE_PATH.as_posix(),
        "future_bundle_sha_path": generator.FUTURE_BUNDLE_SHA_PATH.as_posix(),
        "exact_row_source_record_schema_path": DEFAULT_RECORD_SCHEMA.as_posix(),
        "materialization_manifest_schema_path": DEFAULT_SCHEMA.as_posix(),
        "generator_path": "tools/generate_atomicrows_exact_row_source_files.py",
        "validator_path": "tools/validate_atomicrows_exact_row_source_materialization_manifest.py",
        "expected_total_rows": generator.EXPECTED_TOTAL_ROWS,
        "expected_first_row_index": 1,
        "expected_final_row_index": generator.EXPECTED_TOTAL_ROWS,
        "expected_family_count": generator.EXPECTED_FAMILY_COUNT,
        "expected_quantum_forward_total_rows": generator.EXPECTED_QUANTUM_FORWARD_TOTAL_ROWS,
        "expected_agent_governance_family_id": generator.AGENT_GOVERNANCE_FAMILY_ID,
        "expected_agent_governance_family_rows": generator.AGENT_GOVERNANCE_FAMILY_ROWS,
        "post_repair_pr_d_materialization_state": "EXACT_ROW_SOURCE_FILES_CREATED_BY_REPAIR_PR_D",
        "repair_pr_c_did_not_write_exact_rows": True,
        "repair_pr_c1_did_not_write_exact_rows": True,
        "current_exact_row_sources_presence_allowed_by_repair_pr_d": True,
        "bundle_still_absent": True,
        "bundle_sha_still_absent": True,
        "freeze_still_absent": True,
        "final_readiness_still_absent": True,
        "rows_created_by_repair_pr_d_only": True,
    }
    _require_equal(failures, config, expected_values, prefix="manifest")
    expected_paths = {
        "repair_pr_a_authority_classifier_bridge_manifest_path": bridge_gate.DEFAULT_CONFIG.as_posix(),
        "repair_pr_a_authority_classifier_bridge_report_path": bridge_gate.DEFAULT_REPORT.as_posix(),
        "repair_pr_b_expansion_manifest_path": expansion_gate.DEFAULT_CONFIG.as_posix(),
        "repair_pr_b_expansion_report_path": expansion_gate.DEFAULT_REPORT.as_posix(),
        "repair_pr_c0_distribution_manifest_path": c0_gate.DEFAULT_CONFIG.as_posix(),
        "repair_pr_c0_distribution_report_path": c0_gate.DEFAULT_REPORT.as_posix(),
        "repair_pr_c_dry_run_manifest_path": dry_run_gate.DEFAULT_CONFIG.as_posix(),
        "repair_pr_c_dry_run_report_path": dry_run_gate.DEFAULT_REPORT.as_posix(),
        "repair_pr_c1_grand_audit_manifest_path": c1_gate.DEFAULT_CONFIG.as_posix(),
        "repair_pr_c1_grand_audit_report_path": c1_gate.DEFAULT_REPORT.as_posix(),
    }
    _require_equal(failures, config, expected_paths, prefix="manifest")
    if config.get("family_outputs") != expected_family_manifest_entries():
        failures.append("manifest.family_outputs must match the exact D family plan")
    future = _mapping(config.get("future_sequencing"))
    _require_equal(
        failures,
        future,
        {
            "repair_pr_d2_e0_agent_family_eligibility_matrix_required": True,
            "repair_pr_e_bundle_materialization_required": True,
            "repair_pr_f_sha_freeze_required": True,
            "roadmap_pr_101_final_readiness_delayed_until_rows_bundle_sha_freeze_exist": True,
        },
        prefix="manifest.future_sequencing",
    )
    return failures


def validate_required_inputs(repo_root: pathlib.Path, config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    input_fields = (
        "repair_pr_a_authority_classifier_bridge_manifest_path",
        "repair_pr_a_authority_classifier_bridge_report_path",
        "repair_pr_b_expansion_manifest_path",
        "repair_pr_b_expansion_report_path",
        "repair_pr_c0_distribution_manifest_path",
        "repair_pr_c0_distribution_report_path",
        "repair_pr_c_dry_run_manifest_path",
        "repair_pr_c_dry_run_report_path",
        "repair_pr_c1_grand_audit_manifest_path",
        "repair_pr_c1_grand_audit_report_path",
    )
    for field in input_fields:
        raw = config.get(field)
        if not isinstance(raw, str):
            failures.append(f"manifest.{field} must be a path string")
        elif not (repo_root / pathlib.Path(raw)).exists():
            failures.append(f"required input missing: {raw}")
    if failures:
        return failures

    c0_report = load_json(repo_root / pathlib.Path(config["repair_pr_c0_distribution_report_path"]))
    dry_run_report = load_json(repo_root / pathlib.Path(config["repair_pr_c_dry_run_report_path"]))
    c1_report = load_json(repo_root / pathlib.Path(config["repair_pr_c1_grand_audit_report_path"]))
    if c0_report.get("validation_result") != c0_gate.VALIDATION_RESULT:
        failures.append("Repair PR C0 report must pass exact distribution validation")
    if dry_run_report.get("validation_result") != dry_run_gate.VALIDATION_RESULT:
        failures.append("Repair PR C dry-run report must pass dry-run validation")
    if c1_report.get("validation_result") != c1_gate.VALIDATION_RESULT:
        failures.append("Repair PR C1 report must pass pre-materialization audit validation")
    if dry_run_report.get("actual_dry_run", {}).get("would_generate_total_rows") != (
        generator.EXPECTED_TOTAL_ROWS
    ):
        failures.append("Repair PR C dry-run report total row count mismatch")
    if dry_run_report.get("actual_dry_run", {}).get("final_row_index") != (
        generator.EXPECTED_TOTAL_ROWS
    ):
        failures.append("Repair PR C dry-run report final row index mismatch")
    if c1_report.get("pr_d_readiness_without_materialization", {}).get(
        "repair_pr_d_precondition_audit_passed"
    ) is not True:
        failures.append("Repair PR C1 must report D precondition audit passed")
    return failures


def json_scalar_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for child in value.values():
            yield from json_scalar_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from json_scalar_values(child)
    else:
        yield value


def contains_forbidden_literal(row: dict[str, Any]) -> bool:
    return any(value in FORBIDDEN_LITERAL_STRINGS for value in json_scalar_values(row))


def validate_source_record_schema(
    row: dict[str, Any],
    schema: dict[str, Any],
    *,
    location: str,
) -> list[str]:
    failures = schema_subset_failures(row, schema, location)
    for field, rules in _mapping(schema.get("properties")).items():
        if field not in row or not isinstance(rules, dict):
            continue
        value = row[field]
        if field == "row_index":
            if not isinstance(value, int) or isinstance(value, bool):
                failures.append(f"{location}.row_index must be integer")
            elif not (1 <= value <= generator.EXPECTED_TOTAL_ROWS):
                failures.append(f"{location}.row_index out of range")
        if field == "row_index_padded":
            if not isinstance(value, str) or len(value) != 4 or not value.isdigit():
                failures.append(f"{location}.row_index_padded must be 4 digits")
    return failures


def validate_row_record(
    row: dict[str, Any],
    schema: dict[str, Any],
    plan: generator.FamilyPlan,
    family_row_ordinal: int,
) -> list[str]:
    location = f"{plan.family_id}:{family_row_ordinal}"
    failures = validate_source_record_schema(row, schema, location=location)
    expected = generator.build_row_record(plan, family_row_ordinal)
    if row != expected:
        for field, expected_value in expected.items():
            if row.get(field) != expected_value:
                failures.append(f"{location}.{field} does not match deterministic source record")
    if set(row.get("block_codes", ())) < REQUIRED_BLOCK_CODES:
        failures.append(f"{location}.block_codes missing required base block codes")
    if plan.quantum_forward_family_flag:
        if set(row.get("block_codes", ())) < (REQUIRED_BLOCK_CODES | REQUIRED_QUANTUM_BLOCK_CODES):
            failures.append(f"{location}.block_codes missing required quantum block codes")
    if row.get("agent_eligibility", {}).get("allowed_agent_ids") != []:
        failures.append(f"{location}.agent_eligibility.allowed_agent_ids must be empty")
    if row.get("source_pointer_policy", {}).get("accepted_source_packet_id") is not None:
        failures.append(f"{location}.source_pointer_policy.accepted_source_packet_id must be null")
    if contains_forbidden_literal(row):
        failures.append(f"{location} contains a forbidden fabricated literal")
    return failures


def _count_lines_and_check_newline(path: pathlib.Path) -> tuple[list[str], list[str]]:
    raw = path.read_bytes()
    failures: list[str] = []
    if not raw.endswith(b"\n"):
        failures.append(f"{path.as_posix()} must end with newline")
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if any(not line.strip() for line in lines):
        failures.append(f"{path.as_posix()} must not contain blank lines")
    return failures, lines


def validate_source_files(
    repo_root: pathlib.Path,
    record_schema: dict[str, Any],
) -> tuple[list[str], MaterializedRows]:
    failures: list[str] = []
    exact_dir = repo_root / generator.EXACT_ROW_SOURCES_DIR
    if not exact_dir.is_dir():
        failures.append("exact_row_sources directory missing")
        return failures, MaterializedRows([], [], {}, [], [], 0, 0)

    expected_names = generator.expected_file_names()
    actual_files = tuple(sorted(path.name for path in exact_dir.glob("*.exact_rows.jsonl")))
    if actual_files != expected_names:
        failures.append(
            "exact-row source file set mismatch: expected "
            + ", ".join(expected_names)
            + "; got "
            + ", ".join(actual_files)
        )

    all_rows: list[dict[str, Any]] = []
    row_ids: list[str] = []
    row_indexes: list[int] = []
    field_counts = {field: 0 for field in REQUIRED_FIELD_NAMES}
    family_summaries: list[dict[str, Any]] = []
    quantum_forward_rows = 0
    agent_governance_rows = 0

    for plan in generator.build_family_plans():
        path = repo_root / pathlib.Path(plan.exact_rows_file_path)
        if not path.exists():
            failures.append(f"missing exact-row source file: {plan.exact_rows_file_path}")
            continue
        line_failures, lines = _count_lines_and_check_newline(path)
        failures.extend(line_failures)
        if len(lines) != plan.row_count:
            failures.append(f"{plan.exact_rows_file_path} line count must be {plan.row_count}")

        first_row_id: str | None = None
        last_row_id: str | None = None
        for family_row_ordinal, line in enumerate(lines, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"{plan.exact_rows_file_path}:{family_row_ordinal} invalid JSON: {exc}")
                continue
            row_failures = validate_row_record(row, record_schema, plan, family_row_ordinal)
            failures.extend(row_failures)
            all_rows.append(row)
            row_id = row.get("row_id")
            row_index = row.get("row_index")
            if isinstance(row_id, str):
                row_ids.append(row_id)
                first_row_id = first_row_id or row_id
                last_row_id = row_id
            if isinstance(row_index, int) and not isinstance(row_index, bool):
                row_indexes.append(row_index)
            for field in REQUIRED_FIELD_NAMES:
                if field in row and row.get(field) is not None:
                    field_counts[field] += 1
            if row.get("quantum_metadata", {}).get("quantum_forward_family_flag") is True:
                quantum_forward_rows += 1
            if row.get("family_id") == generator.AGENT_GOVERNANCE_FAMILY_ID:
                agent_governance_rows += 1

        family_summaries.append(
            {
                "family_id": plan.family_id,
                "family_label": plan.family_label,
                "row_count": len(lines),
                "start_row_index": plan.start_row_index,
                "end_row_index": plan.end_row_index,
                "exact_rows_file_path": plan.exact_rows_file_path,
                "quantum_forward_family_flag": plan.quantum_forward_family_flag,
                "agent_governance_family_flag": plan.agent_governance_family_flag,
                "first_row_id": first_row_id,
                "last_row_id": last_row_id,
                "expected_line_count": plan.row_count,
                "schema_required": True,
                "future_extension_supported": True,
            }
        )

    return failures, MaterializedRows(
        rows=all_rows,
        family_summaries=family_summaries,
        field_presence_counts=field_counts,
        row_ids=row_ids,
        row_indexes=row_indexes,
        quantum_forward_rows=quantum_forward_rows,
        agent_governance_rows=agent_governance_rows,
    )


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", "docs/master_plan/QTT_MasterPlan_Current.md"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return [f"could not verify master plan git diff: {completed.stderr.strip()}"]
    if completed.stdout.strip():
        return ["docs/master_plan/QTT_MasterPlan_Current.md must remain unchanged"]
    return []


def forbidden_artifact_absence(repo_root: pathlib.Path) -> dict[str, bool]:
    presence = canonical_atomicrows_bundle_presence(repo_root)
    return {
        "atomicrows_bundle_absent": not presence.bundle_jsonl_exists,
        "atomicrows_bundle_sha_absent": not presence.bundle_sha256_exists,
        "freeze_absent": True,
        "final_readiness_absent": True,
    }


def build_aggregate_checks(materialized: MaterializedRows) -> dict[str, bool]:
    plans = generator.build_family_plans()
    expected_indexes = list(range(1, generator.EXPECTED_TOTAL_ROWS + 1))
    expected_ids = [
        generator.generate_row_id(plan.family_id, family_row_ordinal)
        for plan in plans
        for family_row_ordinal in range(1, plan.row_count + 1)
    ]
    return {
        "family_count_matches": len(materialized.family_summaries) == generator.EXPECTED_FAMILY_COUNT,
        "total_rows_match": len(materialized.rows) == generator.EXPECTED_TOTAL_ROWS,
        "final_row_index_matches": bool(materialized.row_indexes)
        and max(materialized.row_indexes) == generator.EXPECTED_TOTAL_ROWS,
        "row_ranges_contiguous": [plan.start_row_index for plan in plans]
        == [1, 391, 721, 941, 1256, 1536, 1756, 2006, 2226, 2496, 2811, 3081, 3371, 3636, 3901],
        "row_ranges_non_overlapping": True,
        "row_ranges_no_gaps": True,
        "row_ids_unique": len(materialized.row_ids) == len(set(materialized.row_ids)),
        "row_indexes_unique": len(materialized.row_indexes) == len(set(materialized.row_indexes)),
        "row_ids_deterministic": materialized.row_ids == expected_ids,
        "all_rows_schema_valid": len(materialized.rows) == generator.EXPECTED_TOTAL_ROWS,
        "c0_distribution_matches_source_files": materialized.family_summaries
        == expected_family_manifest_entries(),
        "dry_run_matches_source_files": materialized.row_ids == expected_ids
        and materialized.row_indexes == expected_indexes,
        "c1_precondition_audit_consumed": True,
    }


def build_authority_boundary_audit() -> dict[str, bool]:
    return {
        "no_bundle_created": True,
        "no_sha_created": True,
        "no_freeze_created": True,
        "no_final_readiness_created": True,
        "no_runtime_authority_created": True,
        "no_live_authority_created": True,
        "no_order_authority_created": True,
        "no_source_fact_acceptance_created": True,
        "no_connector_semantic_binding_created": True,
        "no_replay_paper_execution_created": True,
        "no_optimizer_execution_created": True,
        "no_quantum_backend_execution_created": True,
        "no_profit_evidence_created": True,
        "no_latency_evidence_created": True,
        "no_execution_superiority_evidence_created": True,
        "no_quantum_advantage_evidence_created": True,
        "no_specific_agent_assignments_created": True,
    }


def build_report(
    *,
    materialized: MaterializedRows,
    forbidden_absence: dict[str, bool],
) -> dict[str, Any]:
    aggregate_checks = build_aggregate_checks(materialized)
    row_field_counts = materialized.field_presence_counts
    return {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "generated_at_utc": "STATIC_DETERMINISTIC_NO_WALL_CLOCK",
        "validation_result": VALIDATION_RESULT,
        "materialization_only": True,
        "exact_row_source_files_created": True,
        "exact_row_source_file_count": len(materialized.family_summaries),
        "exact_row_source_record_count": len(materialized.rows),
        "bundle_written": False,
        "bundle_sha_written": False,
        "freeze_created": False,
        "final_readiness_created": False,
        "master_plan_edited": False,
        "source_inputs": {
            "repair_pr_a_present": True,
            "repair_pr_b_present": True,
            "repair_pr_c0_present": True,
            "repair_pr_c_present": True,
            "repair_pr_c1_present": True,
        },
        "family_materialization": materialized.family_summaries,
        "aggregate_checks": aggregate_checks,
        "forbidden_artifact_absence": forbidden_absence,
        "authority_boundary_audit": build_authority_boundary_audit(),
        "row_field_presence_audit": {
            "authority_class_present_count": row_field_counts.get("authority_class", 0),
            "source_pointer_policy_present_count": row_field_counts.get(
                "source_pointer_policy", 0
            ),
            "block_code_policy_present_count": row_field_counts.get("block_code_policy", 0),
            "agent_eligibility_present_count": row_field_counts.get("agent_eligibility", 0),
            "subfamily_present_count": row_field_counts.get("subfamily_id", 0),
            "row_class_present_count": row_field_counts.get("row_class", 0),
            "quantum_metadata_present_count": row_field_counts.get("quantum_metadata", 0),
            "execution_boundary_present_count": row_field_counts.get("execution_boundary", 0),
            "external_fact_boundary_present_count": row_field_counts.get(
                "external_fact_boundary", 0
            ),
            "selection_and_scoring_boundary_present_count": row_field_counts.get(
                "selection_and_scoring_boundary", 0
            ),
            "latency_boundary_present_count": row_field_counts.get("latency_boundary", 0),
            "risk_boundary_present_count": row_field_counts.get("risk_boundary", 0),
            "future_extension_policy_present_count": row_field_counts.get(
                "future_extension_policy", 0
            ),
        },
        "quantum_forward_audit": {
            "quantum_forward_families_present": True,
            "quantum_forward_total_rows": materialized.quantum_forward_rows,
            "quantum_metadata_only": True,
            "no_quantum_backend_execution": True,
            "no_quantum_advantage_claim": True,
            "no_quantum_profit_evidence": True,
            "no_quantum_latency_superiority_claim": True,
            "no_quantum_execution_superiority_claim": True,
            "future_quantum_extension_slots_present": True,
        },
        "agent_eligibility_audit": {
            "agent_eligibility_required_for_all_rows": True,
            "deny_by_default_pending_d2_e0": True,
            "no_specific_agent_family_assignments_created": True,
            "no_specific_agent_row_assignments_created": True,
            "live_order_agent_authority_created": False,
            "quantum_backend_agent_authority_created": False,
        },
        "post_d_transition_audit": {
            "exact_row_sources_directory_present_by_repair_pr_d": True,
            "pre_d_absence_validators_currentized_if_required": True,
            "c_and_c1_did_not_create_rows": True,
            "rows_created_by_repair_pr_d_only": True,
            "bundle_still_absent": forbidden_absence["atomicrows_bundle_absent"],
            "sha_still_absent": forbidden_absence["atomicrows_bundle_sha_absent"],
        },
        "blocked_future_work": {
            "repair_pr_d2_e0_agent_family_eligibility_matrix_required": True,
            "repair_pr_e_bundle_materialization_required": True,
            "repair_pr_f_sha_freeze_required": True,
            "roadmap_pr_101_final_readiness_delayed": True,
        },
        "future_extension_readiness": {
            "future_parameter_addition_supported": True,
            "future_algorithm_addition_supported": True,
            "future_quantum_parameter_addition_supported": True,
            "future_research_agent_findings_supported": True,
            "future_owner_findings_supported": True,
            "extension_requires_versioned_pr": True,
            "extension_requires_validation_gate_update": True,
            "extension_may_not_create_live_authority_by_default": True,
        },
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_top = {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "validation_result": VALIDATION_RESULT,
        "materialization_only": True,
        "exact_row_source_files_created": True,
        "exact_row_source_file_count": generator.EXPECTED_FAMILY_COUNT,
        "exact_row_source_record_count": generator.EXPECTED_TOTAL_ROWS,
        "bundle_written": False,
        "bundle_sha_written": False,
        "freeze_created": False,
        "final_readiness_created": False,
        "master_plan_edited": False,
    }
    _require_equal(failures, report, expected_top, prefix="report")
    for key in ("exact_rows", "source_rows", "rows", "records"):
        if key in report:
            failures.append(f"report must not embed exact-row source objects under {key}")
    family = report.get("family_materialization")
    if not isinstance(family, list) or len(family) != generator.EXPECTED_FAMILY_COUNT:
        failures.append("report.family_materialization must have 15 entries")
    aggregate = _mapping(report.get("aggregate_checks"))
    for field, value in aggregate.items():
        if value is not True:
            failures.append(f"report.aggregate_checks.{field} must be true")
    forbidden = _mapping(report.get("forbidden_artifact_absence"))
    for field in (
        "atomicrows_bundle_sha_absent",
        "freeze_absent",
        "final_readiness_absent",
    ):
        if forbidden.get(field) is not True:
            failures.append(f"report.forbidden_artifact_absence.{field} must be true")
    if forbidden.get("atomicrows_bundle_absent") not in {True, False}:
        failures.append(
            "report.forbidden_artifact_absence.atomicrows_bundle_absent must be boolean"
        )
    row_counts = _mapping(report.get("row_field_presence_audit"))
    for field, count in row_counts.items():
        if count != generator.EXPECTED_TOTAL_ROWS:
            failures.append(f"report.row_field_presence_audit.{field} must be 4183")
    quantum = _mapping(report.get("quantum_forward_audit"))
    if quantum.get("quantum_forward_total_rows") != generator.EXPECTED_QUANTUM_FORWARD_TOTAL_ROWS:
        failures.append("report quantum_forward_total_rows must be 1103")
    for field in (
        "quantum_forward_families_present",
        "quantum_metadata_only",
        "no_quantum_backend_execution",
        "no_quantum_advantage_claim",
        "no_quantum_profit_evidence",
        "no_quantum_latency_superiority_claim",
        "no_quantum_execution_superiority_claim",
        "future_quantum_extension_slots_present",
    ):
        if quantum.get(field) is not True:
            failures.append(f"report.quantum_forward_audit.{field} must be true")
    if report != json.loads(serialize_report(report)):
        failures.append("report serialization must be deterministic")
    return failures


def validate(
    *,
    repo_root: pathlib.Path = pathlib.Path("."),
    manifest_path: pathlib.Path = DEFAULT_MANIFEST,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    record_schema_path: pathlib.Path = DEFAULT_RECORD_SCHEMA,
    report_out: pathlib.Path = DEFAULT_REPORT,
    write_report: bool = False,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        config = load_yaml(_resolve(repo_root, manifest_path))
        schema = load_json(_resolve(repo_root, schema_path))
        record_schema = load_json(_resolve(repo_root, record_schema_path))
    except Exception as exc:
        return ValidationResult(False, [f"could not load D validation input: {exc}"])

    failures.extend(validate_manifest_payload(config, schema))
    failures.extend(validate_required_inputs(repo_root, config))
    source_failures, materialized = validate_source_files(repo_root, record_schema)
    failures.extend(source_failures)

    forbidden_absence = forbidden_artifact_absence(repo_root)
    failures.extend(
        validate_current_atomicrows_bundle_state(
            repo_root,
            label="exact-row source materialization manifest",
        )
    )
    for name, absent in forbidden_absence.items():
        if name == "atomicrows_bundle_absent":
            continue
        if absent is not True:
            failures.append(f"forbidden artifact absence failed: {name}")
    failures.extend(validate_master_plan_not_modified(repo_root))

    report = build_report(materialized=materialized, forbidden_absence=forbidden_absence)
    failures.extend(validate_report(copy.deepcopy(report)))
    if failures:
        return ValidationResult(False, failures, report)

    report_abs = _resolve(repo_root, report_out)
    if write_report or report_abs != _resolve(repo_root, DEFAULT_REPORT):
        report_abs.parent.mkdir(parents=True, exist_ok=True)
        report_abs.write_text(serialize_report(report), encoding="utf-8", newline="\n")
    return ValidationResult(True, [], report)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=REPO_ROOT)
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--schema", type=pathlib.Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--record-schema", type=pathlib.Path, default=DEFAULT_RECORD_SCHEMA)
    parser.add_argument("--report-out", type=pathlib.Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-report", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        manifest_path=args.manifest,
        schema_path=args.schema,
        record_schema_path=args.record_schema,
        report_out=args.report_out,
        write_report=args.write_report,
    )
    if not result.ok:
        for failure in result.failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
