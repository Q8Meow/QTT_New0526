#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder  # noqa: E402
from tools import validate_atomicrows_lifecycle_consumer_gate as consumer_gate  # noqa: E402
from tools import validate_atomicrows_lifecycle_promotion_receipt_gate as promotion_gate  # noqa: E402
from tools import validate_atomicrows_lifecycle_registry_mutation_guard as mutation_guard  # noqa: E402
from src.qtt.core.testing.atomicrows_bundle_state import (  # noqa: E402
    validate_current_atomicrows_bundle_state,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_lifecycle_cumulative_readiness_gate.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_lifecycle_cumulative_readiness_gate_blocked.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
)

CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REPORT_TYPE = "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_REPORT"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_FINAL_INCOMPLETE"
)

UPSTREAM_REPORT_PATHS = (
    lifecycle_builder.DEFAULT_OUTPUT,
    consumer_gate.DEFAULT_REPORT,
    promotion_gate.DEFAULT_REPORT,
    mutation_guard.DEFAULT_REPORT,
)

ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "deterministic_output",
    "upstream_report_paths",
    "bundle_file_path",
    "bundle_sha_path",
    "authority_boundary",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_BLOCKED_FIXTURE"
    ),
    "fixture_version": (
        "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_BLOCKED_FIXTURE_V1"
    ),
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_READINESS_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_READINESS_AUTHORITY"
    ),
    "surface_kind": "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "bundle_file_path": str(CANONICAL_BUNDLE).replace("\\", "/"),
    "bundle_sha_path": str(CANONICAL_BUNDLE_SHA).replace("\\", "/"),
}

PROHIBITED_TRUTHY_REPORT_FIELDS = {
    "atomicrows_bundle_created",
    "bundle_created",
    "bundle_creation_claimed",
    "bundle_file_created",
    "bundle_file_present",
    "bundle_sha_created",
    "bundle_sha_present",
    "connector_binding_claimed",
    "connector_binding_created",
    "creates_atomicrows_bundle",
    "creates_connector_binding",
    "creates_freeze_authority",
    "creates_live_reachability",
    "creates_order_authority",
    "creates_profit_evidence",
    "creates_runtime_cash_receipt",
    "creates_sha_authority",
    "creates_source_acceptance",
    "live_authority_claimed",
    "live_authority_created",
    "order_authority_claimed",
    "order_authority_created",
    "profit_evidence_claimed",
    "profit_evidence_created",
    "runtime_authority_claimed",
    "runtime_authority_created",
    "runtime_cash_receipt_claimed",
    "runtime_cash_receipt_created",
    "runtime_live_authority_claimed",
    "sha_authority_claimed",
    "sha_authority_created",
    "source_acceptance_claimed",
    "source_acceptance_created",
}


@dataclass(frozen=True)
class UpstreamReportSpec:
    gate_name: str
    path: pathlib.Path
    report_type: str
    invalid_count_fields: tuple[str, ...]
    optimizer_authority_fields: tuple[str, ...]
    runtime_authority_fields: tuple[str, ...]
    live_authority_fields: tuple[str, ...]
    quantum_backend_authority_fields: tuple[str, ...]


UPSTREAM_REPORT_SPECS = (
    UpstreamReportSpec(
        gate_name="AtomicRowsParameterLifecycleReport",
        path=lifecycle_builder.DEFAULT_OUTPUT,
        report_type=lifecycle_builder.REPORT_TYPE,
        invalid_count_fields=("invalid_eligibility_claim_count",),
        optimizer_authority_fields=("optimizer_eligible_count",),
        runtime_authority_fields=("runtime_eligible_count",),
        live_authority_fields=("live_eligible_count",),
        quantum_backend_authority_fields=(),
    ),
    UpstreamReportSpec(
        gate_name="AtomicRowsLifecycleConsumerGate",
        path=consumer_gate.DEFAULT_REPORT,
        report_type=consumer_gate.REPORT_TYPE,
        invalid_count_fields=("invalid_consumer_access_count",),
        optimizer_authority_fields=("optimizer_access_allowed_count",),
        runtime_authority_fields=("runtime_access_allowed_count",),
        live_authority_fields=("live_access_allowed_count",),
        quantum_backend_authority_fields=("quantum_backend_execution_allowed_count",),
    ),
    UpstreamReportSpec(
        gate_name="AtomicRowsLifecyclePromotionReceiptGate",
        path=promotion_gate.DEFAULT_REPORT,
        report_type=promotion_gate.REPORT_TYPE,
        invalid_count_fields=("invalid_promotion_count",),
        optimizer_authority_fields=("optimizer_promotion_allowed_count",),
        runtime_authority_fields=("runtime_promotion_allowed_count",),
        live_authority_fields=("live_promotion_allowed_count",),
        quantum_backend_authority_fields=("quantum_backend_promotion_allowed_count",),
    ),
    UpstreamReportSpec(
        gate_name="AtomicRowsLifecycleRegistryMutationGuard",
        path=mutation_guard.DEFAULT_REPORT,
        report_type=mutation_guard.REPORT_TYPE,
        invalid_count_fields=("invalid_mutation_count",),
        optimizer_authority_fields=("optimizer_authority_mutation_allowed_count",),
        runtime_authority_fields=("runtime_authority_mutation_allowed_count",),
        live_authority_fields=("live_authority_mutation_allowed_count",),
        quantum_backend_authority_fields=(
            "quantum_backend_authority_mutation_allowed_count",
        ),
    ),
)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _normalize_path(path: pathlib.Path) -> str:
    return str(path).replace("\\", "/")


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


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: set[str],
    label: str,
) -> list[str]:
    failures: list[str] = []
    missing = sorted(expected_fields - set(value))
    unexpected = sorted(set(value) - expected_fields)
    if missing:
        failures.append(f"{label} missing required fields: {', '.join(missing)}")
    if unexpected:
        failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    return failures


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return value != 0
    if isinstance(value, str):
        return bool(value)
    if isinstance(value, list | dict):
        return bool(value)
    return value is not None


def _walk_object_fields(value: Any) -> list[tuple[str, Any]]:
    fields: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            fields.append((key, item))
            fields.extend(_walk_object_fields(item))
    elif isinstance(value, list):
        for item in value:
            fields.extend(_walk_object_fields(item))
    return fields


def _integer_count(report: dict[str, Any], field: str) -> int:
    value = report.get(field)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _sum_fields(report: dict[str, Any], fields: Sequence[str]) -> int:
    return sum(_integer_count(report, field) for field in fields)


def _prohibited_claim_count(report: dict[str, Any]) -> int:
    return sum(
        1
        for field, value in _walk_object_fields(report)
        if field in PROHIBITED_TRUTHY_REPORT_FIELDS and _truthy(value)
    )


def _report_for_spec(
    upstream_reports: Mapping[str, dict[str, Any] | None],
    spec: UpstreamReportSpec,
) -> dict[str, Any] | None:
    return upstream_reports.get(_normalize_path(spec.path))


def _empty_report() -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "upstream_report_count": len(UPSTREAM_REPORT_SPECS),
        "upstream_reports_present_count": 0,
        "upstream_reports_missing_count": len(UPSTREAM_REPORT_SPECS),
        "upstream_reports_deterministic_count": 0,
        "upstream_reports_final_ready_false_count": 0,
        "upstream_reports_authority_boundary_all_false_count": 0,
        "total_invalid_claim_count": 0,
        "optimizer_authority_allowed_total": 0,
        "runtime_authority_allowed_total": 0,
        "live_authority_allowed_total": 0,
        "quantum_backend_authority_allowed_total": 0,
        "bundle_file_present": False,
        "bundle_sha_present": False,
        "cumulative_ready": False,
        "final_ready": False,
        "authority_boundary_all_false": False,
    }


def build_report(
    *,
    repo_root: pathlib.Path,
    upstream_reports: Mapping[str, dict[str, Any] | None],
    bundle_file_path: pathlib.Path = CANONICAL_BUNDLE,
    bundle_sha_path: pathlib.Path = CANONICAL_BUNDLE_SHA,
) -> dict[str, Any]:
    root = repo_root.resolve()
    reports = [_report_for_spec(upstream_reports, spec) for spec in UPSTREAM_REPORT_SPECS]
    present_reports = [report for report in reports if report is not None]
    deterministic_count = sum(
        1
        for report in present_reports
        if report.get("deterministic_output") is True
        and report.get("generated_at_utc") == DETERMINISTIC_GENERATED_AT
    )
    final_ready_false_count = sum(
        1 for report in present_reports if report.get("final_ready") is False
    )
    authority_boundary_all_false_count = sum(
        1
        for report in present_reports
        if report.get("authority_boundary_all_false") is True
    )
    total_invalid_claim_count = sum(
        _sum_fields(report, spec.invalid_count_fields) + _prohibited_claim_count(report)
        for spec in UPSTREAM_REPORT_SPECS
        for report in [_report_for_spec(upstream_reports, spec)]
        if report is not None
    )
    optimizer_authority_allowed_total = sum(
        _sum_fields(report, spec.optimizer_authority_fields)
        for spec in UPSTREAM_REPORT_SPECS
        for report in [_report_for_spec(upstream_reports, spec)]
        if report is not None
    )
    runtime_authority_allowed_total = sum(
        _sum_fields(report, spec.runtime_authority_fields)
        for spec in UPSTREAM_REPORT_SPECS
        for report in [_report_for_spec(upstream_reports, spec)]
        if report is not None
    )
    live_authority_allowed_total = sum(
        _sum_fields(report, spec.live_authority_fields)
        for spec in UPSTREAM_REPORT_SPECS
        for report in [_report_for_spec(upstream_reports, spec)]
        if report is not None
    )
    quantum_backend_authority_allowed_total = sum(
        _sum_fields(report, spec.quantum_backend_authority_fields)
        for spec in UPSTREAM_REPORT_SPECS
        for report in [_report_for_spec(upstream_reports, spec)]
        if report is not None
    )
    bundle_file_present = (root / bundle_file_path).exists()
    bundle_sha_present = (root / bundle_sha_path).exists()
    upstream_report_count = len(UPSTREAM_REPORT_SPECS)
    upstream_reports_present_count = len(present_reports)
    upstream_reports_missing_count = upstream_report_count - upstream_reports_present_count
    cumulative_ready = (
        upstream_reports_missing_count == 0
        and deterministic_count == upstream_report_count
        and final_ready_false_count == 0
        and authority_boundary_all_false_count == upstream_report_count
        and total_invalid_claim_count == 0
        and optimizer_authority_allowed_total == 0
        and runtime_authority_allowed_total == 0
        and live_authority_allowed_total == 0
        and quantum_backend_authority_allowed_total == 0
        and not bundle_sha_present
    )
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "upstream_report_count": upstream_report_count,
        "upstream_reports_present_count": upstream_reports_present_count,
        "upstream_reports_missing_count": upstream_reports_missing_count,
        "upstream_reports_deterministic_count": deterministic_count,
        "upstream_reports_final_ready_false_count": final_ready_false_count,
        "upstream_reports_authority_boundary_all_false_count": (
            authority_boundary_all_false_count
        ),
        "total_invalid_claim_count": total_invalid_claim_count,
        "optimizer_authority_allowed_total": optimizer_authority_allowed_total,
        "runtime_authority_allowed_total": runtime_authority_allowed_total,
        "live_authority_allowed_total": live_authority_allowed_total,
        "quantum_backend_authority_allowed_total": (
            quantum_backend_authority_allowed_total
        ),
        "bundle_file_present": bundle_file_present,
        "bundle_sha_present": bundle_sha_present,
        "cumulative_ready": cumulative_ready,
        "final_ready": cumulative_ready,
        "authority_boundary_all_false": (
            authority_boundary_all_false_count == upstream_report_count
        ),
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _validate_fixture_shape(
    *,
    fixture: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(fixture, ROOT_FIELDS, "fixture")
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")

    expected_paths = [_normalize_path(path) for path in UPSTREAM_REPORT_PATHS]
    if fixture.get("upstream_report_paths") != expected_paths:
        failures.append("fixture.upstream_report_paths must contain the canonical reports")

    boundary = fixture.get("authority_boundary")
    if not isinstance(boundary, dict):
        failures.append("fixture.authority_boundary must be an object")
    else:
        failures.extend(
            _require_exact_fields(
                boundary,
                set(lifecycle_builder.AUTHORITY_BOUNDARY_FIELDS),
                "fixture.authority_boundary",
            )
        )
        for field in lifecycle_builder.AUTHORITY_BOUNDARY_FIELDS:
            if boundary.get(field) is not False:
                failures.append(f"fixture.authority_boundary.{field} must remain false")

    if fixture.get("validation_hook_ids") != [
        "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_STATIC_VALIDATION"
    ]:
        failures.append(
            "fixture.validation_hook_ids must contain only "
            "ATOMICROWS_LIFECYCLE_CUMULATIVE_READINESS_GATE_STATIC_VALIDATION"
        )

    if schema is not None:
        failures.extend(validate_json_schema_subset(fixture, schema))
    return failures


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]

    report_schema = defs.get("cumulative_readiness_report")
    if isinstance(report_schema, dict):
        required = report_schema.get("required")
        if required != list(_empty_report()):
            failures.append(
                "schema.$defs.cumulative_readiness_report.required is not exact"
            )
    else:
        failures.append("schema.$defs.cumulative_readiness_report must be an object")
    return failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    report_schema = _mapping(schema.get("$defs")).get("cumulative_readiness_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.cumulative_readiness_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _expected_upstream_reports(repo_root: pathlib.Path) -> tuple[
    dict[str, dict[str, Any]],
    list[str],
]:
    root = repo_root.resolve()
    failures: list[str] = []
    expected: dict[str, dict[str, Any]] = {}
    expected[_normalize_path(lifecycle_builder.DEFAULT_OUTPUT)] = (
        lifecycle_builder.build_report(
            repo_root=root,
            registry_path=lifecycle_builder.DEFAULT_REGISTRY,
        )
    )

    registry = lifecycle_builder.load_registry(root / lifecycle_builder.DEFAULT_REGISTRY)
    lifecycle_report = expected[_normalize_path(lifecycle_builder.DEFAULT_OUTPUT)]

    consumer_fixture, consumer_failures = _load_json(root / consumer_gate.DEFAULT_FIXTURE)
    failures.extend(consumer_failures)
    if consumer_fixture is not None:
        report, report_failures = consumer_gate.build_report(
            fixture=consumer_fixture,
            registry=registry,
            lifecycle_report=lifecycle_report,
        )
        expected[_normalize_path(consumer_gate.DEFAULT_REPORT)] = report
        failures.extend(report_failures)

    promotion_fixture, promotion_failures = _load_json(root / promotion_gate.DEFAULT_FIXTURE)
    failures.extend(promotion_failures)
    if promotion_fixture is not None:
        report, report_failures = promotion_gate.build_report(
            fixture=promotion_fixture,
            registry=registry,
            lifecycle_report=lifecycle_report,
        )
        expected[_normalize_path(promotion_gate.DEFAULT_REPORT)] = report
        failures.extend(report_failures)

    mutation_fixture, mutation_failures = _load_json(root / mutation_guard.DEFAULT_FIXTURE)
    failures.extend(mutation_failures)
    if mutation_fixture is not None:
        report, report_failures = mutation_guard.build_report(
            fixture=mutation_fixture,
            registry=registry,
            lifecycle_report=lifecycle_report,
        )
        expected[_normalize_path(mutation_guard.DEFAULT_REPORT)] = report
        failures.extend(report_failures)

    return expected, failures


def _load_upstream_reports(
    repo_root: pathlib.Path,
    upstream_report_paths: Sequence[pathlib.Path],
) -> tuple[dict[str, dict[str, Any] | None], list[str]]:
    root = repo_root.resolve()
    reports: dict[str, dict[str, Any] | None] = {}
    failures: list[str] = []
    for path in upstream_report_paths:
        report, report_failures = _load_json(root / path)
        reports[_normalize_path(path)] = report
        failures.extend(report_failures)
    return reports, failures


def _validate_upstream_reports(
    *,
    repo_root: pathlib.Path,
    upstream_reports: Mapping[str, dict[str, Any] | None],
) -> list[str]:
    failures: list[str] = []
    expected_reports, expected_failures = _expected_upstream_reports(repo_root)
    failures.extend(expected_failures)
    for spec in UPSTREAM_REPORT_SPECS:
        label = spec.gate_name
        path_key = _normalize_path(spec.path)
        report = upstream_reports.get(path_key)
        if report is None:
            continue
        if report.get("report_type") != spec.report_type:
            failures.append(f"{label} report_type is invalid")
        if report.get("deterministic_output") is not True:
            failures.append(f"{label} deterministic_output must be true")
        if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
            failures.append(f"{label} generated_at_utc must be deterministic")
        if report.get("authority_boundary_all_false") is not True:
            failures.append(f"{label} authority_boundary_all_false must be true")

        expected = expected_reports.get(path_key)
        if expected is not None:
            if set(report) != set(expected):
                failures.append(f"{label} report fields are not exact")
            if report != expected:
                failures.append(
                    f"{label} generated report is stale or non-deterministic"
                )
            if report != json.loads(serialize_report(report)):
                failures.append(f"{label} report serialization is non-deterministic")

        for field_group in (
            spec.optimizer_authority_fields,
            spec.runtime_authority_fields,
            spec.live_authority_fields,
            spec.quantum_backend_authority_fields,
        ):
            for field in field_group:
                if _integer_count(report, field) != 0:
                    failures.append(f"{label}.{field} must be 0")
    return failures


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("upstream_reports_missing_count") != 0:
        failures.append("all AtomicRows lifecycle upstream reports must be present")
    if report.get("upstream_reports_deterministic_count") != report.get(
        "upstream_reports_present_count"
    ):
        failures.append("all present upstream reports must be deterministic")
    if report.get("upstream_reports_authority_boundary_all_false_count") != report.get(
        "upstream_reports_present_count"
    ):
        failures.append("all present upstream reports must keep authority boundaries false")
    if report.get("total_invalid_claim_count") != 0:
        failures.append("upstream reports must not contain invalid or prohibited claims")
    for field in (
        "optimizer_authority_allowed_total",
        "runtime_authority_allowed_total",
        "live_authority_allowed_total",
        "quantum_backend_authority_allowed_total",
    ):
        if report.get(field) != 0:
            failures.append(f"report.{field} must be 0")
    if report.get("bundle_sha_present") is not False:
        failures.append("report.bundle_sha_present must remain false before SHA/freeze authority")
    if (
        report.get("upstream_reports_final_ready_false_count")
        != report.get("upstream_report_count")
        and report.get("cumulative_ready") is not True
    ):
        failures.append(
            "upstream final_ready claims must remain false until cumulative coverage "
            "is complete"
        )
    if report.get("final_ready") is True and report.get("cumulative_ready") is not True:
        failures.append("report.final_ready cannot be true while cumulative_ready is false")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is nondeterministic")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path,
    fixture_path: pathlib.Path,
    output_path: pathlib.Path | None = None,
    upstream_report_paths: Sequence[pathlib.Path] = UPSTREAM_REPORT_PATHS,
    bundle_file_path: pathlib.Path = CANONICAL_BUNDLE,
    bundle_sha_path: pathlib.Path = CANONICAL_BUNDLE_SHA,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []

    schema, schema_failures = _load_json(root / schema_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(fixture_failures)
    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if fixture is not None:
        failures.extend(_validate_fixture_shape(fixture=fixture, schema=schema))

    upstream_reports, upstream_load_failures = _load_upstream_reports(
        root,
        upstream_report_paths,
    )
    failures.extend(upstream_load_failures)
    failures.extend(
        _validate_upstream_reports(
            repo_root=root,
            upstream_reports=upstream_reports,
        )
    )

    report = build_report(
        repo_root=root,
        upstream_reports=upstream_reports,
        bundle_file_path=bundle_file_path,
        bundle_sha_path=bundle_sha_path,
    )
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))
    failures.extend(
        validate_current_atomicrows_bundle_state(
            root,
            label="AtomicRows lifecycle cumulative readiness gate",
        )
    )

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: AtomicRows lifecycle cumulative coverage is not "
            "complete"
        )

    if output_path is not None and not failures:
        write_report(report, root / output_path)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        schema_path=pathlib.Path(args.schema),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"upstream_present={report.get('upstream_reports_present_count', 0)} "
            f"invalid_claims={report.get('total_invalid_claim_count', 0)} "
            f"cumulative_ready={report.get('cumulative_ready', False)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
