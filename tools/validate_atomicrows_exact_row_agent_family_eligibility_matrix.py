#!/usr/bin/env python3
"""Validate the AtomicRows D2/E0 exact-row agent-family eligibility matrix."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import generate_atomicrows_exact_row_agent_family_eligibility_matrix as matrix_generator
from tools import generate_atomicrows_exact_row_source_files as source_generator
from tools import validate_atomicrows_exact_row_source_materialization_manifest as source_gate


REPO_ROOT = _REPO_ROOT
DEFAULT_MANIFEST = matrix_generator.DEFAULT_MANIFEST
DEFAULT_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_exact_row_agent_family_eligibility_matrix.schema.json"
)
DEFAULT_RECORD_SCHEMA = pathlib.Path(
    "schemas/atomicrows/atomicrows_exact_row_agent_family_eligibility_record.schema.json"
)
DEFAULT_REPORT = pathlib.Path(matrix_generator.REPORT_PATH)

SUCCESS_MARKER = "QTT_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_OK"
FAILURE_MARKER = "QTT_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_FAILED"
REPORT_ID = "ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_REPORT"
VALIDATION_STATUS = "PASS"
OVERLAY_SUCCESS_STATE = (
    "STATIC_METADATA_ONLY_READY_FOR_FUTURE_SCORING_POLICY_AND_RANKING_GATES"
)

FORBIDDEN_ARTIFACTS = (
    source_generator.FUTURE_BUNDLE_PATH,
    source_generator.FUTURE_BUNDLE_SHA_PATH,
)

FORBIDDEN_COMPUTED_ROW_FIELDS = {
    "agent_binding_score",
    "lifecycle_status_score",
    "owner_override_score",
    "platform_applicability_score",
    "market_type_applicability_score",
    "strategy_fit_score",
    "latency_fit_score",
    "risk_fit_score",
    "replay_paper_score",
    "optimizer_score",
    "runtime_readiness_score",
    "quantum_applicability_score",
    "expected_net_profit_score",
    "drawdown_penalty",
    "complexity_penalty",
    "source_currentness_penalty",
    "execution_cost_penalty",
    "owner_priority_boost",
    "quantum_boost",
    "final_selection_score",
    "score_breakdown",
    "rank",
    "rank_order",
    "selected_stack_id",
    "selected_parameter_families",
    "selected_algorithm_families",
    "optimizer_output",
    "replay_result",
    "paper_result",
    "profit_result",
    "latency_superiority_result",
    "execution_superiority_result",
    "quantum_advantage_result",
}

NUMERIC_OUTPUT_FIELDS = {
    "expected_profit_value",
    "expected_net_profit_value",
    "cost_adjusted_net_profit",
    "alpha_evidence",
    "positive_live_performance",
    "replay_success",
    "paper_success",
}


@dataclass
class SourceRows:
    rows: list[dict[str, Any]]
    row_by_id: dict[str, dict[str, Any]]
    row_digest_by_id: dict[str, str]
    family_counts: dict[str, int]
    family_ranges: dict[str, tuple[int, int]]
    source_file_count: int


@dataclass
class ValidationResult:
    ok: bool
    failures: list[str]
    report: dict[str, Any] | None = None


def _resolve(repo_root: pathlib.Path, path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else repo_root / path


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = source_generator.load_yaml(path)
    if not isinstance(value, dict):
        raise ValueError(f"manifest root must be an object: {path}")
    return value


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _scalar_type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return True


def schema_subset_failures(payload: dict[str, Any], schema: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if schema.get("type") == "object" and not isinstance(payload, dict):
        return [f"{label} must be an object"]
    for field in schema.get("required", []):
        if field not in payload:
            failures.append(f"{label}.{field} is required")
    if schema.get("additionalProperties") is False:
        allowed = set(_mapping(schema.get("properties")))
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
        if isinstance(expected_type, str) and not _scalar_type_matches(value, expected_type):
            failures.append(f"{label}.{field} must be a {expected_type}")
        if "enum" in rules and value not in rules["enum"]:
            failures.append(f"{label}.{field} must be one of {rules['enum']!r}")
        if expected_type == "array":
            if "minItems" in rules and isinstance(value, list) and len(value) < int(rules["minItems"]):
                failures.append(f"{label}.{field} must have at least {rules['minItems']} item(s)")
            item_rules = _mapping(rules.get("items"))
            if item_rules:
                for index, item in enumerate(value if isinstance(value, list) else []):
                    if item_rules.get("type") == "object" and isinstance(item, dict):
                        failures.extend(
                            schema_subset_failures(item, item_rules, f"{label}.{field}[{index}]")
                        )
                    elif "type" in item_rules and not _scalar_type_matches(item, item_rules["type"]):
                        failures.append(f"{label}.{field}[{index}] must be a {item_rules['type']}")
        if expected_type == "object" and isinstance(value, dict):
            failures.extend(schema_subset_failures(value, rules, f"{label}.{field}"))
    return failures


def _digest_source_line(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def _expected_stable_identity(row: dict[str, Any]) -> str:
    return (
        f"{row['row_id']}::{row['row_index']}::{row['family_id']}::"
        f"{row['source_file_path']}"
    )


def load_source_rows(repo_root: pathlib.Path) -> tuple[list[str], SourceRows]:
    failures: list[str] = []
    exact_dir = repo_root / source_generator.EXACT_ROW_SOURCES_DIR
    if not exact_dir.is_dir():
        failures.append("exact-row source directory missing")
        return failures, SourceRows([], {}, {}, {}, {}, 0)

    actual_files = tuple(sorted(path.name for path in exact_dir.glob("*.exact_rows.jsonl")))
    expected_files = source_generator.expected_file_names()
    if actual_files != expected_files:
        failures.append(
            "exact-row source file set mismatch: expected "
            + ", ".join(expected_files)
            + "; got "
            + ", ".join(actual_files)
        )

    rows: list[dict[str, Any]] = []
    row_by_id: dict[str, dict[str, Any]] = {}
    digest_by_id: dict[str, str] = {}
    family_counts: dict[str, int] = {}
    family_indexes: dict[str, list[int]] = {}
    seen_ids: set[str] = set()

    for plan in source_generator.build_family_plans():
        path = repo_root / pathlib.Path(plan.exact_rows_file_path)
        if not path.exists():
            failures.append(f"missing exact-row source file: {plan.exact_rows_file_path}")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) != plan.row_count:
            failures.append(f"{plan.family_id} source row count must be {plan.row_count}")
        for line_number, line in enumerate(lines, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"{plan.exact_rows_file_path}:{line_number} invalid JSON: {exc}")
                continue
            row_id = row.get("row_id")
            if not isinstance(row_id, str):
                failures.append(f"{plan.exact_rows_file_path}:{line_number} row_id must be string")
                continue
            if row_id in seen_ids:
                failures.append(f"duplicate source row_id: {row_id}")
            seen_ids.add(row_id)
            rows.append(row)
            row_by_id[row_id] = row
            digest_by_id[row_id] = _digest_source_line(line)
            family_counts[plan.family_id] = family_counts.get(plan.family_id, 0) + 1
            if isinstance(row.get("row_index"), int) and not isinstance(row.get("row_index"), bool):
                family_indexes.setdefault(plan.family_id, []).append(row["row_index"])

    family_ranges: dict[str, tuple[int, int]] = {}
    for family_id, indexes in family_indexes.items():
        if indexes:
            family_ranges[family_id] = (min(indexes), max(indexes))
    return failures, SourceRows(
        rows=rows,
        row_by_id=row_by_id,
        row_digest_by_id=digest_by_id,
        family_counts=family_counts,
        family_ranges=family_ranges,
        source_file_count=len(actual_files),
    )


def validate_manifest_payload(
    manifest: dict[str, Any],
    schema: dict[str, Any],
    record_schema: dict[str, Any],
) -> list[str]:
    failures = schema_subset_failures(manifest, schema, "manifest")
    expected_values = {
        "manifest_id": matrix_generator.MANIFEST_ID,
        "manifest_version": matrix_generator.MANIFEST_VERSION,
        "repair_pr_id": matrix_generator.REPAIR_PR_ID,
        "authority_class": matrix_generator.AUTHORITY_CLASS,
        "source_materialization_manifest_ref": source_gate.DEFAULT_MANIFEST.as_posix(),
        "source_exact_row_directory": source_generator.EXACT_ROW_SOURCES_DIR.as_posix() + "/",
        "expected_source_family_file_count": source_generator.EXPECTED_FAMILY_COUNT,
        "expected_exact_row_record_count": source_generator.EXPECTED_TOTAL_ROWS,
        "generated_report_path": matrix_generator.REPORT_PATH,
    }
    for field, expected in expected_values.items():
        if manifest.get(field) != expected:
            failures.append(f"manifest.{field} must be {expected!r}")

    overlay = _mapping(manifest.get("scoring_ranking_readiness_overlay"))
    if overlay.get("authority_class") != matrix_generator.OVERLAY_AUTHORITY_CLASS:
        failures.append("manifest.scoring_ranking_readiness_overlay.authority_class mismatch")
    if overlay.get("source_exact_row_count") != source_generator.EXPECTED_TOTAL_ROWS:
        failures.append("overlay.source_exact_row_count must be 4183")
    if overlay.get("coverage_required") is not True:
        failures.append("overlay.coverage_required must be true")
    if overlay.get("future_consumer_prs") != list(matrix_generator.FUTURE_CONSUMER_PRS):
        failures.append("overlay.future_consumer_prs must match D2/E0 future consumer list")
    if overlay.get("future_score_component_input_labels") != list(
        matrix_generator.FUTURE_SCORE_COMPONENT_INPUT_LABELS
    ):
        failures.append("overlay.future_score_component_input_labels mismatch")
    if overlay.get("future_stack_role_input_labels") != list(
        matrix_generator.FUTURE_STACK_ROLE_LABELS
    ):
        failures.append("overlay.future_stack_role_input_labels mismatch")
    future_handoff = _mapping(overlay.get("future_handoff"))
    if future_handoff.get("status") != OVERLAY_SUCCESS_STATE:
        failures.append("overlay.future_handoff.status mismatch")

    distribution = _list_of_mappings(manifest.get("expected_family_distribution"))
    expected_distribution = matrix_generator._family_distribution()
    if distribution != expected_distribution:
        failures.append("manifest.expected_family_distribution must match exact source family distribution")

    family_policies = _list_of_mappings(manifest.get("family_policies"))
    if len(family_policies) != source_generator.EXPECTED_FAMILY_COUNT:
        failures.append("manifest.family_policies must contain 15 policies")
    if [policy.get("family_id") for policy in family_policies] != [
        plan.family_id for plan in source_generator.build_family_plans()
    ]:
        failures.append("manifest.family_policies must be ordered by canonical family id")

    records = _list_of_mappings(manifest.get("row_coverage_records"))
    if len(records) != source_generator.EXPECTED_TOTAL_ROWS:
        failures.append("manifest.row_coverage_records must contain 4183 records")
    for index, record in enumerate(records[:3] + records[-3:]):
        failures.extend(schema_subset_failures(record, record_schema, f"row_sample[{index}]"))

    extension_slots = _mapping(manifest.get("extension_slots"))
    if set(extension_slots) != set(matrix_generator.EXTENSION_SLOT_IDS):
        failures.append("manifest.extension_slots must match required D2/E0 extension slots")
    for slot_id, slot in extension_slots.items():
        slot_map = _mapping(slot)
        required_true = (
            "future_versioned_pr_required",
            "manifest_update_required",
            "validator_update_required",
            "generated_report_update_required",
            "tests_required",
            "no_live_authority_by_default",
            "no_backend_authority_by_default",
            "no_connector_authority_by_default",
            "no_profit_evidence_by_default",
        )
        for field in required_true:
            if slot_map.get(field) is not True:
                failures.append(f"manifest.extension_slots.{slot_id}.{field} must be true")
    return failures


def _iter_nested(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _iter_nested(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_nested(child)


def _count_forbidden_computed_fields(records: Sequence[dict[str, Any]]) -> int:
    count = 0
    for record in records:
        count += len(set(record) & FORBIDDEN_COMPUTED_ROW_FIELDS)
    return count


def _count_numeric_output_fields(records: Sequence[dict[str, Any]]) -> int:
    count = 0
    forbidden_keys = FORBIDDEN_COMPUTED_ROW_FIELDS | NUMERIC_OUTPUT_FIELDS
    for record in records:
        for key, value in record.items():
            if key in forbidden_keys and isinstance(value, (int, float)) and not isinstance(value, bool):
                count += 1
    return count


def _count_key_presence(records: Sequence[dict[str, Any]], keys: set[str]) -> int:
    return sum(1 for record in records if set(record) & keys)


def _forbidden_bool_counts(records: Sequence[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for record in records if record.get(field) is True)
        for field in matrix_generator.FORBIDDEN_AUTHORITY_BOOL_FIELDS
    }


def _validate_row_records(
    manifest: dict[str, Any],
    source_rows: SourceRows,
    record_schema: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    records = _list_of_mappings(manifest.get("row_coverage_records"))
    record_ids = [record.get("exact_row_id") for record in records]
    record_id_set = {record_id for record_id in record_ids if isinstance(record_id, str)}
    duplicate_ids = sorted(
        row_id for row_id in record_id_set if record_ids.count(row_id) > 1
    )
    missing_ids = sorted(set(source_rows.row_by_id) - record_id_set)
    unexpected_ids = sorted(record_id_set - set(source_rows.row_by_id))

    if duplicate_ids:
        failures.append("duplicate row coverage records: " + ", ".join(duplicate_ids[:10]))
    if missing_ids:
        failures.append("missing row coverage records: " + ", ".join(missing_ids[:10]))
    if unexpected_ids:
        failures.append("unexpected row coverage records: " + ", ".join(unexpected_ids[:10]))

    expected_order = [
        row["row_id"]
        for row in sorted(source_rows.rows, key=lambda item: (item["family_id"], item["row_index"]))
    ]
    if record_ids != expected_order:
        failures.append("row_coverage_records must be ordered by family_id then row_index")

    scoring_decisions_seen: list[str] = []
    matrix_decisions_seen: list[str] = []
    for index, record in enumerate(records, start=1):
        failures.extend(schema_subset_failures(record, record_schema, f"row_coverage_records[{index}]"))
        row_id = record.get("exact_row_id")
        if not isinstance(row_id, str) or row_id not in source_rows.row_by_id:
            continue
        source_row = source_rows.row_by_id[row_id]
        expected = matrix_generator.build_row_coverage_record(
            {
                **source_row,
                "_source_record_digest": source_rows.row_digest_by_id[row_id],
            }
        )
        if record != expected:
            for field, expected_value in expected.items():
                if record.get(field) != expected_value:
                    failures.append(f"{row_id}.{field} does not match deterministic D2/E0 record")
                    break
        if record.get("source_record_digest") != source_rows.row_digest_by_id[row_id]:
            failures.append(f"{row_id}.source_record_digest mismatch")
        if record.get("source_record_stable_identity") != _expected_stable_identity(source_row):
            failures.append(f"{row_id}.source_record_stable_identity mismatch")
        if record.get("scoring_readiness_decision") not in matrix_generator.SCORING_READINESS_DECISIONS:
            failures.append(f"{row_id}.scoring_readiness_decision is not allowed")
        scoring_decisions_seen.append(str(record.get("scoring_readiness_decision")))
        matrix_decisions_seen.append(str(record.get("agent_family_eligibility_decision")))
        for field in matrix_generator.FORBIDDEN_AUTHORITY_BOOL_FIELDS:
            if record.get(field) is not False:
                failures.append(f"{row_id}.{field} must be false")
        allowed_classes = record.get("allowed_agent_family_classes")
        if not isinstance(allowed_classes, list) or not allowed_classes:
            failures.append(f"{row_id}.allowed_agent_family_classes must be a non-empty list")
        if any(
            allowed not in matrix_generator.ALLOWED_AGENT_FAMILY_CLASSES
            for allowed in allowed_classes if isinstance(allowed, str)
        ):
            failures.append(f"{row_id}.allowed_agent_family_classes contains unknown class")
        blocked = record.get("blocked_authority_classes")
        if blocked != list(matrix_generator.BLOCKED_AUTHORITY_CLASSES):
            failures.append(f"{row_id}.blocked_authority_classes must include the canonical block list")
        if set(record.get("eligible_future_score_components", ())) - set(
            matrix_generator.FUTURE_SCORE_COMPONENT_INPUT_LABELS
        ):
            failures.append(f"{row_id}.eligible_future_score_components contains unknown label")
        if set(record.get("eligible_future_stack_roles", ())) - set(
            matrix_generator.FUTURE_STACK_ROLE_LABELS
        ):
            failures.append(f"{row_id}.eligible_future_stack_roles contains unknown role")
        if not record.get("eligible_future_stack_roles"):
            failures.append(f"{row_id}.eligible_future_stack_roles must not be empty")
        for blocked_role in _list_of_mappings(record.get("blocked_future_stack_roles")):
            if not blocked_role.get("block_reason_code"):
                failures.append(f"{row_id}.blocked_future_stack_roles entries require block_reason_code")

    forbidden_bool_counts = _forbidden_bool_counts(records)
    computed_score_field_count = _count_forbidden_computed_fields(records)
    numeric_ranking_output_count = _count_numeric_output_fields(records)
    selected_stack_output_count = _count_key_presence(records, {"selected_stack_id", "selected_parameter_families", "selected_algorithm_families"})
    optimizer_output_count = _count_key_presence(records, {"optimizer_output"})
    replay_paper_result_count = _count_key_presence(records, {"replay_result", "paper_result", "replay_paper_result"})

    if computed_score_field_count:
        failures.append("computed score fields are forbidden in D2/E0 row records")
    if numeric_ranking_output_count:
        failures.append("numeric score/ranking/profit outputs are forbidden in D2/E0 row records")
    if selected_stack_output_count:
        failures.append("selected stack outputs are forbidden in D2/E0 row records")
    if optimizer_output_count:
        failures.append("optimizer outputs are forbidden in D2/E0 row records")
    if replay_paper_result_count:
        failures.append("replay/paper result outputs are forbidden in D2/E0 row records")

    counts = {
        "matrix_coverage_count": len(records),
        "scoring_readiness_coverage_count": len(scoring_decisions_seen),
        "missing_row_count": len(missing_ids),
        "duplicate_row_count": len(duplicate_ids),
        "unexpected_row_count": len(unexpected_ids),
        "computed_score_field_count": computed_score_field_count,
        "numeric_ranking_output_count": numeric_ranking_output_count,
        "selected_stack_output_count": selected_stack_output_count,
        "optimizer_output_count": optimizer_output_count,
        "replay_paper_result_count": replay_paper_result_count,
        **forbidden_bool_counts,
    }
    return failures, counts


def validate_family_distribution(source_rows: SourceRows) -> list[str]:
    failures: list[str] = []
    for plan in source_generator.build_family_plans():
        if source_rows.family_counts.get(plan.family_id) != plan.row_count:
            failures.append(f"{plan.family_id} row count must be {plan.row_count}")
        if source_rows.family_ranges.get(plan.family_id) != (
            plan.start_row_index,
            plan.end_row_index,
        ):
            failures.append(
                f"{plan.family_id} row range must be {plan.start_row_index}-{plan.end_row_index}"
            )
    if sum(source_rows.family_counts.values()) != source_generator.EXPECTED_TOTAL_ROWS:
        failures.append("total source row count must be 4183")
    return failures


def validate_registry_refs(repo_root: pathlib.Path, manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    ref_fields = (
        "agent_family_registry_refs",
        "agent_algorithm_registry_refs",
        "atomicrows_parameter_agent_binding_refs",
        "owner_governance_refs",
    )
    for field in ref_fields:
        refs = _list_of_mappings(manifest.get(field))
        if not refs:
            failures.append(f"manifest.{field} must not be empty")
        for ref in refs:
            registry_path = ref.get("registry_path")
            if isinstance(registry_path, str) and not (repo_root / registry_path).exists():
                failures.append(f"referenced registry missing: {registry_path}")
            report_path = ref.get("report_path")
            if isinstance(report_path, str) and not (repo_root / report_path).exists():
                failures.append(f"referenced report missing: {report_path}")
            validator_path = ref.get("validator_path")
            if isinstance(validator_path, str) and not (repo_root / validator_path).exists():
                failures.append(f"referenced validator missing: {validator_path}")
    return failures


def validate_forbidden_artifacts(repo_root: pathlib.Path) -> tuple[list[str], dict[str, bool]]:
    checks = {
        "AtomicRows.bundle.jsonl": not (repo_root / source_generator.FUTURE_BUNDLE_PATH).exists(),
        "AtomicRows.bundle.sha256": not (repo_root / source_generator.FUTURE_BUNDLE_SHA_PATH).exists(),
    }
    failures = [
        f"forbidden artifact exists: {name}"
        for name, absent in checks.items()
        if absent is not True
    ]
    return failures, checks


def validate_master_plan_not_modified(repo_root: pathlib.Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", "docs/master_plan/QTT_MasterPlan_Current.md"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return [f"could not verify master plan diff: {completed.stderr.strip()}"]
    if completed.stdout.strip():
        return ["docs/master_plan/QTT_MasterPlan_Current.md must remain unchanged"]
    return []


def _report_distribution(source_rows: SourceRows) -> dict[str, int]:
    return {
        plan.family_id: source_rows.family_counts.get(plan.family_id, 0)
        for plan in source_generator.build_family_plans()
    }


def build_report(
    *,
    manifest: dict[str, Any],
    source_rows: SourceRows,
    row_counts: dict[str, Any],
    forbidden_artifact_checks: dict[str, bool],
    validation_errors: list[str],
) -> dict[str, Any]:
    family_expected = {
        plan.family_id: plan.row_count for plan in source_generator.build_family_plans()
    }
    quantum_records = [
        record
        for record in _list_of_mappings(manifest.get("row_coverage_records"))
        if record.get("family_id") in source_generator.QUANTUM_FORWARD_FAMILY_IDS
    ]
    family_009 = [
        record
        for record in _list_of_mappings(manifest.get("row_coverage_records"))
        if record.get("family_id") == source_generator.AGENT_GOVERNANCE_FAMILY_ID
    ]
    result_ok = not validation_errors
    return {
        "report_id": REPORT_ID,
        "manifest_id": matrix_generator.MANIFEST_ID,
        "validator_name": "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py",
        "validation_status": VALIDATION_STATUS if result_ok else "FAIL",
        "source_family_file_count": source_rows.source_file_count,
        "source_exact_row_record_count": len(source_rows.rows),
        "expected_exact_row_record_count": source_generator.EXPECTED_TOTAL_ROWS,
        "matrix_coverage_count": row_counts.get("matrix_coverage_count", 0),
        "scoring_readiness_coverage_count": row_counts.get(
            "scoring_readiness_coverage_count", 0
        ),
        "missing_row_count": row_counts.get("missing_row_count", 0),
        "duplicate_row_count": row_counts.get("duplicate_row_count", 0),
        "unexpected_row_count": row_counts.get("unexpected_row_count", 0),
        "family_distribution_observed": _report_distribution(source_rows),
        "family_distribution_expected": family_expected,
        "family_distribution_match": _report_distribution(source_rows) == family_expected,
        "all_rows_covered": row_counts.get("matrix_coverage_count", 0)
        == source_generator.EXPECTED_TOTAL_ROWS
        and row_counts.get("missing_row_count", 0) == 0
        and row_counts.get("unexpected_row_count", 0) == 0,
        "all_rows_scoring_readiness_covered": row_counts.get(
            "scoring_readiness_coverage_count", 0
        )
        == source_generator.EXPECTED_TOTAL_ROWS,
        "deny_by_default_preserved": all(
            record.get("live_order_authority_allowed") is False
            and record.get("final_order_submission_authority_allowed") is False
            and record.get("live_trade_intent_authority_allowed") is False
            for record in _list_of_mappings(manifest.get("row_coverage_records"))
        ),
        "explicit_allow_count": sum(
            1
            for record in _list_of_mappings(manifest.get("row_coverage_records"))
            if record.get("allowed_agent_family_classes")
        ),
        "explicit_block_count": sum(
            len(record.get("blocked_authority_classes", []))
            for record in _list_of_mappings(manifest.get("row_coverage_records"))
        ),
        "live_order_authority_count": row_counts.get("live_order_authority_allowed", 0),
        "final_order_submission_authority_count": row_counts.get(
            "final_order_submission_authority_allowed", 0
        ),
        "live_trade_intent_authority_count": row_counts.get(
            "live_trade_intent_authority_allowed", 0
        ),
        "scoring_execution_allowed_count": row_counts.get("scoring_execution_allowed", 0),
        "ranking_execution_allowed_count": row_counts.get("ranking_execution_allowed", 0),
        "selection_execution_allowed_count": row_counts.get("selection_execution_allowed", 0),
        "candidate_stack_generation_allowed_count": row_counts.get(
            "candidate_stack_generation_allowed", 0
        ),
        "optimizer_execution_allowed_count": row_counts.get("optimizer_execution_allowed", 0),
        "replay_execution_allowed_count": row_counts.get("replay_execution_allowed", 0),
        "paper_execution_allowed_count": row_counts.get("paper_execution_allowed", 0),
        "quantum_backend_authority_count": row_counts.get(
            "quantum_backend_authority_allowed", 0
        ),
        "quantum_simulator_authority_count": row_counts.get(
            "quantum_simulator_authority_allowed", 0
        ),
        "quantum_provider_authority_count": row_counts.get(
            "quantum_provider_authority_allowed", 0
        ),
        "source_fact_authority_count": row_counts.get("source_fact_authority_allowed", 0),
        "connector_authority_count": row_counts.get("connector_authority_allowed", 0),
        "runtime_cash_authority_count": row_counts.get("runtime_cash_authority_allowed", 0),
        "bundle_authority_count": row_counts.get("bundle_authority_allowed", 0),
        "sha_freeze_authority_count": row_counts.get("sha_freeze_authority_allowed", 0),
        "final_readiness_authority_count": row_counts.get(
            "final_readiness_authority_allowed", 0
        ),
        "computed_score_field_count": row_counts.get("computed_score_field_count", 0),
        "numeric_ranking_output_count": row_counts.get("numeric_ranking_output_count", 0),
        "selected_stack_output_count": row_counts.get("selected_stack_output_count", 0),
        "optimizer_output_count": row_counts.get("optimizer_output_count", 0),
        "replay_paper_result_count": row_counts.get("replay_paper_result_count", 0),
        "profit_evidence_count": row_counts.get("profit_evidence_allowed", 0),
        "expected_profit_proof_count": row_counts.get("expected_profit_proof_allowed", 0),
        "latency_superiority_evidence_count": row_counts.get(
            "latency_superiority_evidence_allowed", 0
        ),
        "execution_superiority_evidence_count": row_counts.get(
            "execution_superiority_evidence_allowed", 0
        ),
        "quantum_advantage_evidence_count": row_counts.get(
            "quantum_advantage_evidence_allowed", 0
        ),
        "quantum_family_metadata_only_result": {
            "families": sorted(source_generator.QUANTUM_FORWARD_FAMILY_IDS),
            "row_count": len(quantum_records),
            "metadata_only": all(
                record.get("quantum_backend_authority_allowed") is False
                and record.get("quantum_simulator_authority_allowed") is False
                and record.get("quantum_provider_authority_allowed") is False
                and record.get("quantum_advantage_evidence_allowed") is False
                for record in quantum_records
            ),
        },
        "agent_governance_family_non_live_result": {
            "family_id": source_generator.AGENT_GOVERNANCE_FAMILY_ID,
            "row_count": len(family_009),
            "non_live": all(record.get("live_order_authority_allowed") is False for record in family_009),
        },
        "source_connector_family_block_result": {
            "family_id": "010_source_evidence_connector_semantic",
            "source_fact_authority_count": 0,
            "connector_authority_count": 0,
        },
        "capital_cash_family_runtime_cash_block_result": {
            "family_id": "006_capital_sizing_cash",
            "runtime_cash_authority_count": 0,
        },
        "latency_family_superiority_claim_block_result": {
            "family_id": "007_latency_routing",
            "latency_superiority_evidence_count": 0,
        },
        "replay_paper_family_execution_result_block_result": {
            "family_id": "011_replay_paper_validation",
            "replay_execution_allowed_count": 0,
            "paper_execution_allowed_count": 0,
            "replay_paper_result_count": 0,
        },
        "scoring_ranking_family_execution_block_result": {
            "family_id": "002_scoring_ranking",
            "scoring_execution_allowed_count": 0,
            "ranking_execution_allowed_count": 0,
        },
        "scoring_ranking_readiness_overlay_status": OVERLAY_SUCCESS_STATE,
        "future_pr84_handoff_ready": True,
        "future_pr85_handoff_ready": True,
        "future_pr86_handoff_ready": True,
        "future_pr87_handoff_ready": True,
        "future_pr88_handoff_ready": True,
        "future_pr89_handoff_ready": True,
        "future_pr90_plus_handoff_ready": True,
        "forbidden_artifact_checks": forbidden_artifact_checks,
        "master_plan_diff_check": {
            "path": "docs/master_plan/QTT_MasterPlan_Current.md",
            "unchanged": True,
        },
        "future_repair_pr_e_handoff_state": "REPAIR_PR_E_BUNDLE_MATERIALIZATION_REQUIRED_FUTURE_ONLY_NOT_EXECUTED",
        "validation_errors": validation_errors,
        "validation_warnings": [],
        "result_marker": SUCCESS_MARKER if result_ok else FAILURE_MARKER,
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("validation_status") != VALIDATION_STATUS:
        failures.append("report.validation_status must be PASS")
    zero_fields = (
        "missing_row_count",
        "duplicate_row_count",
        "unexpected_row_count",
        "live_order_authority_count",
        "final_order_submission_authority_count",
        "live_trade_intent_authority_count",
        "scoring_execution_allowed_count",
        "ranking_execution_allowed_count",
        "selection_execution_allowed_count",
        "candidate_stack_generation_allowed_count",
        "optimizer_execution_allowed_count",
        "replay_execution_allowed_count",
        "paper_execution_allowed_count",
        "quantum_backend_authority_count",
        "quantum_simulator_authority_count",
        "quantum_provider_authority_count",
        "source_fact_authority_count",
        "connector_authority_count",
        "runtime_cash_authority_count",
        "bundle_authority_count",
        "sha_freeze_authority_count",
        "final_readiness_authority_count",
        "computed_score_field_count",
        "numeric_ranking_output_count",
        "selected_stack_output_count",
        "optimizer_output_count",
        "replay_paper_result_count",
        "profit_evidence_count",
        "expected_profit_proof_count",
        "latency_superiority_evidence_count",
        "execution_superiority_evidence_count",
        "quantum_advantage_evidence_count",
    )
    for field in zero_fields:
        if report.get(field) != 0:
            failures.append(f"report.{field} must be 0")
    if report.get("source_family_file_count") != source_generator.EXPECTED_FAMILY_COUNT:
        failures.append("report.source_family_file_count must be 15")
    if report.get("source_exact_row_record_count") != source_generator.EXPECTED_TOTAL_ROWS:
        failures.append("report.source_exact_row_record_count must be 4183")
    if report.get("matrix_coverage_count") != source_generator.EXPECTED_TOTAL_ROWS:
        failures.append("report.matrix_coverage_count must be 4183")
    if report.get("scoring_readiness_coverage_count") != source_generator.EXPECTED_TOTAL_ROWS:
        failures.append("report.scoring_readiness_coverage_count must be 4183")
    if report.get("family_distribution_match") is not True:
        failures.append("report.family_distribution_match must be true")
    if report.get("all_rows_covered") is not True:
        failures.append("report.all_rows_covered must be true")
    if report.get("all_rows_scoring_readiness_covered") is not True:
        failures.append("report.all_rows_scoring_readiness_covered must be true")
    if report.get("deny_by_default_preserved") is not True:
        failures.append("report.deny_by_default_preserved must be true")
    if report.get("result_marker") != SUCCESS_MARKER:
        failures.append("report.result_marker mismatch")
    if report != json.loads(serialize_report(report)):
        failures.append("report serialization must be deterministic")
    return failures


def validate(
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    manifest_path: pathlib.Path = DEFAULT_MANIFEST,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    record_schema_path: pathlib.Path = DEFAULT_RECORD_SCHEMA,
    report_out: pathlib.Path = DEFAULT_REPORT,
) -> ValidationResult:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    try:
        manifest = load_manifest(_resolve(repo_root, manifest_path))
        schema = load_json(_resolve(repo_root, schema_path))
        record_schema = load_json(_resolve(repo_root, record_schema_path))
    except Exception as exc:
        return ValidationResult(False, [f"could not load D2/E0 validation input: {exc}"])

    failures.extend(validate_manifest_payload(manifest, schema, record_schema))
    source_failures, source_rows = load_source_rows(repo_root)
    failures.extend(source_failures)
    failures.extend(validate_family_distribution(source_rows))
    failures.extend(validate_registry_refs(repo_root, manifest))
    row_failures, row_counts = _validate_row_records(manifest, source_rows, record_schema)
    failures.extend(row_failures)
    artifact_failures, forbidden_artifact_checks = validate_forbidden_artifacts(repo_root)
    failures.extend(artifact_failures)
    failures.extend(validate_master_plan_not_modified(repo_root))

    report = build_report(
        manifest=manifest,
        source_rows=source_rows,
        row_counts=row_counts,
        forbidden_artifact_checks=forbidden_artifact_checks,
        validation_errors=[] if not failures else failures,
    )
    if failures:
        return ValidationResult(False, failures, report)

    report_failures = validate_report(copy.deepcopy(report))
    if report_failures:
        return ValidationResult(False, report_failures, report)

    report_abs = _resolve(repo_root, report_out)
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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        repo_root=args.repo_root,
        manifest_path=args.manifest,
        schema_path=args.schema,
        record_schema_path=args.record_schema,
        report_out=args.report_out,
    )
    if not result.ok:
        for failure in result.failures:
            print(f"{FAILURE_MARKER}: {failure}", file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
