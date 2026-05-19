#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Iterable, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_master_plan_section_coverage_report as builder

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "master_plan"
    / "master_plan_section_coverage_report.schema.json"
)
SUCCESS_MARKER = "MASTER_PLAN_SECTION_COVERAGE_VALIDATION_OK"
FAILURE_MARKER = "MASTER_PLAN_SECTION_COVERAGE_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = "MASTER_PLAN_SECTION_COVERAGE_FINAL_INCOMPLETE"

ALLOWED_COVERAGE_CLASSES = {
    "EXECUTABLE_IMPLEMENTATION",
    "STATIC_CONTRACT",
    "SOURCE_EVIDENCE_DEPENDENT",
    "RUNTIME_RECEIPT_DEPENDENT",
    "OWNER_APPROVAL_DEPENDENT",
    "POLICY_ONLY",
    "RESEARCH_CANDIDATE",
    "QUARANTINE_REQUIRED",
    "RETIRED_NOT_USEFUL",
}

ALLOWED_CURRENT_STATUSES = {
    "NOT_STARTED",
    "PARTIAL",
    "STATIC_CONTRACT_IMPLEMENTED",
    "BLOCKED_SOURCE_EVIDENCE",
    "BLOCKED_REPLAY_PAPER_EVIDENCE",
    "BLOCKED_RUNTIME_RECEIPT",
    "BLOCKED_OWNER_APPROVAL",
    "RESEARCH_ROUTED",
    "QUARANTINED_UNPROVEN",
    "RETIRED_NOT_USEFUL",
    "COMPLETE_VERIFIED",
}

REQUIRED_ENTRY_FIELDS = set(builder.REGISTRY_ENTRY_FIELDS)
REQUIRED_AUTHORITY_BOUNDARY_FIELDS = set(builder.AUTHORITY_BOUNDARY_FIELDS)
COMPLETE_EVIDENCE_PATH_FIELDS = (
    "required_files",
    "required_tools",
    "required_schemas",
    "required_tests",
    "required_reports",
)
DEPENDENT_COVERAGE_CLASSES = {
    "SOURCE_EVIDENCE_DEPENDENT",
    "RUNTIME_RECEIPT_DEPENDENT",
    "OWNER_APPROVAL_DEPENDENT",
}
FINAL_COMPLETE_STATUSES = {
    "COMPLETE_VERIFIED",
    "STATIC_CONTRACT_IMPLEMENTED",
    "RETIRED_NOT_USEFUL",
}
PR_TRACKING_KEYS = {
    "completion_" + "pr",
    "completion_" + "pr" + "_number",
    "pending_" + "pr",
    "pending_" + "pr" + "_record",
    "pr" + "_number",
    "pull_" + "request",
    "pull_" + "request" + "_number",
}
ALLOWED_ROUTE_CLASSES = set(builder.ROUTE_CLASSES)
ALLOWED_ROUTE_CONFIDENCE_CLASSES = set(builder.ROUTE_CONFIDENCE_CLASSES)
ALLOWED_UNRESOLVED_REASON_CODES = set(builder.UNRESOLVED_REASON_CODES)
ALLOWED_QUANTUM_RELEVANCE_CLASSES = {
    "NONE",
    "QUANTUM_APPLICABILITY_METADATA",
    "QUBO_ISING_FORMULATION_CANDIDATE",
    "QAOA_VQE_ANNEALING_CANDIDATE",
    "QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE",
    "TRUE_QUANTUM_BACKEND_RECEIPT_GATED",
    "HYBRID_CLASSICAL_QUANTUM_ARBITRATION",
    "PORTFOLIO_CANDIDATE_SET_OPTIMIZATION",
    "LATENCY_AWARE_OPTIMIZATION_ROUTE",
}
QUANTUM_RELATED_ROUTE_CLASSES = {
    "QUANTUM_FORWARD_OPTIMIZATION_ROUTE",
    "QUANTUM_BACKEND_ROUTE",
    "OPTIMIZER_ARBITRATION_ROUTE",
    "LATENCY_COST_ROUTE",
}
EXPECTED_ROUTE_MAP_FIELDS = set(builder.ROUTE_MAP_FIELDS)
EXPECTED_ROUTE_ENTRY_FIELDS = set(builder.ROUTE_ENTRY_FIELDS)
EXPECTED_QUANTUM_METADATA_FIELDS = set(builder.QUANTUM_FORWARD_METADATA_FIELDS)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _load_json(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"JSON file is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"JSON file is invalid: {path}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"JSON file must contain an object: {path}"]
    return value, []


def _type_matches(value: Any, expected_type: str) -> bool:
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
    if expected_type == "null":
        return value is None
    return True


def _resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        raise ValueError(f"unsupported schema ref: {ref}")
    name = ref[len(prefix) :]
    defs = schema.get("$defs", {})
    target = defs.get(name)
    if not isinstance(target, dict):
        raise ValueError(f"missing schema ref target: {ref}")
    return target


def validate_json_schema_subset(
    value: Any,
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any] | None = None,
    path: str = "$",
) -> list[str]:
    root = schema if root_schema is None else root_schema
    if "$ref" in schema:
        try:
            schema = _resolve_ref(root, str(schema["$ref"]))
        except ValueError as exc:
            return [f"{path}: {exc}"]

    failures: list[str] = []
    if "const" in schema and value != schema["const"]:
        failures.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        failures.append(f"{path}: value {value!r} is not in enum")

    expected_type = schema.get("type")
    if isinstance(expected_type, str):
        if not _type_matches(value, expected_type):
            return [f"{path}: expected type {expected_type}"]
    elif isinstance(expected_type, list):
        if not any(_type_matches(value, item) for item in expected_type):
            return [f"{path}: expected one of types {', '.join(expected_type)}"]

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for field in required:
                if field not in value:
                    failures.append(f"{path}: missing required field {field}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for field, child_schema in properties.items():
                if field in value and isinstance(child_schema, dict):
                    failures.extend(
                        validate_json_schema_subset(
                            value[field],
                            child_schema,
                            root_schema=root,
                            path=f"{path}.{field}",
                        )
                    )
            if schema.get("additionalProperties") is False:
                unexpected = sorted(set(value) - set(properties))
                if unexpected:
                    failures.append(
                        f"{path}: unexpected fields {', '.join(unexpected)}"
                    )
    elif isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            failures.append(f"{path}: expected at least {min_items} items")
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for index, item in enumerate(value):
                failures.extend(
                    validate_json_schema_subset(
                        item,
                        items_schema,
                        root_schema=root,
                        path=f"{path}[{index}]",
                    )
                )
    return failures


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{path}.{key}"
            yield current, key, item
            yield from _walk(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            current = f"{path}[{index}]"
            yield current, f"[{index}]", item
            yield from _walk(item, current)


def _is_blocked_or_future(entry: dict[str, Any]) -> bool:
    status = entry.get("current_status")
    return (
        status in {"NOT_STARTED", "PARTIAL", "RESEARCH_ROUTED", "QUARANTINED_UNPROVEN"}
        or (isinstance(status, str) and status.startswith("BLOCKED_"))
    )


def _has_route(entry: dict[str, Any]) -> bool:
    return any(
        [
            entry.get("research_route"),
            entry.get("unblock_condition"),
            entry.get("required_receipts"),
            entry.get("quarantine_reason"),
            entry.get("retirement_reason"),
            entry.get("static_safety_stub"),
        ]
    )


def validate_registry_entries(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        label = f"coverage_entries[{index}]"
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
        if missing:
            failures.append(f"{label}: missing required fields {', '.join(missing)}")
        capability_id = entry.get("capability_id")
        if not isinstance(capability_id, str) or not capability_id:
            failures.append(f"{label}: capability_id must be a non-empty string")
        elif capability_id in seen_ids:
            failures.append(f"{label}: duplicate capability_id {capability_id}")
        else:
            seen_ids.add(capability_id)
        owner_section_ids = entry.get("owner_section_ids")
        if not isinstance(owner_section_ids, list) or not owner_section_ids:
            failures.append(f"{label}: owner_section_ids must be a non-empty list")
        for field in builder.LIST_FIELDS:
            if not isinstance(entry.get(field), list):
                failures.append(f"{label}.{field} must be a list")
        if entry.get("coverage_class") not in ALLOWED_COVERAGE_CLASSES:
            failures.append(f"{label}: coverage_class is not allowed")
        if entry.get("current_status") not in ALLOWED_CURRENT_STATUSES:
            failures.append(f"{label}: current_status is not allowed")
        if not isinstance(entry.get("retirement_allowed"), bool):
            failures.append(f"{label}.retirement_allowed must be boolean")
        authority_boundary = entry.get("authority_boundary")
        if not isinstance(authority_boundary, dict):
            failures.append(f"{label}.authority_boundary must be an object")
            continue
        missing_boundary = sorted(
            REQUIRED_AUTHORITY_BOUNDARY_FIELDS - set(authority_boundary)
        )
        if missing_boundary:
            failures.append(
                f"{label}.authority_boundary missing fields "
                + ", ".join(missing_boundary)
            )
        for field in builder.AUTHORITY_BOUNDARY_FIELDS:
            if authority_boundary.get(field) is not False:
                failures.append(
                    f"{label}.authority_boundary.{field} claims authority without "
                    "validated receipt evidence"
                )
    return failures


def validate_blocked_future_routing(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for entry in entries:
        capability_id = entry.get("capability_id", "<unknown>")
        if _is_blocked_or_future(entry) and not _has_route(entry):
            failures.append(
                f"{capability_id}: blocked or future item lacks research route, "
                "unblock condition, required receipt, quarantine reason, "
                "retirement reason, or static safety stub"
            )
        if entry.get("current_status") == "QUARANTINED_UNPROVEN" and not entry.get(
            "quarantine_reason"
        ):
            failures.append(f"{capability_id}: quarantined item lacks quarantine reason")
        if entry.get("current_status") == "RETIRED_NOT_USEFUL" and not entry.get(
            "retirement_reason"
        ):
            failures.append(f"{capability_id}: retired item lacks retirement reason")
    return failures


def validate_route_map(route_map: Mapping[str, Any], *, repo_root: pathlib.Path) -> list[str]:
    failures: list[str] = []
    missing = sorted(EXPECTED_ROUTE_MAP_FIELDS - set(route_map))
    if missing:
        return [f"route_map missing required fields: {', '.join(missing)}"]
    expected = {
        "route_map_id": "QTT_MASTER_PLAN_SECTION_COVERAGE_TRIAGE_ROUTES_V1_0",
        "route_map_version": "v1.0",
        "authority_class": "STATIC_CONTROL_PLANE_ROUTE_MAP_NOT_MASTER_PLAN_AUTHORITY",
        "repo_canonical_pr_label": "PR119",
        "roadmap_pr_label": "PR #102",
        "semantic_task_id": "ROADMAP-MASTER-PLAN-COVERAGE-TRIAGE-I",
        "source_manifest_reference": "docs/master_plan/generated/SectionManifest.json",
        "generated_report_path": "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
        "controller_decision_reference": (
            "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
            "#/roadmap_range_currentization/1"
        ),
        "no_old_coverage_ledger_reintroduction_flag": True,
        "no_runtime_live_order_profit_authority_created_flag": True,
        "no_source_connector_replay_paper_authority_created_flag": True,
        "no_quantum_backend_or_simulator_execution_created_flag": True,
        "no_master_plan_text_mutation_flag": True,
    }
    for field, expected_value in expected.items():
        if route_map.get(field) != expected_value:
            failures.append(f"route_map.{field} must be {expected_value!r}")

    discovery = route_map.get("existing_artifact_discovery_result")
    if not isinstance(discovery, Mapping):
        failures.append("route_map.existing_artifact_discovery_result must be an object")
    elif discovery.get("decision") != "EXISTING_MASTER_PLAN_SECTION_COVERAGE_FAMILY_EXTENDED":
        failures.append("route_map must extend the existing section coverage family")

    entries = route_map.get("route_entries")
    if not isinstance(entries, list) or not entries:
        return failures + ["route_map.route_entries must be a non-empty array"]
    sorted_entries = sorted(
        entries,
        key=lambda entry: (
            str(entry.get("section_id") or ""),
            str(entry.get("normalized_section_title") or ""),
        ),
    )
    if entries != sorted_entries:
        failures.append("route_map.route_entries must be sorted by section_id then title")

    manifest_path = repo_root / pathlib.Path(str(route_map.get("source_manifest_reference")))
    manifest, manifest_failures = _load_json(manifest_path)
    failures.extend(manifest_failures)
    manifest_ids: set[str] = set()
    if manifest is not None:
        manifest_ids = {
            str(section.get("canonical_id"))
            for section in manifest.get("sections", [])
            if isinstance(section, dict) and section.get("canonical_id")
        }

    seen: set[str] = set()
    route_classes: list[str] = []
    for index, entry in enumerate(entries, start=1):
        label = f"route_entries[{index}]"
        if not isinstance(entry, Mapping):
            failures.append(f"{label} must be an object")
            continue
        missing_entry = sorted(EXPECTED_ROUTE_ENTRY_FIELDS - set(entry))
        if missing_entry:
            failures.append(f"{label} missing required fields: {', '.join(missing_entry)}")
            continue
        section_id = str(entry.get("section_id") or "")
        if section_id in seen:
            failures.append(f"{label} duplicate section_id: {section_id}")
        seen.add(section_id)
        if manifest_ids and section_id not in manifest_ids:
            failures.append(f"{label} section_id not found in SectionManifest: {section_id}")

        route_class = str(entry.get("current_route_class") or "")
        route_classes.append(route_class)
        if route_class not in ALLOWED_ROUTE_CLASSES:
            failures.append(f"{label} invalid current_route_class: {route_class}")
        confidence = str(entry.get("route_confidence_class") or "")
        if confidence not in ALLOWED_ROUTE_CONFIDENCE_CLASSES:
            failures.append(f"{label} invalid route_confidence_class: {confidence}")

        for flag in (
            "no_authority_created_flag",
            "no_master_plan_text_mutation_flag",
            "no_old_coverage_ledger_flag",
        ):
            if entry.get(flag) is not True:
                failures.append(f"{label}.{flag} must be true")
        if not entry.get("route_owner_artifact"):
            failures.append(f"{label} must include route_owner_artifact")
        owner_path = repo_root / pathlib.Path(str(entry.get("route_owner_artifact") or ""))
        if entry.get("route_owner_artifact") and not owner_path.exists():
            failures.append(
                f"{label} route_owner_artifact missing: {entry.get('route_owner_artifact')}"
            )

        unresolved = entry.get("unresolved_reason_code_when_applicable")
        if route_class == "UNRESOLVED_DEFAULT_ROUTE":
            if unresolved not in ALLOWED_UNRESOLVED_REASON_CODES:
                failures.append(f"{label} unresolved route must include an allowed reason code")
            if confidence != "UNRESOLVED_EXPLICITLY":
                failures.append(f"{label} unresolved route must use UNRESOLVED_EXPLICITLY")
        elif unresolved is not None:
            failures.append(f"{label} resolved route must not include unresolved reason")

        metadata = entry.get("quantum_forward_metadata")
        if not isinstance(metadata, Mapping):
            failures.append(f"{label}.quantum_forward_metadata must be an object")
            continue
        metadata_missing = sorted(EXPECTED_QUANTUM_METADATA_FIELDS - set(metadata))
        if metadata_missing:
            failures.append(
                f"{label}.quantum_forward_metadata missing fields: {', '.join(metadata_missing)}"
            )
        relevance = str(metadata.get("quantum_relevance_class") or "")
        if relevance not in ALLOWED_QUANTUM_RELEVANCE_CLASSES:
            failures.append(f"{label} invalid quantum_relevance_class: {relevance}")
        if route_class in QUANTUM_RELATED_ROUTE_CLASSES and relevance == "NONE":
            failures.append(f"{label} quantum/optimizer/latency route needs quantum metadata")
        for flag in (
            "no_backend_execution_flag",
            "no_simulator_execution_flag",
            "no_optimizer_runtime_execution_flag",
            "no_quantum_advantage_claim_flag",
            "no_profit_or_latency_superiority_claim_flag",
        ):
            if metadata.get(flag) is not True:
                failures.append(f"{label}.quantum_forward_metadata.{flag} must be true")

    return failures


def _path_exists(repo_root: pathlib.Path, value: str) -> bool:
    return (repo_root / pathlib.Path(value)).exists()


def validate_complete_verified_evidence(
    entries: Sequence[dict[str, Any]],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    for entry in entries:
        if entry.get("current_status") != "COMPLETE_VERIFIED":
            continue
        capability_id = entry.get("capability_id", "<unknown>")
        for required_non_empty in ("required_files", "required_tests", "required_reports"):
            if not entry.get(required_non_empty):
                failures.append(
                    f"{capability_id}: COMPLETE_VERIFIED requires {required_non_empty}"
                )
        for field in COMPLETE_EVIDENCE_PATH_FIELDS:
            for rel_path in entry.get(field, []):
                if not _path_exists(repo_root, rel_path):
                    failures.append(
                        f"{capability_id}: COMPLETE_VERIFIED missing {field} path "
                        f"{rel_path}"
                    )
    return failures


def validate_no_pr_tracking_keys(value: Any) -> list[str]:
    failures: list[str] = []
    for path, key, _ in _walk(value):
        if key.lower() in PR_TRACKING_KEYS:
            failures.append(f"{path}: section coverage must not use PR tracking keys")
    return failures


def _removed_ledger_patterns() -> tuple[str, ...]:
    return (
        "MasterPlan" + "Implementation" + "Coverage" + "Ledger",
        "PR" + "Coverage" + "Ledger",
        "pending_" + "pr_record",
        "pending " + "PR record",
        "PR " + "ledger",
        "PR-" + "ledger",
        "coverage_" + "ledger_generator.py",
        "Coverage" + "Ledger.generated",
    )


def validate_no_removed_ledger_references(
    *,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    schema_path: pathlib.Path,
    report_path: pathlib.Path,
) -> list[str]:
    files = [
        registry_path,
        schema_path,
        pathlib.Path("tools") / "build_master_plan_section_coverage_report.py",
        pathlib.Path("tools") / "run_validation_gates.py",
    ]
    if report_path.exists():
        files.append(report_path)
    patterns = _removed_ledger_patterns()
    failures: list[str] = []
    for rel_path in files:
        path = repo_root / rel_path
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            if pattern in text:
                failures.append(
                    f"{rel_path.as_posix()}: removed implementation-ledger reference "
                    f"was reintroduced: {pattern}"
                )
    return failures


def _central_enum_values(config: Mapping[str, Any], field: str) -> list[str]:
    values = config.get(field)
    if not isinstance(values, list):
        return []
    if field == "parent_capability_group_enum":
        return [
            str(item.get("parent_capability_group_id"))
            for item in values
            if isinstance(item, Mapping) and item.get("parent_capability_group_id")
        ]
    if field == "market_taxonomy":
        return [
            str(item.get("market_id"))
            for item in values
            if isinstance(item, Mapping) and item.get("market_id")
        ]
    return [str(item) for item in values]


def validate_schema_enums_match_registry(
    *,
    registry: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> list[str]:
    config = registry.get("central_config", {})
    if not isinstance(config, Mapping):
        return ["central_config must be present in the section coverage registry"]
    defs = schema.get("$defs", {})
    if not isinstance(defs, Mapping):
        return ["schema $defs must be an object"]
    comparisons = (
        ("route_class_enum", "route_class"),
        ("route_confidence_class_enum", "route_confidence_class"),
        ("unresolved_reason_code_enum", "unresolved_reason_code"),
        ("parent_capability_group_enum", "parent_capability_group_id"),
        ("market_taxonomy", "market_id"),
        ("command_family_enum", "command_family"),
        ("command_scope_class_enum", "command_scope_class"),
        ("command_authority_class_enum", "command_authority_class"),
        ("command_owner_class_enum", "command_owner_class"),
        ("command_consumer_class_enum", "command_consumer_class"),
        ("command_status_enum", "command_status"),
        ("static_allowed_operation_enum", "static_allowed_operation"),
        ("future_gated_operation_enum", "future_gated_operation"),
        ("command_block_reason_enum", "command_block_reason"),
        (
            "explicit_future_market_candidate_family_enum",
            "explicit_future_market_candidate_family",
        ),
        ("forbidden_market_taxonomy_value_enum", "forbidden_market_taxonomy_value"),
    )
    failures: list[str] = []
    for registry_field, schema_def in comparisons:
        schema_values = defs.get(schema_def, {}).get("enum")
        registry_values = _central_enum_values(config, registry_field)
        if schema_values != registry_values:
            failures.append(
                f"schema enum {schema_def} must match registry {registry_field}"
            )
    return failures


def _section_ids_from_report(report: Mapping[str, Any]) -> list[str]:
    return [
        str(record.get("owner_section_id"))
        for record in report.get("section_coverage", [])
        if isinstance(record, Mapping)
    ]


def _rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    crosswalk = report.get("roadmap_crosswalk", {})
    if not isinstance(crosswalk, Mapping):
        return []
    return [row for row in crosswalk.get("rows", []) if isinstance(row, dict)]


def _command_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    matrix = report.get("command_matrix", {})
    if not isinstance(matrix, Mapping):
        return []
    return [row for row in matrix.get("rows", []) if isinstance(row, dict)]


def validate_roadmap_crosswalk(
    *,
    report: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    rows = _rows(report)
    section_ids = _section_ids_from_report(report)
    row_ids = [str(row.get("section_id")) for row in rows]
    if len(rows) != len(section_ids):
        failures.append("crosswalk row count must equal SectionManifest section count")
    if row_ids != section_ids:
        failures.append("crosswalk row ordering must match SectionManifest document order")
    duplicates = [section_id for section_id, count in Counter(row_ids).items() if count > 1]
    if duplicates:
        failures.append(f"crosswalk contains duplicate section IDs: {', '.join(sorted(duplicates))}")
    missing = sorted(set(section_ids) - set(row_ids))
    if missing:
        failures.append(f"crosswalk missing section IDs: {', '.join(missing[:20])}")

    config = registry.get("central_config", {})
    if not isinstance(config, Mapping):
        failures.append("registry central_config must be an object")
        config = {}
    route_classes = set(_central_enum_values(config, "route_class_enum"))
    confidence_classes = set(_central_enum_values(config, "route_confidence_class_enum"))
    parent_groups = set(_central_enum_values(config, "parent_capability_group_enum"))
    unresolved_reasons = set(_central_enum_values(config, "unresolved_reason_code_enum"))
    market_ids = set(_central_enum_values(config, "market_taxonomy"))
    required_row_fields = {
        "document_order_index",
        "section_id",
        "normalized_section_title",
        "section_manifest_reference",
        "section_position_source",
        "section_start_line_or_position_if_available",
        "section_end_line_or_position_if_available",
        "parent_capability_group_id",
        "parent_capability_group_title",
        "current_route_class",
        "route_confidence_class",
        "exact_route_source",
        "roadmap_pr_labels",
        "blueprint_pr_labels",
        "semantic_task_ids",
        "controller_state_references",
        "downstream_consumer_references",
        "route_owner_artifacts",
        "required_validators",
        "required_reports",
        "market_relevance",
        "authority_boundary",
        "unresolved_reason_code_when_applicable",
        "owner_review_required_flag",
        "no_master_plan_text_mutation_flag",
        "no_old_coverage_ledger_flag",
        "no_runtime_live_order_profit_authority_created_flag",
        "no_source_connector_replay_paper_authority_created_flag",
        "no_quantum_backend_or_simulator_execution_created_flag",
        "no_market_launch_authority_created_flag",
    }
    for index, row in enumerate(rows, start=1):
        label = f"roadmap_crosswalk.rows[{index}]"
        missing_fields = sorted(required_row_fields - set(row))
        if missing_fields:
            failures.append(f"{label} missing required fields: {', '.join(missing_fields)}")
            continue
        if row.get("document_order_index") != index:
            failures.append(f"{label}.document_order_index must be {index}")
        if row.get("current_route_class") not in route_classes:
            failures.append(f"{label} invalid route class {row.get('current_route_class')}")
        if row.get("route_confidence_class") not in confidence_classes:
            failures.append(
                f"{label} invalid route confidence {row.get('route_confidence_class')}"
            )
        if row.get("parent_capability_group_id") not in parent_groups:
            failures.append(
                f"{label} invalid parent capability group {row.get('parent_capability_group_id')}"
            )
        unresolved = row.get("unresolved_reason_code_when_applicable")
        if row.get("current_route_class") == "UNRESOLVED_DEFAULT_ROUTE":
            if unresolved not in unresolved_reasons:
                failures.append(f"{label} unresolved row needs central reason code")
            if row.get("route_confidence_class") not in {
                "UNRESOLVED_EXPLICITLY",
                "EXACT_PR119_ROUTE_ENTRY",
            }:
                failures.append(
                    f"{label} unresolved row needs explicit unresolved or exact PR119 confidence"
                )
        elif unresolved is not None and unresolved not in unresolved_reasons:
            failures.append(f"{label} invalid unresolved reason {unresolved}")
        for flag in (
            "no_master_plan_text_mutation_flag",
            "no_old_coverage_ledger_flag",
            "no_runtime_live_order_profit_authority_created_flag",
            "no_source_connector_replay_paper_authority_created_flag",
            "no_quantum_backend_or_simulator_execution_created_flag",
            "no_market_launch_authority_created_flag",
        ):
            if row.get(flag) is not True:
                failures.append(f"{label}.{flag} must be true")
        boundary = row.get("authority_boundary")
        if not isinstance(boundary, Mapping):
            failures.append(f"{label}.authority_boundary must be an object")
        elif any(value is not False for value in boundary.values()):
            failures.append(f"{label}.authority_boundary must not create authority")
        if not isinstance(row.get("market_relevance"), list) or not row["market_relevance"]:
            failures.append(f"{label}.market_relevance must be a non-empty array")
        else:
            for relevance in row["market_relevance"]:
                if not isinstance(relevance, Mapping):
                    failures.append(f"{label}.market_relevance item must be an object")
                    continue
                if relevance.get("market_id") not in market_ids:
                    failures.append(f"{label} invalid market_id {relevance.get('market_id')}")
                if relevance.get("no_launch_authority_created_flag") is not True:
                    failures.append(f"{label} market relevance must not create launch authority")
        if not row.get("roadmap_pr_labels"):
            failures.append(f"{label} must include exact roadmap/controller crosswalk label")
        if row.get("current_route_class") in {
            "QUANTUM_FORWARD_OPTIMIZATION_ROUTE",
            "QUANTUM_BACKEND_ROUTE",
            "OPTIMIZER_ARBITRATION_ROUTE",
            "LATENCY_COST_ROUTE",
        }:
            if row["authority_boundary"].get("quantum_backend_or_simulator_execution_created") is not False:
                failures.append(f"{label} quantum/latency row must not create execution")
            if row["authority_boundary"].get("profit_evidence_created") is not False:
                failures.append(f"{label} quantum/latency row must not create profit evidence")

    route_entries = registry.get("route_map", {}).get("route_entries", [])
    exact_rows = {row.get("section_id"): row for row in rows}
    if len(route_entries) != 13:
        failures.append("PR119 exact route map must still contain 13 route entries")
    for entry in route_entries:
        if not isinstance(entry, Mapping):
            continue
        section_id = entry.get("section_id")
        row = exact_rows.get(section_id)
        if row is None:
            failures.append(f"PR119 exact route entry missing from crosswalk: {section_id}")
            continue
        if row.get("current_route_class") != entry.get("current_route_class"):
            failures.append(f"PR119 route class changed for {section_id}")
        if row.get("route_confidence_class") != "EXACT_PR119_ROUTE_ENTRY":
            failures.append(f"PR119 route source not marked exact for {section_id}")
        if entry.get("downstream_consumer_reference") not in row.get(
            "downstream_consumer_references", []
        ):
            failures.append(f"PR119 downstream reference not preserved for {section_id}")
        controller_reference = entry.get("controller_state_reference")
        controller_refs = [
            ref.get("controller_entry_reference")
            for ref in row.get("controller_state_references", [])
            if isinstance(ref, Mapping)
        ]
        if controller_reference not in controller_refs:
            failures.append(f"PR119 controller reference not preserved for {section_id}")
    return failures


def validate_command_matrix(
    *,
    report: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    crosswalk_rows = _rows(report)
    command_rows = _command_rows(report)
    crosswalk_ids = [str(row.get("section_id")) for row in crosswalk_rows]
    command_ids = [str(row.get("section_id")) for row in command_rows]
    if len(command_rows) != len(crosswalk_rows):
        failures.append("command matrix row count must equal crosswalk row count")
    if command_ids != crosswalk_ids:
        failures.append("command matrix ordering must match crosswalk document order")
    duplicates = [section_id for section_id, count in Counter(command_ids).items() if count > 1]
    if duplicates:
        failures.append(f"command matrix contains duplicate section IDs: {', '.join(sorted(duplicates))}")
    missing = sorted(set(crosswalk_ids) - set(command_ids))
    if missing:
        failures.append(f"command matrix missing section IDs: {', '.join(missing[:20])}")
    extra = sorted(set(command_ids) - set(crosswalk_ids))
    if extra:
        failures.append(f"command matrix contains section IDs not in crosswalk: {', '.join(extra[:20])}")

    config = registry.get("central_config", {})
    if not isinstance(config, Mapping):
        failures.append("registry central_config must be an object")
        config = {}
    command_families = set(_central_enum_values(config, "command_family_enum"))
    command_scopes = set(_central_enum_values(config, "command_scope_class_enum"))
    command_authorities = set(_central_enum_values(config, "command_authority_class_enum"))
    command_owners = set(_central_enum_values(config, "command_owner_class_enum"))
    command_consumers = set(_central_enum_values(config, "command_consumer_class_enum"))
    command_statuses = set(_central_enum_values(config, "command_status_enum"))
    static_operations = set(_central_enum_values(config, "static_allowed_operation_enum"))
    future_operations = set(_central_enum_values(config, "future_gated_operation_enum"))
    block_reasons = set(_central_enum_values(config, "command_block_reason_enum"))
    future_families = set(
        _central_enum_values(config, "explicit_future_market_candidate_family_enum")
    )
    forbidden_market_values = set(
        _central_enum_values(config, "forbidden_market_taxonomy_value_enum")
    )
    stage1_rules = config.get("stage1_prediction_market_only_rules", {})
    if not isinstance(stage1_rules, Mapping):
        failures.append("stage1_prediction_market_only_rules must be centralized")
        stage1_rules = {}
    expected_stage1_ids = [
        "PREDICTION_MARKETS_GENERAL",
        "KALSHI",
        "POLYMARKET",
        "FORECASTEX_IBKR",
    ]
    if stage1_rules.get("stage1_launch_scope_locked_to_prediction_markets_flag") is not True:
        failures.append("Stage 1 launch scope must remain prediction-market-only")
    if list(stage1_rules.get("stage1_active_market_ids", [])) != expected_stage1_ids:
        failures.append("Stage 1 active market IDs must remain prediction-market-only")
    if stage1_rules.get("stage2_market_selection_created_flag") is not False:
        failures.append("Stage 2 market selection must not be created")
    if stage1_rules.get("future_market_launch_authority_created_flag") is not False:
        failures.append("future market launch authority must not be created")
    if stage1_rules.get("no_open_ended_future_market_taxonomy_flag") is not True:
        failures.append("open-ended future market taxonomy must remain blocked")

    required_fields = {
        "document_order_index",
        "section_id",
        "crosswalk_reference",
        "parent_capability_group_id",
        "current_route_class",
        "command_family",
        "command_scope_class",
        "command_authority_class",
        "command_owner_class",
        "command_consumer_class",
        "command_status",
        "static_allowed_now_operations",
        "future_gated_operations",
        "block_reason_codes",
        "future_pr_labels",
        "roadmap_pr_labels",
        "blueprint_pr_labels",
        "controller_state_references",
        "required_validators",
        "required_reports",
        "required_artifacts",
        "market_scope_summary",
        "stage1_prediction_market_relevance",
        "future_market_relevance",
        "explicit_future_market_candidate_family_when_applicable",
        "owner_review_future_market_scope_classification_when_applicable",
        "quantum_forward_command_metadata",
        "latency_command_metadata",
        "source_connector_runtime_command_metadata",
        "owner_review_required_flag",
        "unresolved_reason_code_when_applicable",
        "no_command_execution_flag",
        "no_runtime_live_order_profit_authority_created_flag",
        "no_source_connector_replay_paper_authority_created_flag",
        "no_quantum_backend_or_simulator_execution_created_flag",
        "no_market_launch_authority_created_flag",
        "no_open_ended_future_market_taxonomy_flag",
        "no_master_plan_text_mutation_flag",
        "no_old_coverage_ledger_flag",
    }
    static_execution_operations = {
        "FUTURE_SOURCE_RETRIEVAL",
        "FUTURE_SOURCE_ACCEPTANCE",
        "FUTURE_CONNECTOR_BINDING",
        "FUTURE_RUNTIME_SNAPSHOT",
        "FUTURE_RUNTIME_CASH_RECEIPT",
        "FUTURE_REPLAY_EXECUTION",
        "FUTURE_PAPER_EXECUTION",
        "FUTURE_LIVE_CANARY",
        "FUTURE_ORDER_INTENT",
        "FUTURE_ORDER_EXECUTION",
        "FUTURE_QUANTUM_BACKEND_RECEIPT",
        "FUTURE_OPTIMIZER_EXECUTION",
        "FUTURE_MARKET_EXPANSION",
        "FUTURE_STAGE2_MARKET_SELECTION",
    }
    for index, row in enumerate(command_rows, start=1):
        label = f"command_matrix.rows[{index}]"
        missing_fields = sorted(required_fields - set(row))
        if missing_fields:
            failures.append(f"{label} missing required fields: {', '.join(missing_fields)}")
            continue
        if row.get("document_order_index") != index:
            failures.append(f"{label}.document_order_index must be {index}")
        reference = row.get("crosswalk_reference")
        if not isinstance(reference, Mapping):
            failures.append(f"{label}.crosswalk_reference must be an object")
        else:
            if reference.get("section_id") != row.get("section_id"):
                failures.append(f"{label}.crosswalk_reference section_id must match row")
            if reference.get("document_order_index") != row.get("document_order_index"):
                failures.append(f"{label}.crosswalk_reference document_order_index must match row")
            if "normalized_section_title" in reference or "section_title" in reference:
                failures.append(f"{label}.crosswalk_reference must stay compact-normalized")
        if row.get("command_family") not in command_families:
            failures.append(f"{label} invalid command_family {row.get('command_family')}")
        if row.get("command_scope_class") not in command_scopes:
            failures.append(f"{label} invalid command_scope_class {row.get('command_scope_class')}")
        if row.get("command_authority_class") not in command_authorities:
            failures.append(f"{label} invalid command_authority_class {row.get('command_authority_class')}")
        if row.get("command_owner_class") not in command_owners:
            failures.append(f"{label} invalid command_owner_class {row.get('command_owner_class')}")
        if row.get("command_consumer_class") not in command_consumers:
            failures.append(f"{label} invalid command_consumer_class {row.get('command_consumer_class')}")
        if row.get("command_status") not in command_statuses:
            failures.append(f"{label} invalid command_status {row.get('command_status')}")
        for operation in row.get("static_allowed_now_operations", []):
            if operation not in static_operations:
                failures.append(f"{label} invalid static operation {operation}")
            if operation in static_execution_operations:
                failures.append(f"{label} static operation must not be execution authority")
        for operation in row.get("future_gated_operations", []):
            if operation not in future_operations:
                failures.append(f"{label} invalid future-gated operation {operation}")
        for reason in row.get("block_reason_codes", []):
            if reason not in block_reasons:
                failures.append(f"{label} invalid block reason {reason}")
        for flag in (
            "no_command_execution_flag",
            "no_runtime_live_order_profit_authority_created_flag",
            "no_source_connector_replay_paper_authority_created_flag",
            "no_quantum_backend_or_simulator_execution_created_flag",
            "no_market_launch_authority_created_flag",
            "no_open_ended_future_market_taxonomy_flag",
            "no_master_plan_text_mutation_flag",
            "no_old_coverage_ledger_flag",
        ):
            if row.get(flag) is not True:
                failures.append(f"{label}.{flag} must be true")
        market_summary = row.get("market_scope_summary")
        if not isinstance(market_summary, Mapping):
            failures.append(f"{label}.market_scope_summary must be an object")
        else:
            forbidden_seen = set(market_summary.get("forbidden_market_taxonomy_values_detected", []))
            if forbidden_seen:
                failures.append(f"{label} emitted forbidden market taxonomy values: {sorted(forbidden_seen)}")
            families = set(market_summary.get("explicit_future_market_candidate_families", []))
            invalid_families = families - future_families
            if invalid_families:
                failures.append(f"{label} invalid explicit future market families: {sorted(invalid_families)}")
            for forbidden in forbidden_market_values:
                if forbidden in set(market_summary.get("market_ids", [])) | families:
                    failures.append(f"{label} emitted forbidden future market value {forbidden}")
        if row.get("future_market_relevance") == "FUTURE_MARKET_PLANNING_DEFERRED":
            if row.get("command_family") not in {
                "FUTURE_MARKET_DEFERRED_COMMAND",
                "MARKET_INDEX_COMMAND",
                "UNRESOLVED_RESEARCH_COMMAND",
                "OWNER_REVIEW_COMMAND",
            }:
                failures.append(f"{label} future-market row must stay deferred or owner-review")
        quantum = row.get("quantum_forward_command_metadata")
        if not isinstance(quantum, Mapping):
            failures.append(f"{label}.quantum_forward_command_metadata must be an object")
        else:
            for flag in (
                "no_backend_execution_flag",
                "no_simulator_execution_flag",
                "no_optimizer_runtime_execution_flag",
                "no_quantum_advantage_claim_flag",
                "no_profit_or_latency_superiority_claim_flag",
            ):
                if quantum.get(flag) is not True:
                    failures.append(f"{label}.quantum_forward_command_metadata.{flag} must be true")
        latency = row.get("latency_command_metadata")
        if isinstance(latency, Mapping):
            for flag in (
                "no_latency_superiority_claim_flag",
                "no_profit_or_latency_superiority_claim_flag",
            ):
                if latency.get(flag) is not True:
                    failures.append(f"{label}.latency_command_metadata.{flag} must be true")
        source_runtime = row.get("source_connector_runtime_command_metadata")
        if isinstance(source_runtime, Mapping):
            for flag in (
                "no_source_retrieval_flag",
                "no_source_fact_acceptance_flag",
                "no_connector_semantic_binding_flag",
                "no_runtime_authority_flag",
                "no_replay_paper_result_flag",
                "no_live_or_order_authority_flag",
            ):
                if source_runtime.get(flag) is not True:
                    failures.append(f"{label}.source_connector_runtime_command_metadata.{flag} must be true")
        if "normalized_section_title" in row:
            failures.append(f"{label} must not duplicate normalized_section_title")

    summary = report.get("command_matrix_summary", {})
    if not isinstance(summary, Mapping):
        failures.append("command_matrix_summary must be an object")
    else:
        expected_counts = {
            "pr120_crosswalk_row_count": len(crosswalk_rows),
            "command_matrix_row_count": len(command_rows),
            "missing_section_count": len(missing),
            "duplicate_section_count": len(duplicates),
            "forbidden_market_taxonomy_value_count": 0,
        }
        for field, expected in expected_counts.items():
            if summary.get(field) != expected:
                failures.append(f"command_matrix_summary.{field} must be {expected!r}")
        for field in (
            "runtime_authority_created",
            "live_authority_created",
            "source_retrieval_created",
            "source_fact_acceptance_created",
            "connector_semantic_binding_created",
            "replay_paper_result_created",
            "order_authority_created",
            "profit_evidence_created",
            "latency_superiority_evidence_created",
            "quantum_backend_simulator_optimizer_execution_created",
            "market_launch_authority_created",
            "stage2_market_selection_created",
        ):
            if summary.get(field) is not False:
                failures.append(f"command_matrix_summary.{field} must be false")
        if summary.get("deterministic_output") is not True:
            failures.append("command_matrix_summary.deterministic_output must be true")
    return failures


def validate_market_index(report: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = _rows(report)
    order = {str(row.get("section_id")): index for index, row in enumerate(rows)}
    valid_ids = set(order)
    market_index = report.get("market_specific_section_index", {})
    markets = market_index.get("markets", []) if isinstance(market_index, Mapping) else []
    if not isinstance(markets, list):
        return ["market_specific_section_index.markets must be an array"]
    sorted_markets = sorted(
        markets,
        key=lambda market: (
            builder.MARKET_STAGE_CLASSES.index(market.get("market_stage_class"))
            if market.get("market_stage_class") in builder.MARKET_STAGE_CLASSES
            else 10**9,
            str(market.get("market_id")),
        ),
    )
    if markets != sorted_markets:
        failures.append("market entries must be sorted deterministically")
    for market in markets:
        if not isinstance(market, Mapping):
            failures.append("market entry must be an object")
            continue
        label = f"market {market.get('market_id')}"
        section_ids = [str(section_id) for section_id in market.get("related_section_ids", [])]
        invalid = sorted(set(section_ids) - valid_ids)
        if invalid:
            failures.append(f"{label} references unknown section IDs: {', '.join(invalid[:20])}")
        if section_ids != sorted(section_ids, key=lambda section_id: order.get(section_id, 10**9)):
            failures.append(f"{label} section IDs must follow document order")
        for flag in (
            "no_market_launch_authority_created_flag",
            "no_external_market_fact_created_flag",
            "no_runtime_live_order_profit_authority_created_flag",
        ):
            if market.get(flag) is not True:
                failures.append(f"{label}.{flag} must be true")
    summary = report.get("market_specific_section_index_summary", {})
    if isinstance(summary, Mapping):
        for field in (
            "market_launch_authority_created",
            "stage2_launch_authority_created",
            "next_market_selected",
        ):
            if summary.get(field) is not False:
                failures.append(f"market index summary {field} must be false")
    return failures


def _receipt_is_validated_file(repo_root: pathlib.Path, receipt: str) -> bool:
    return (
        receipt.endswith(".json")
        or receipt.endswith(".jsonl")
        or "/" in receipt
        or "\\" in receipt
    ) and _path_exists(repo_root, receipt)


def validate_final_mode(
    entries: Sequence[dict[str, Any]],
    *,
    repo_root: pathlib.Path,
) -> list[str]:
    failures: list[str] = []
    for entry in entries:
        capability_id = entry.get("capability_id", "<unknown>")
        status = entry.get("current_status")
        if status in {"NOT_STARTED", "PARTIAL"} and not entry.get("owner_deferred"):
            failures.append(
                f"{capability_id}: final mode does not allow {status} without "
                "owner_deferred=true"
            )
        if status not in FINAL_COMPLETE_STATUSES:
            failures.append(
                f"{capability_id}: final mode incomplete status remains {status}"
            )
        if entry.get("coverage_class") in DEPENDENT_COVERAGE_CLASSES:
            receipts = entry.get("required_receipts", [])
            if not receipts:
                failures.append(
                    f"{capability_id}: final mode requires validated receipts for "
                    f"{entry.get('coverage_class')}"
                )
            for receipt in receipts:
                if not _receipt_is_validated_file(repo_root, receipt):
                    failures.append(
                        f"{capability_id}: final mode receipt is not a validated "
                        f"receipt file: {receipt}"
                    )
    return failures


def validate_report_files(
    *,
    repo_root: pathlib.Path,
    master_plan: pathlib.Path,
    registry_path: pathlib.Path,
    report_path: pathlib.Path,
    schema_path: pathlib.Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    expected_report = builder.build_report(
        repo_root=repo_root,
        master_plan=master_plan,
        registry_path=registry_path,
    )
    second_report = builder.build_report(
        repo_root=repo_root,
        master_plan=master_plan,
        registry_path=registry_path,
    )
    if expected_report != second_report:
        failures.append("generated section coverage report is not deterministic")

    actual_report, json_failures = _load_json(repo_root / report_path)
    failures.extend(json_failures)
    if actual_report is not None and actual_report != expected_report:
        failures.append(
            f"generated report is stale or non-deterministic: {report_path.as_posix()}"
        )
        expected_text = builder.serialize_report(expected_report)
        actual_text = (repo_root / report_path).read_text(encoding="utf-8")
        if actual_text != expected_text:
            failures.append(
                f"generated report serialization differs from deterministic output: "
                f"{report_path.as_posix()}"
            )

    schema, schema_failures = _load_json(repo_root / schema_path)
    failures.extend(schema_failures)
    if actual_report is not None and schema is not None:
        failures.extend(validate_json_schema_subset(actual_report, schema))
    return actual_report, failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    master_plan: pathlib.Path,
    registry_path: pathlib.Path,
    report_path: pathlib.Path,
    schema_path: pathlib.Path,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    try:
        registry = builder.load_registry(root / registry_path)
    except (builder.RegistryParseError, OSError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)

    entries = registry["entries"]
    failures.extend(validate_registry_entries(entries))
    failures.extend(validate_route_map(registry.get("route_map", {}), repo_root=root))
    failures.extend(validate_blocked_future_routing(entries))
    failures.extend(validate_complete_verified_evidence(entries, repo_root=root))
    failures.extend(validate_no_pr_tracking_keys(registry))
    failures.extend(
        validate_no_removed_ledger_references(
            repo_root=root,
            registry_path=registry_path,
            schema_path=schema_path,
            report_path=report_path,
        )
    )

    report, report_failures = validate_report_files(
        repo_root=root,
        master_plan=master_plan,
        registry_path=registry_path,
        report_path=report_path,
        schema_path=schema_path,
    )
    failures.extend(report_failures)
    schema, schema_failures = _load_json(root / schema_path)
    failures.extend(schema_failures)
    if schema is not None:
        failures.extend(validate_schema_enums_match_registry(registry=registry, schema=schema))
    if report is not None:
        failures.extend(validate_no_pr_tracking_keys(report))
        failures.extend(validate_roadmap_crosswalk(report=report, registry=registry))
        failures.extend(validate_command_matrix(report=report, registry=registry))
        failures.extend(validate_market_index(report))

    if mode == "final":
        failures.extend(validate_final_mode(entries, repo_root=root))
    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--master-plan", default=str(builder.DEFAULT_MASTER_PLAN))
    parser.add_argument("--registry", default=str(builder.DEFAULT_REGISTRY))
    parser.add_argument("--report", default=str(builder.DEFAULT_OUTPUT))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        master_plan=pathlib.Path(args.master_plan),
        registry_path=pathlib.Path(args.registry),
        report_path=pathlib.Path(args.report),
        schema_path=pathlib.Path(args.schema),
    )
    if result.ok:
        report = result.report or {}
        summary = report.get("coverage_summary", {})
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"sections={summary.get('parser_visible_section_count', 0)} "
            f"entries={report.get('registry', {}).get('entry_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
