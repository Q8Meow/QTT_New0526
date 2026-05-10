#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_parameter_lifecycle_report as builder  # noqa: E402
from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_parameter_lifecycle_registry.schema.json"
)

SUCCESS_MARKER = "ATOMICROWS_PARAMETER_LIFECYCLE_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_LIFECYCLE_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = "ATOMICROWS_PARAMETER_LIFECYCLE_FINAL_INCOMPLETE"

ROOT_FIELDS = {
    "schema_version",
    "registry_name",
    "registry_model",
    "authority_class",
    "source_master_plan",
    "final_expected_row_coverage",
    "lifecycle_statuses",
    "entries",
}
ENTRY_FIELDS = set(builder.ENTRY_FIELDS)


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


def _entry_label(entry: dict[str, Any], index: int) -> str:
    return f"entries[{index}] {builder._entry_identifier(entry)}"


def validate_registry_shape(registry: dict[str, Any]) -> list[str]:
    failures = _require_exact_fields(registry, ROOT_FIELDS, "registry")
    if registry.get("schema_version") != 1:
        failures.append("registry.schema_version must be 1")
    if registry.get("registry_name") != builder.REGISTRY_NAME:
        failures.append(f"registry.registry_name must be {builder.REGISTRY_NAME}")
    if registry.get("registry_model") != builder.REGISTRY_MODEL:
        failures.append(f"registry.registry_model must be {builder.REGISTRY_MODEL}")
    if registry.get("authority_class") != builder.AUTHORITY_CLASS:
        failures.append(f"registry.authority_class must be {builder.AUTHORITY_CLASS}")
    if registry.get("source_master_plan") != "docs/master_plan/QTT_MasterPlan_Current.md":
        failures.append("registry.source_master_plan must point to the current master plan")
    if registry.get("lifecycle_statuses") != list(builder.LIFECYCLE_STATUSES):
        failures.append("registry.lifecycle_statuses must contain the exact lifecycle enum")
    if not isinstance(registry.get("entries"), list) or not registry.get("entries"):
        failures.append("registry.entries must be a non-empty list")
    return failures


def _is_present_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def validate_registry_entries(entries: Sequence[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        label = _entry_label(entry, index)
        failures.extend(_require_exact_fields(entry, ENTRY_FIELDS, label))

        row_id = entry.get("atomic_parameter_row_id")
        pattern_id = entry.get("row_pattern_id")
        row_present = _is_present_string(row_id)
        pattern_present = _is_present_string(pattern_id)
        if row_present == pattern_present:
            failures.append(
                f"{label}: exactly one of atomic_parameter_row_id or row_pattern_id "
                "must be set"
            )
        identity = row_id if row_present else pattern_id
        if isinstance(identity, str):
            if identity in seen_ids:
                failures.append(f"{label}: duplicate row lifecycle identity {identity}")
            seen_ids.add(identity)

        if entry.get("lifecycle_status") not in builder.LIFECYCLE_STATUSES:
            failures.append(f"{label}: lifecycle_status is not allowed")
        if entry.get("classical_or_quantum") not in {"CLASSICAL", "QUANTUM"}:
            failures.append(f"{label}: classical_or_quantum must be CLASSICAL or QUANTUM")

        for field in (
            "parameter_family",
            "owner_section_id",
            "linked_capability_id",
            "unit",
            "scale",
            "default_value_policy",
            "source_authority_class",
            "research_route",
            "promotion_gate",
        ):
            if not _is_present_string(entry.get(field)):
                failures.append(f"{label}.{field} must be a non-empty string")

        if not isinstance(entry.get("range_required"), bool):
            failures.append(f"{label}.range_required must be boolean")
        if not isinstance(entry.get("evidence_required"), list) or not entry.get(
            "evidence_required"
        ):
            failures.append(f"{label}.evidence_required must be a non-empty list")

        status = entry.get("lifecycle_status")
        if status == "QUARANTINED_UNPROVEN" and not entry.get("quarantine_reason"):
            failures.append(f"{label}: quarantine_reason is required")
        if status == "RETIRED_NOT_USEFUL" and not entry.get("retirement_reason"):
            failures.append(f"{label}: retirement_reason is required")

        for group in (
            "optimizer_eligibility",
            "runtime_eligibility",
            "live_eligibility",
            "authority_boundary",
        ):
            if not isinstance(entry.get(group), dict):
                failures.append(f"{label}.{group} must be an object")

        authority = entry.get("authority_boundary")
        if isinstance(authority, dict):
            missing = sorted(set(builder.AUTHORITY_BOUNDARY_FIELDS) - set(authority))
            if missing:
                failures.append(
                    f"{label}.authority_boundary missing fields: {', '.join(missing)}"
                )
            for field in builder.AUTHORITY_BOUNDARY_FIELDS:
                if authority.get(field) is not False:
                    failures.append(
                        f"{label}.authority_boundary.{field} must remain false"
                    )
    failures.extend(builder.invalid_eligibility_claims(entries))
    return failures


def validate_report_file(
    *,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    report_path: pathlib.Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    expected = builder.build_report(repo_root=repo_root, registry_path=registry_path)
    second = builder.build_report(repo_root=repo_root, registry_path=registry_path)
    if expected != second:
        failures.append("generated parameter lifecycle report is not deterministic")

    actual, json_failures = _load_json(repo_root / report_path)
    failures.extend(json_failures)
    if actual is not None and actual != expected:
        failures.append(
            f"generated report is stale or non-deterministic: {report_path.as_posix()}"
        )
        if (repo_root / report_path).read_text(
            encoding="utf-8"
        ) != builder.serialize_report(expected):
            failures.append(
                "generated report serialization differs from deterministic output: "
                f"{report_path.as_posix()}"
            )
    return actual, failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    registry_path: pathlib.Path,
    schema_path: pathlib.Path,
    report_path: pathlib.Path,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    try:
        registry = builder.load_registry(root / registry_path)
    except (OSError, RegistryParseError) as exc:
        return ValidationResult(mode=mode, failures=(str(exc),), report=None)

    schema, schema_failures = _load_json(root / schema_path)
    failures.extend(schema_failures)
    if schema is not None:
        failures.extend(validate_json_schema_subset(registry, schema))

    failures.extend(validate_registry_shape(registry))
    entries = registry.get("entries", [])
    if isinstance(entries, list):
        failures.extend(validate_registry_entries(entries))
    else:
        failures.append("registry.entries must be a list")

    report, report_failures = validate_report_file(
        repo_root=root,
        registry_path=registry_path,
        report_path=report_path,
    )
    failures.extend(report_failures)
    if report is not None:
        if report.get("deterministic_output") is not True:
            failures.append("report.deterministic_output must be true")
        if report.get("generated_at_utc") != builder.DETERMINISTIC_GENERATED_AT:
            failures.append("report.generated_at_utc must be deterministic sentinel")
        if report.get("authority_boundary_all_false") is not True:
            failures.append("report.authority_boundary_all_false must be true")
        for field in (
            "optimizer_eligible_count",
            "runtime_eligible_count",
            "live_eligible_count",
        ):
            if report.get(field) != 0:
                failures.append(f"report.{field} must be 0 for this PR")

    if mode == "final" and (report is None or report.get("final_ready") is not True):
        failures.append(
            "final mode incomplete: parameter lifecycle registry is a pattern "
            "foundation, not complete row/family coverage"
        )
    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["dev", "final"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--registry", default=str(builder.DEFAULT_REGISTRY))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--report", default=str(builder.DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    result = validate(
        mode=args.mode,
        repo_root=pathlib.Path(args.repo_root),
        registry_path=pathlib.Path(args.registry),
        schema_path=pathlib.Path(args.schema),
        report_path=pathlib.Path(args.report),
    )
    if result.ok:
        report = result.report or {}
        print(
            f"{SUCCESS_MARKER} mode={args.mode} "
            f"entries={report.get('registry_entry_count', 0)} "
            f"invalid_eligibility_claims="
            f"{report.get('invalid_eligibility_claim_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
