#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import pathlib
import re
import sys
from typing import Any, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder  # noqa: E402
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "atomicrows"
    / "atomicrows_lifecycle_gate_command_matrix.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_lifecycle_gate_command_matrix.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsLifecycleGateCommandMatrix.json"
)

GENERATED_REPORT_ROOT = pathlib.Path("docs") / "master_plan" / "generated"
CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REPORT_TYPE = "ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_REPORT"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = "ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_FINAL_INCOMPLETE"
VALIDATION_HOOK = "ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_STATIC_VALIDATION"

ROOT_FIELDS = {
    "fixture_id",
    "fixture_version",
    "fixture_authority_class",
    "schema_authority_class",
    "surface_kind",
    "mode",
    "execution",
    "deterministic_output",
    "generated_report_root",
    "bundle_file_path",
    "bundle_sha_path",
    "commands",
    "authority_boundary",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": "SYNTHETIC_ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_FIXTURE",
    "fixture_version": "ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_FIXTURE_V1",
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_ATOMICROWS_COMMAND_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_ATOMICROWS_COMMAND_AUTHORITY"
    ),
    "surface_kind": "ATOMICROWS_LIFECYCLE_GATE_COMMAND_MATRIX_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "generated_report_root": "docs/master_plan/generated",
    "bundle_file_path": "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    "bundle_sha_path": "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
}

COMMAND_FIELDS = {
    "order",
    "command_name",
    "gate_name",
    "command",
    "shell",
    "tool_path",
    "schema_path",
    "generated_report_path",
    "operation_class",
    "required",
    "local_offline_only",
    "deterministic_output",
    "authority_boundary",
}

AUTHORITY_BOUNDARY_FIELDS = (
    "creates_live_reachability",
    "creates_live_authority",
    "creates_order_authority",
    "creates_runtime_cash_receipt",
    "creates_runtime_authority",
    "retrieves_source_facts",
    "creates_source_acceptance",
    "creates_connector_binding",
    "fetches_private_state",
    "creates_atomicrows_bundle",
    "creates_atomicrows_bundle_sha",
    "creates_sha_freeze_authority",
    "creates_quantum_backend_authority",
    "creates_profit_evidence",
    "creates_profit_claim",
    "reduces_blockers",
)

OPERATION_CLASSES = (
    "DETERMINISTIC_REPORT_GENERATION",
    "LOCAL_OFFLINE_STATIC_VALIDATION",
)


@dataclass(frozen=True)
class CommandSpec:
    order: int
    command_name: str
    gate_name: str
    command: str
    tool_path: pathlib.Path
    schema_path: pathlib.Path | None
    generated_report_path: pathlib.Path | None
    operation_class: str


REQUIRED_COMMANDS = (
    CommandSpec(
        order=1,
        command_name="build_parameter_lifecycle_report",
        gate_name="AtomicRowsParameterLifecycleReport",
        command=(
            r".\.venv\Scripts\python.exe "
            r"tools\build_atomicrows_parameter_lifecycle_report.py"
        ),
        tool_path=pathlib.Path("tools/build_atomicrows_parameter_lifecycle_report.py"),
        schema_path=None,
        generated_report_path=lifecycle_builder.DEFAULT_OUTPUT,
        operation_class="DETERMINISTIC_REPORT_GENERATION",
    ),
    CommandSpec(
        order=2,
        command_name="validate_parameter_lifecycle",
        gate_name="AtomicRowsParameterLifecycleValidation",
        command=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_parameter_lifecycle.py --mode dev"
        ),
        tool_path=pathlib.Path("tools/validate_atomicrows_parameter_lifecycle.py"),
        schema_path=pathlib.Path(
            "schemas/atomicrows/atomicrows_parameter_lifecycle_registry.schema.json"
        ),
        generated_report_path=None,
        operation_class="LOCAL_OFFLINE_STATIC_VALIDATION",
    ),
    CommandSpec(
        order=3,
        command_name="validate_lifecycle_consumer_gate",
        gate_name="AtomicRowsLifecycleConsumerGate",
        command=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_lifecycle_consumer_gate.py --mode dev --out "
            r"docs\master_plan\generated\AtomicRowsLifecycleConsumerGate.report.json"
        ),
        tool_path=pathlib.Path("tools/validate_atomicrows_lifecycle_consumer_gate.py"),
        schema_path=pathlib.Path(
            "schemas/atomicrows/atomicrows_lifecycle_consumer_gate.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/AtomicRowsLifecycleConsumerGate.report.json"
        ),
        operation_class="LOCAL_OFFLINE_STATIC_VALIDATION",
    ),
    CommandSpec(
        order=4,
        command_name="validate_lifecycle_promotion_receipt_gate",
        gate_name="AtomicRowsLifecyclePromotionReceiptGate",
        command=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_lifecycle_promotion_receipt_gate.py "
            r"--mode dev --out "
            r"docs\master_plan\generated"
            r"\AtomicRowsLifecyclePromotionReceiptGate.report.json"
        ),
        tool_path=pathlib.Path(
            "tools/validate_atomicrows_lifecycle_promotion_receipt_gate.py"
        ),
        schema_path=pathlib.Path(
            "schemas/atomicrows/atomicrows_lifecycle_promotion_receipt_gate.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/"
            "AtomicRowsLifecyclePromotionReceiptGate.report.json"
        ),
        operation_class="LOCAL_OFFLINE_STATIC_VALIDATION",
    ),
    CommandSpec(
        order=5,
        command_name="validate_lifecycle_registry_mutation_guard",
        gate_name="AtomicRowsLifecycleRegistryMutationGuard",
        command=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_lifecycle_registry_mutation_guard.py "
            r"--mode dev --out "
            r"docs\master_plan\generated"
            r"\AtomicRowsLifecycleRegistryMutationGuard.report.json"
        ),
        tool_path=pathlib.Path(
            "tools/validate_atomicrows_lifecycle_registry_mutation_guard.py"
        ),
        schema_path=pathlib.Path(
            "schemas/atomicrows/atomicrows_lifecycle_registry_mutation_guard.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/"
            "AtomicRowsLifecycleRegistryMutationGuard.report.json"
        ),
        operation_class="LOCAL_OFFLINE_STATIC_VALIDATION",
    ),
    CommandSpec(
        order=6,
        command_name="validate_lifecycle_cumulative_readiness_gate",
        gate_name="AtomicRowsLifecycleCumulativeReadinessGate",
        command=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_lifecycle_cumulative_readiness_gate.py "
            r"--mode dev --out "
            r"docs\master_plan\generated"
            r"\AtomicRowsLifecycleCumulativeReadinessGate.report.json"
        ),
        tool_path=pathlib.Path(
            "tools/validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
        ),
        schema_path=pathlib.Path(
            "schemas/atomicrows/"
            "atomicrows_lifecycle_cumulative_readiness_gate.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/"
            "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
        ),
        operation_class="LOCAL_OFFLINE_STATIC_VALIDATION",
    ),
)

PR_NUMBER_PATTERN = re.compile(
    r"\bPR\s*#?\s*\d+\b|(?<![A-Za-z])pr\d+\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidationResult:
    mode: str
    failures: tuple[str, ...]
    report: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return not self.failures


def _normalize_path(path: pathlib.Path | str | None) -> str | None:
    if path is None:
        return None
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


def _commands(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    commands = fixture.get("commands")
    if not isinstance(commands, list):
        return []
    return [command for command in commands if isinstance(command, dict)]


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


def _authority_flag(command: dict[str, Any], *fields: str) -> bool:
    boundary = _mapping(command.get("authority_boundary"))
    return any(_truthy(boundary.get(field)) for field in fields)


def _command_targets_path(command: dict[str, Any], path: pathlib.Path) -> bool:
    target = (_normalize_path(path) or "").lower()
    command_text = str(command.get("command") or "").replace("\\", "/").lower()
    generated_report_path = str(
        _normalize_path(command.get("generated_report_path")) or ""
    ).lower()
    return target in command_text or generated_report_path == target


def _path_under_generated(path_text: Any) -> bool:
    if path_text is None:
        return True
    normalized = _normalize_path(str(path_text)) or ""
    generated_root = _normalize_path(GENERATED_REPORT_ROOT) or ""
    return normalized.startswith(f"{generated_root}/") and normalized.endswith(".json")


def _uses_pr_number(value: Any) -> bool:
    if isinstance(value, str):
        return PR_NUMBER_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(_uses_pr_number(item) for item in value.values())
    if isinstance(value, list):
        return any(_uses_pr_number(item) for item in value)
    return False


def _authority_boundary_all_false(fixture: dict[str, Any]) -> bool:
    boundaries = [_mapping(fixture.get("authority_boundary"))]
    boundaries.extend(_mapping(command.get("authority_boundary")) for command in _commands(fixture))
    return all(
        boundary.get(field) is False
        for boundary in boundaries
        for field in AUTHORITY_BOUNDARY_FIELDS
    )


def _empty_report() -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "command_count": 0,
        "required_command_count": len(REQUIRED_COMMANDS),
        "required_commands_present_count": 0,
        "missing_command_count": len(REQUIRED_COMMANDS),
        "command_order_valid": False,
        "tool_paths_present_count": 0,
        "missing_tool_path_count": 0,
        "generated_report_output_count": 0,
        "forbidden_bundle_command_count": 0,
        "forbidden_bundle_sha_command_count": 0,
        "forbidden_runtime_authority_command_count": 0,
        "forbidden_live_authority_command_count": 0,
        "forbidden_source_acceptance_command_count": 0,
        "forbidden_connector_binding_command_count": 0,
        "forbidden_order_authority_command_count": 0,
        "forbidden_profit_claim_command_count": 0,
        "uses_pr_number_as_authority": False,
        "cumulative_ready": False,
        "final_ready": False,
        "authority_boundary_all_false": False,
    }


def build_report(*, repo_root: pathlib.Path, fixture: dict[str, Any]) -> dict[str, Any]:
    root = repo_root.resolve()
    commands = _commands(fixture)
    command_texts = [str(command.get("command") or "") for command in commands]
    required_texts = [spec.command for spec in REQUIRED_COMMANDS]
    required_present_count = sum(
        1 for required_command in required_texts if required_command in command_texts
    )
    tool_paths_present_count = sum(
        1
        for command in commands
        if isinstance(command.get("tool_path"), str)
        and (root / pathlib.Path(command["tool_path"])).exists()
    )
    forbidden_bundle_command_count = sum(
        1
        for command in commands
        if _authority_flag(command, "creates_atomicrows_bundle")
        or _command_targets_path(command, CANONICAL_BUNDLE)
    )
    forbidden_bundle_sha_command_count = sum(
        1
        for command in commands
        if _authority_flag(command, "creates_atomicrows_bundle_sha")
        or _command_targets_path(command, CANONICAL_BUNDLE_SHA)
    )
    forbidden_runtime_authority_command_count = sum(
        1
        for command in commands
        if _authority_flag(
            command,
            "creates_runtime_cash_receipt",
            "creates_runtime_authority",
            "creates_sha_freeze_authority",
        )
    )
    forbidden_live_authority_command_count = sum(
        1
        for command in commands
        if _authority_flag(
            command,
            "creates_live_reachability",
            "creates_live_authority",
            "creates_quantum_backend_authority",
        )
    )
    forbidden_source_acceptance_command_count = sum(
        1
        for command in commands
        if _authority_flag(
            command,
            "retrieves_source_facts",
            "creates_source_acceptance",
        )
    )
    forbidden_connector_binding_command_count = sum(
        1 for command in commands if _authority_flag(command, "creates_connector_binding")
    )
    forbidden_order_authority_command_count = sum(
        1 for command in commands if _authority_flag(command, "creates_order_authority")
    )
    forbidden_profit_claim_command_count = sum(
        1
        for command in commands
        if _authority_flag(command, "creates_profit_evidence", "creates_profit_claim")
    )
    missing_command_count = len(REQUIRED_COMMANDS) - required_present_count
    command_order_valid = command_texts == required_texts
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "command_count": len(commands),
        "required_command_count": len(REQUIRED_COMMANDS),
        "required_commands_present_count": required_present_count,
        "missing_command_count": missing_command_count,
        "command_order_valid": command_order_valid,
        "tool_paths_present_count": tool_paths_present_count,
        "missing_tool_path_count": len(commands) - tool_paths_present_count,
        "generated_report_output_count": sum(
            1 for command in commands if command.get("generated_report_path") is not None
        ),
        "forbidden_bundle_command_count": forbidden_bundle_command_count,
        "forbidden_bundle_sha_command_count": forbidden_bundle_sha_command_count,
        "forbidden_runtime_authority_command_count": (
            forbidden_runtime_authority_command_count
        ),
        "forbidden_live_authority_command_count": forbidden_live_authority_command_count,
        "forbidden_source_acceptance_command_count": (
            forbidden_source_acceptance_command_count
        ),
        "forbidden_connector_binding_command_count": (
            forbidden_connector_binding_command_count
        ),
        "forbidden_order_authority_command_count": (
            forbidden_order_authority_command_count
        ),
        "forbidden_profit_claim_command_count": forbidden_profit_claim_command_count,
        "uses_pr_number_as_authority": _uses_pr_number(fixture),
        "cumulative_ready": False,
        "final_ready": False,
        "authority_boundary_all_false": _authority_boundary_all_false(fixture),
    }


def serialize_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def write_report(report: dict[str, Any], output: pathlib.Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_report(report), encoding="utf-8")


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return ["schema.$defs must be an object"]

    command_names = defs.get("command_name")
    expected_names = [spec.command_name for spec in REQUIRED_COMMANDS]
    if not isinstance(command_names, dict) or command_names.get("enum") != expected_names:
        failures.append("schema.$defs.command_name must contain the exact enum")

    operation_classes = defs.get("operation_class")
    if (
        not isinstance(operation_classes, dict)
        or operation_classes.get("enum") != list(OPERATION_CLASSES)
    ):
        failures.append("schema.$defs.operation_class must contain the exact enum")

    report_schema = defs.get("command_matrix_report")
    if isinstance(report_schema, dict):
        if report_schema.get("required") != list(_empty_report()):
            failures.append("schema.$defs.command_matrix_report.required is not exact")
    else:
        failures.append("schema.$defs.command_matrix_report must be an object")
    return failures


def _validate_authority_boundary(boundary: Any, label: str) -> list[str]:
    if not isinstance(boundary, dict):
        return [f"{label} must be an object"]
    failures = _require_exact_fields(boundary, set(AUTHORITY_BOUNDARY_FIELDS), label)
    for field in AUTHORITY_BOUNDARY_FIELDS:
        if boundary.get(field) is not False:
            failures.append(f"{label}.{field} must remain false")
    return failures


def _validate_command(command: dict[str, Any], spec: CommandSpec) -> list[str]:
    label = f"commands[{spec.order - 1}]"
    failures = _require_exact_fields(command, COMMAND_FIELDS, label)
    expected_values: dict[str, Any] = {
        "order": spec.order,
        "command_name": spec.command_name,
        "gate_name": spec.gate_name,
        "command": spec.command,
        "shell": "powershell",
        "tool_path": _normalize_path(spec.tool_path),
        "schema_path": _normalize_path(spec.schema_path),
        "generated_report_path": _normalize_path(spec.generated_report_path),
        "operation_class": spec.operation_class,
        "required": True,
        "local_offline_only": True,
        "deterministic_output": True,
    }
    for field, expected in expected_values.items():
        if command.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected}")

    failures.extend(
        _validate_authority_boundary(command.get("authority_boundary"), f"{label}.authority_boundary")
    )
    if command.get("operation_class") not in OPERATION_CLASSES:
        failures.append(f"{label}.operation_class must be local static or deterministic")
    if not _path_under_generated(command.get("generated_report_path")):
        failures.append(f"{label}.generated_report_path must be under docs/master_plan/generated")
    if _uses_pr_number(command):
        failures.append(f"{label} must not use a PR number as implementation truth")
    return failures


def _validate_fixture_shape(
    *,
    fixture: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(fixture, ROOT_FIELDS, "fixture")
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")

    failures.extend(
        _validate_authority_boundary(
            fixture.get("authority_boundary"),
            "fixture.authority_boundary",
        )
    )

    commands = fixture.get("commands")
    if not isinstance(commands, list):
        failures.append("fixture.commands must be a list")
    elif len(commands) != len(REQUIRED_COMMANDS):
        failures.append("fixture.commands must contain exactly the required commands")
    else:
        for command, spec in zip(commands, REQUIRED_COMMANDS):
            if not isinstance(command, dict):
                failures.append(f"commands[{spec.order - 1}] must be an object")
                continue
            failures.extend(_validate_command(command, spec))

    if fixture.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"fixture.validation_hook_ids must contain only {VALIDATION_HOOK}")
    if _uses_pr_number(fixture):
        failures.append("fixture must not use PR numbers as implementation truth")

    if schema is not None:
        failures.extend(validate_json_schema_subset(fixture, schema))
    return failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    report_schema = _mapping(schema.get("$defs")).get("command_matrix_report")
    if not isinstance(report_schema, dict):
        return ["schema.$defs.command_matrix_report must be an object"]
    return validate_json_schema_subset(report, report_schema, root_schema=schema)


def _report_safety_failures(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_counts = {
        "command_count": len(REQUIRED_COMMANDS),
        "required_command_count": len(REQUIRED_COMMANDS),
        "required_commands_present_count": len(REQUIRED_COMMANDS),
        "missing_command_count": 0,
        "tool_paths_present_count": len(REQUIRED_COMMANDS),
        "missing_tool_path_count": 0,
        "generated_report_output_count": 5,
        "forbidden_bundle_command_count": 0,
        "forbidden_bundle_sha_command_count": 0,
        "forbidden_runtime_authority_command_count": 0,
        "forbidden_live_authority_command_count": 0,
        "forbidden_source_acceptance_command_count": 0,
        "forbidden_connector_binding_command_count": 0,
        "forbidden_order_authority_command_count": 0,
        "forbidden_profit_claim_command_count": 0,
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    if report.get("command_order_valid") is not True:
        failures.append("report.command_order_valid must be true")
    if report.get("uses_pr_number_as_authority") is not False:
        failures.append("report.uses_pr_number_as_authority must be false")
    if report.get("cumulative_ready") is not False:
        failures.append("report.cumulative_ready must remain false for this matrix")
    if report.get("final_ready") is not False:
        failures.append("report.final_ready must remain false for this matrix")
    if report.get("authority_boundary_all_false") is not True:
        failures.append("report.authority_boundary_all_false must be true")
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

    report = _empty_report()
    if fixture is not None:
        report = build_report(repo_root=root, fixture=fixture)
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: AtomicRows lifecycle coverage and bundle authority "
            "are not complete"
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
            f"commands={report.get('command_count', 0)} "
            f"missing={report.get('missing_command_count', 0)} "
            f"order_valid={report.get('command_order_valid', False)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
