#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
ALLOWED_ROUTE_CONFIDENCE_CLASSES = {
    "EXACT_CONTROLLER_REFERENCE",
    "EXACT_ARTIFACT_REFERENCE",
    "EXACT_SCHEMA_REFERENCE",
    "EXACT_VALIDATOR_REFERENCE",
    "EXACT_TOOL_REFERENCE",
    "EXACT_MASTER_PLAN_SECTION_REFERENCE",
    "EXACT_ROADMAP_BLUEPRINT_REFERENCE",
    "OWNER_POLICY_REFERENCE",
    "UNRESOLVED_EXPLICITLY",
}
ALLOWED_UNRESOLVED_REASON_CODES = {
    "NO_EXACT_ARTIFACT_OWNER_FOUND",
    "NO_EXACT_CONTROLLER_REFERENCE_FOUND",
    "AMBIGUOUS_SECTION_SCOPE",
    "TITLE_SIMILARITY_ONLY_NOT_ALLOWED",
    "WOULD_REQUIRE_MASTER_PLAN_MUTATION",
    "WOULD_REQUIRE_RUNTIME_OR_LIVE_AUTHORITY",
    "WOULD_REQUIRE_SOURCE_OR_CONNECTOR_AUTHORITY",
    "WOULD_REQUIRE_REPLAY_OR_PAPER_RESULT",
    "WOULD_REQUIRE_QUANTUM_BACKEND_OR_OPTIMIZER_EXECUTION",
    "WOULD_REINTRODUCE_OLD_COVERAGE_LEDGER",
    "OUT_OF_SCOPE_FOR_PR119",
}
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

    for route_class in ALLOWED_ROUTE_CLASSES:
        if route_class not in route_classes:
            failures.append(f"route_map missing required route class: {route_class}")
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
    if report is not None:
        failures.extend(validate_no_pr_tracking_keys(report))

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
