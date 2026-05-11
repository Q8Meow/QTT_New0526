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
    / "atomicrows_parameter_agent_binding_command_matrix.schema.json"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "atomicrows"
    / "synthetic_atomicrows_parameter_agent_binding_command_matrix.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "AtomicRowsParameterAgentBindingCommandMatrix.json"
)

GENERATED_REPORT_ROOT = pathlib.Path("docs") / "master_plan" / "generated"
CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

REPORT_TYPE = "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_REPORT"
DETERMINISTIC_GENERATED_AT = lifecycle_builder.DETERMINISTIC_GENERATED_AT
SUCCESS_MARKER = "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_VALIDATION_OK"
FAILURE_MARKER = "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_VALIDATION_FAILED"
FINAL_INCOMPLETE_MARKER = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_FINAL_INCOMPLETE"
)
VALIDATION_HOOK = (
    "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_STATIC_VALIDATION"
)
OWNER_QUANTUM_PRIORITY_POLICY_FORWARD_REFERENCE = (
    "OWNER_QUANTUM_PRIORITY_POLICY_FORWARD_REFERENCE_STATIC_ONLY"
)


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    command_name: str
    command_order: int
    command_text: str
    tool_path: pathlib.Path
    schema_path: pathlib.Path
    generated_report_path: pathlib.Path
    quantum_backend_surface_covered: bool


REQUIRED_COMMANDS = (
    CommandSpec(
        command_id="QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY",
        command_name="validate_qtt_owner_global_override_authority",
        command_order=1,
        command_text=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_qtt_owner_global_override_authority.py --mode dev "
            r"--repo-root . --out "
            r"docs\master_plan\generated\QTTOwnerGlobalOverrideAuthority.report.json"
        ),
        tool_path=pathlib.Path("tools/validate_qtt_owner_global_override_authority.py"),
        schema_path=pathlib.Path(
            "schemas/governance/qtt_owner_global_override_authority.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json"
        ),
        quantum_backend_surface_covered=False,
    ),
    CommandSpec(
        command_id="ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY",
        command_name="validate_atomicrows_parameter_agent_binding_registry",
        command_order=2,
        command_text=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_parameter_agent_binding_registry.py "
            r"--mode dev --out "
            r"docs\master_plan\generated\AtomicRowsParameterAgentBindingReport.json"
        ),
        tool_path=pathlib.Path(
            "tools/validate_atomicrows_parameter_agent_binding_registry.py"
        ),
        schema_path=pathlib.Path(
            "schemas/atomicrows/atomicrows_parameter_agent_binding_registry.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/AtomicRowsParameterAgentBindingReport.json"
        ),
        quantum_backend_surface_covered=True,
    ),
    CommandSpec(
        command_id="ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE",
        command_name="validate_atomicrows_parameter_agent_binding_consumer_gate",
        command_order=3,
        command_text=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_parameter_agent_binding_consumer_gate.py "
            r"--mode dev --out "
            r"docs\master_plan\generated"
            r"\AtomicRowsParameterAgentBindingConsumerGate.report.json"
        ),
        tool_path=pathlib.Path(
            "tools/validate_atomicrows_parameter_agent_binding_consumer_gate.py"
        ),
        schema_path=pathlib.Path(
            "schemas/atomicrows/"
            "atomicrows_parameter_agent_binding_consumer_gate.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/"
            "AtomicRowsParameterAgentBindingConsumerGate.report.json"
        ),
        quantum_backend_surface_covered=True,
    ),
    CommandSpec(
        command_id="ATOMICROWS_PARAMETER_AGENT_BINDING_CUMULATIVE_READINESS_GATE",
        command_name=(
            "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate"
        ),
        command_order=4,
        command_text=(
            r".\.venv\Scripts\python.exe "
            r"tools\validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py "
            r"--mode dev --out "
            r"docs\master_plan\generated"
            r"\AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
        ),
        tool_path=pathlib.Path(
            "tools/validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
        ),
        schema_path=pathlib.Path(
            "schemas/atomicrows/"
            "atomicrows_parameter_agent_binding_cumulative_readiness_gate.schema.json"
        ),
        generated_report_path=pathlib.Path(
            "docs/master_plan/generated/"
            "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
        ),
        quantum_backend_surface_covered=False,
    ),
)

COMMAND_FIELDS = (
    "command_id",
    "command_name",
    "command_order",
    "command_text",
    "tool_path",
    "tool_path_exists",
    "schema_path",
    "schema_path_exists",
    "generated_report_path",
    "generated_report_path_expected",
    "generated_report_path_under_docs_master_plan_generated",
    "command_is_static_validation",
    "command_is_deterministic",
    "command_uses_wall_clock_time",
    "command_uses_pr_number_as_authority",
    "command_creates_atomicrows_bundle",
    "command_creates_atomicrows_bundle_sha",
    "command_creates_runtime_artifact",
    "command_creates_live_artifact",
    "command_creates_order_artifact",
    "command_creates_quantum_backend_artifact",
    "command_creates_profit_artifact",
    "command_creates_source_acceptance_artifact",
    "command_creates_connector_binding_artifact",
    "command_fetches_private_state",
    "command_materializes_secret",
    "command_clones_external_repo",
    "command_installs_package",
    "owner_override_supported",
    "owner_override_blocked_by_command",
    "quantum_priority_forward_compatible",
    "quantum_backend_surface_covered",
    "final_qtt_internal_status",
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
    "generated_at_utc",
    "generated_report_root",
    "bundle_file_path",
    "bundle_sha_path",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "quantum_priority_forward_compatible",
    "quantum_backend_binding_command_covered",
    "quantum_backend_consumer_gate_command_covered",
    "quantum_backend_artifact_created",
    "owner_quantum_priority_policy_forward_reference",
    "owner_can_force_quantum_priority_in_future_selection_layers",
    "static_command_matrix_ready",
    "qtt_internal_command_matrix_ready",
    "final_ready",
    "final_qtt_internal_status",
    "commands",
    "validation_hook_ids",
}

ROOT_CONST_EXPECTATIONS = {
    "fixture_id": (
        "SYNTHETIC_ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_FIXTURE"
    ),
    "fixture_version": (
        "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_FIXTURE_V1"
    ),
    "fixture_authority_class": (
        "SYNTHETIC_NON_AUTHORITATIVE_FIXTURE_NOT_BINDING_COMMAND_AUTHORITY"
    ),
    "schema_authority_class": (
        "STATIC_SCHEMA_CONTRACT_ONLY_NOT_BINDING_COMMAND_AUTHORITY"
    ),
    "surface_kind": "ATOMICROWS_PARAMETER_AGENT_BINDING_COMMAND_MATRIX_STATIC",
    "mode": "SOURCE_REQUIRED",
    "execution": "DISABLED",
    "deterministic_output": True,
    "generated_at_utc": DETERMINISTIC_GENERATED_AT,
    "generated_report_root": "docs/master_plan/generated",
    "bundle_file_path": "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
    "bundle_sha_path": "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256",
    "owner_global_override_authority": True,
    "owner_override_satisfies_all_qtt_internal_requirements": True,
    "quantum_priority_forward_compatible": True,
    "quantum_backend_binding_command_covered": True,
    "quantum_backend_consumer_gate_command_covered": True,
    "quantum_backend_artifact_created": False,
    "owner_quantum_priority_policy_forward_reference": (
        OWNER_QUANTUM_PRIORITY_POLICY_FORWARD_REFERENCE
    ),
    "owner_can_force_quantum_priority_in_future_selection_layers": True,
    "static_command_matrix_ready": True,
    "qtt_internal_command_matrix_ready": True,
    "final_ready": False,
    "final_qtt_internal_status": "OWNER_OVERRIDE_SATISFIED",
}

FORBIDDEN_COMMAND_FLAG_TO_COUNTER = {
    "command_creates_runtime_artifact": "forbidden_runtime_artifact_command_count",
    "command_creates_live_artifact": "forbidden_live_artifact_command_count",
    "command_creates_order_artifact": "forbidden_order_artifact_command_count",
    "command_creates_quantum_backend_artifact": (
        "forbidden_quantum_backend_artifact_command_count"
    ),
    "command_creates_profit_artifact": "forbidden_profit_artifact_command_count",
    "command_creates_source_acceptance_artifact": (
        "forbidden_source_acceptance_command_count"
    ),
    "command_creates_connector_binding_artifact": (
        "forbidden_connector_binding_command_count"
    ),
    "command_fetches_private_state": "forbidden_private_state_fetch_command_count",
    "command_materializes_secret": "forbidden_secret_materialization_command_count",
    "command_clones_external_repo": "forbidden_external_repo_clone_command_count",
    "command_installs_package": "forbidden_package_install_command_count",
}

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


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def _commands(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    commands = fixture.get("commands")
    if not isinstance(commands, list):
        return []
    return [command for command in commands if isinstance(command, dict)]


def _uses_pr_number(value: Any) -> bool:
    if isinstance(value, str):
        return PR_NUMBER_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(_uses_pr_number(item) for item in value.values())
    if isinstance(value, list):
        return any(_uses_pr_number(item) for item in value)
    return False


def _path_under_generated(path_text: Any) -> bool:
    if not isinstance(path_text, str) or not path_text:
        return False
    normalized = _normalize_path(path_text) or ""
    generated_root = _normalize_path(GENERATED_REPORT_ROOT) or ""
    return normalized.startswith(f"{generated_root}/") and normalized.endswith(".json")


def _command_targets_path(command: dict[str, Any], path: pathlib.Path) -> bool:
    target = (_normalize_path(path) or "").lower()
    command_text = str(command.get("command_text") or "").replace("\\", "/").lower()
    generated_report_path = str(
        _normalize_path(command.get("generated_report_path")) or ""
    ).lower()
    return target in command_text or generated_report_path == target


def _expected_command_entry(
    *,
    repo_root: pathlib.Path,
    spec: CommandSpec,
) -> dict[str, Any]:
    root = repo_root.resolve()
    return {
        "command_id": spec.command_id,
        "command_name": spec.command_name,
        "command_order": spec.command_order,
        "command_text": spec.command_text,
        "tool_path": _normalize_path(spec.tool_path),
        "tool_path_exists": (root / spec.tool_path).exists(),
        "schema_path": _normalize_path(spec.schema_path),
        "schema_path_exists": (root / spec.schema_path).exists(),
        "generated_report_path": _normalize_path(spec.generated_report_path),
        "generated_report_path_expected": True,
        "generated_report_path_under_docs_master_plan_generated": (
            _path_under_generated(_normalize_path(spec.generated_report_path))
        ),
        "command_is_static_validation": True,
        "command_is_deterministic": True,
        "command_uses_wall_clock_time": False,
        "command_uses_pr_number_as_authority": False,
        "command_creates_atomicrows_bundle": False,
        "command_creates_atomicrows_bundle_sha": False,
        "command_creates_runtime_artifact": False,
        "command_creates_live_artifact": False,
        "command_creates_order_artifact": False,
        "command_creates_quantum_backend_artifact": False,
        "command_creates_profit_artifact": False,
        "command_creates_source_acceptance_artifact": False,
        "command_creates_connector_binding_artifact": False,
        "command_fetches_private_state": False,
        "command_materializes_secret": False,
        "command_clones_external_repo": False,
        "command_installs_package": False,
        "owner_override_supported": True,
        "owner_override_blocked_by_command": False,
        "quantum_priority_forward_compatible": True,
        "quantum_backend_surface_covered": spec.quantum_backend_surface_covered,
        "final_qtt_internal_status": "OWNER_OVERRIDE_SATISFIED",
    }


def _normalize_command_for_report(
    *,
    repo_root: pathlib.Path,
    command: dict[str, Any],
) -> dict[str, Any]:
    normalized = {field: command.get(field) for field in COMMAND_FIELDS}
    root = repo_root.resolve()
    tool_path = command.get("tool_path")
    schema_path = command.get("schema_path")
    generated_report_path = command.get("generated_report_path")
    normalized["tool_path_exists"] = (
        isinstance(tool_path, str) and (root / pathlib.Path(tool_path)).exists()
    )
    normalized["schema_path_exists"] = (
        isinstance(schema_path, str) and (root / pathlib.Path(schema_path)).exists()
    )
    normalized["generated_report_path_under_docs_master_plan_generated"] = (
        _path_under_generated(generated_report_path)
    )
    normalized["command_uses_pr_number_as_authority"] = (
        command.get("command_uses_pr_number_as_authority") is True
        or _uses_pr_number(command)
    )
    return normalized


def _empty_report() -> dict[str, Any]:
    return {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "commands": [],
        "command_count": 0,
        "required_command_count": len(REQUIRED_COMMANDS),
        "required_commands_present_count": 0,
        "missing_command_count": len(REQUIRED_COMMANDS),
        "command_order_valid": False,
        "tool_paths_present_count": 0,
        "missing_tool_path_count": 0,
        "schema_paths_present_count": 0,
        "missing_schema_path_count": 0,
        "generated_report_output_count": 0,
        "generated_report_paths_under_generated_count": 0,
        "owner_global_override_authority": False,
        "owner_override_satisfies_all_qtt_internal_requirements": False,
        "owner_override_supported_command_count": 0,
        "owner_override_blocked_command_count": 0,
        "validators_block_owner_override_count": 0,
        "codex_blocks_owner_override_count": 0,
        "qtt_agents_block_owner_override_count": 0,
        "generated_reports_block_owner_override_count": 0,
        "validation_gates_block_owner_override_count": 0,
        "final_qtt_internal_status": "BLOCKED_PENDING_COMMAND_MATRIX",
        "blocks_qtt_when_owner_override_present": False,
        "quantum_priority_forward_compatible": False,
        "quantum_backend_binding_command_covered": False,
        "quantum_backend_consumer_gate_command_covered": False,
        "quantum_backend_artifact_created": False,
        "owner_quantum_priority_policy_forward_reference": (
            OWNER_QUANTUM_PRIORITY_POLICY_FORWARD_REFERENCE
        ),
        "owner_can_force_quantum_priority_in_future_selection_layers": False,
        "forbidden_bundle_command_count": 0,
        "forbidden_bundle_sha_command_count": 0,
        "forbidden_runtime_artifact_command_count": 0,
        "forbidden_live_artifact_command_count": 0,
        "forbidden_order_artifact_command_count": 0,
        "forbidden_quantum_backend_artifact_command_count": 0,
        "forbidden_profit_artifact_command_count": 0,
        "forbidden_source_acceptance_command_count": 0,
        "forbidden_connector_binding_command_count": 0,
        "forbidden_private_state_fetch_command_count": 0,
        "forbidden_secret_materialization_command_count": 0,
        "forbidden_external_repo_clone_command_count": 0,
        "forbidden_package_install_command_count": 0,
        "static_command_matrix_ready": False,
        "qtt_internal_command_matrix_ready": False,
        "final_ready": False,
        "uses_pr_number_as_authority": False,
        "authority_boundary_all_false": False,
    }


REPORT_FIELDS = tuple(_empty_report())


def build_report(*, repo_root: pathlib.Path, fixture: dict[str, Any]) -> dict[str, Any]:
    commands = [
        _normalize_command_for_report(repo_root=repo_root, command=command)
        for command in _commands(fixture)
    ]
    command_texts = [str(command.get("command_text") or "") for command in commands]
    required_texts = [spec.command_text for spec in REQUIRED_COMMANDS]
    required_present_count = sum(
        1 for required_command in required_texts if required_command in command_texts
    )
    command_order_valid = command_texts == required_texts and [
        command.get("command_order") for command in commands
    ] == [spec.command_order for spec in REQUIRED_COMMANDS]

    forbidden_counters = {
        counter: sum(
            1
            for command in commands
            if command.get(flag) is True
        )
        for flag, counter in FORBIDDEN_COMMAND_FLAG_TO_COUNTER.items()
    }
    forbidden_bundle_command_count = sum(
        1
        for command in commands
        if command.get("command_creates_atomicrows_bundle") is True
        or _command_targets_path(command, CANONICAL_BUNDLE)
    )
    forbidden_bundle_sha_command_count = sum(
        1
        for command in commands
        if command.get("command_creates_atomicrows_bundle_sha") is True
        or _command_targets_path(command, CANONICAL_BUNDLE_SHA)
    )
    owner_override_blocked_command_count = sum(
        1
        for command in commands
        if command.get("owner_override_blocked_by_command") is True
    )
    uses_pr_number_as_authority = (
        fixture.get("uses_pr_number_as_authority") is True
        or _uses_pr_number(fixture)
        or any(command.get("command_uses_pr_number_as_authority") is True for command in commands)
    )

    quantum_backend_binding_command_covered = any(
        command.get("command_id") == "ATOMICROWS_PARAMETER_AGENT_BINDING_REGISTRY"
        and command.get("quantum_backend_surface_covered") is True
        for command in commands
    )
    quantum_backend_consumer_gate_command_covered = any(
        command.get("command_id") == "ATOMICROWS_PARAMETER_AGENT_BINDING_CONSUMER_GATE"
        and command.get("quantum_backend_surface_covered") is True
        for command in commands
    )
    quantum_backend_artifact_created = any(
        command.get("command_creates_quantum_backend_artifact") is True
        for command in commands
    )

    report = _empty_report()
    report.update(
        {
            "commands": commands,
            "command_count": len(commands),
            "required_commands_present_count": required_present_count,
            "missing_command_count": len(REQUIRED_COMMANDS) - required_present_count,
            "command_order_valid": command_order_valid,
            "tool_paths_present_count": sum(
                1 for command in commands if command.get("tool_path_exists") is True
            ),
            "missing_tool_path_count": sum(
                1 for command in commands if command.get("tool_path_exists") is not True
            ),
            "schema_paths_present_count": sum(
                1 for command in commands if command.get("schema_path_exists") is True
            ),
            "missing_schema_path_count": sum(
                1 for command in commands if command.get("schema_path_exists") is not True
            ),
            "generated_report_output_count": sum(
                1
                for command in commands
                if isinstance(command.get("generated_report_path"), str)
                and command.get("generated_report_path_expected") is True
            ),
            "generated_report_paths_under_generated_count": sum(
                1
                for command in commands
                if command.get(
                    "generated_report_path_under_docs_master_plan_generated"
                )
                is True
            ),
            "owner_global_override_authority": (
                fixture.get("owner_global_override_authority") is True
            ),
            "owner_override_satisfies_all_qtt_internal_requirements": (
                fixture.get("owner_override_satisfies_all_qtt_internal_requirements")
                is True
            ),
            "owner_override_supported_command_count": sum(
                1
                for command in commands
                if command.get("owner_override_supported") is True
            ),
            "owner_override_blocked_command_count": (
                owner_override_blocked_command_count
            ),
            "quantum_priority_forward_compatible": all(
                command.get("quantum_priority_forward_compatible") is True
                for command in commands
            )
            and fixture.get("quantum_priority_forward_compatible") is True,
            "quantum_backend_binding_command_covered": (
                quantum_backend_binding_command_covered
            ),
            "quantum_backend_consumer_gate_command_covered": (
                quantum_backend_consumer_gate_command_covered
            ),
            "quantum_backend_artifact_created": quantum_backend_artifact_created,
            "owner_quantum_priority_policy_forward_reference": str(
                fixture.get("owner_quantum_priority_policy_forward_reference") or ""
            ),
            "owner_can_force_quantum_priority_in_future_selection_layers": (
                fixture.get("owner_can_force_quantum_priority_in_future_selection_layers")
                is True
            ),
            "forbidden_bundle_command_count": forbidden_bundle_command_count,
            "forbidden_bundle_sha_command_count": forbidden_bundle_sha_command_count,
            "uses_pr_number_as_authority": uses_pr_number_as_authority,
        }
    )
    report.update(forbidden_counters)

    zero_forbidden = all(
        report[counter] == 0
        for counter in (
            "forbidden_bundle_command_count",
            "forbidden_bundle_sha_command_count",
            *FORBIDDEN_COMMAND_FLAG_TO_COUNTER.values(),
        )
    )
    owner_block_counts_clear = all(
        report[field] == 0
        for field in (
            "owner_override_blocked_command_count",
            "validators_block_owner_override_count",
            "codex_blocks_owner_override_count",
            "qtt_agents_block_owner_override_count",
            "generated_reports_block_owner_override_count",
            "validation_gates_block_owner_override_count",
        )
    )
    paths_clear = (
        report["tool_paths_present_count"] == len(REQUIRED_COMMANDS)
        and report["missing_tool_path_count"] == 0
        and report["schema_paths_present_count"] == len(REQUIRED_COMMANDS)
        and report["missing_schema_path_count"] == 0
        and report["generated_report_paths_under_generated_count"]
        == len(REQUIRED_COMMANDS)
    )
    static_ready = (
        report["command_count"] == len(REQUIRED_COMMANDS)
        and report["required_commands_present_count"] == len(REQUIRED_COMMANDS)
        and report["missing_command_count"] == 0
        and report["command_order_valid"] is True
        and paths_clear
        and report["owner_global_override_authority"] is True
        and report["owner_override_satisfies_all_qtt_internal_requirements"] is True
        and report["owner_override_supported_command_count"] == len(REQUIRED_COMMANDS)
        and owner_block_counts_clear
        and report["quantum_priority_forward_compatible"] is True
        and report["quantum_backend_binding_command_covered"] is True
        and report["quantum_backend_consumer_gate_command_covered"] is True
        and report["quantum_backend_artifact_created"] is False
        and zero_forbidden
        and report["uses_pr_number_as_authority"] is False
    )
    qtt_internal_ready = (
        static_ready
        and report["owner_override_satisfies_all_qtt_internal_requirements"] is True
    )
    report.update(
        {
            "final_qtt_internal_status": (
                "OWNER_OVERRIDE_SATISFIED"
                if qtt_internal_ready
                else "BLOCKED_PENDING_COMMAND_MATRIX"
            ),
            "blocks_qtt_when_owner_override_present": False,
            "static_command_matrix_ready": static_ready,
            "qtt_internal_command_matrix_ready": qtt_internal_ready,
            "final_ready": False,
            "authority_boundary_all_false": (
                zero_forbidden
                and owner_block_counts_clear
                and report["uses_pr_number_as_authority"] is False
                and report["quantum_backend_artifact_created"] is False
                and all(
                    command.get(field) is False
                    for command in commands
                    for field in (
                        "command_uses_wall_clock_time",
                        "command_uses_pr_number_as_authority",
                        "command_creates_atomicrows_bundle",
                        "command_creates_atomicrows_bundle_sha",
                        "command_creates_runtime_artifact",
                        "command_creates_live_artifact",
                        "command_creates_order_artifact",
                        "command_creates_quantum_backend_artifact",
                        "command_creates_profit_artifact",
                        "command_creates_source_acceptance_artifact",
                        "command_creates_connector_binding_artifact",
                        "command_fetches_private_state",
                        "command_materializes_secret",
                        "command_clones_external_repo",
                        "command_installs_package",
                        "owner_override_blocked_by_command",
                    )
                )
            ),
        }
    )
    return report


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

    command_ids = defs.get("command_id")
    expected_ids = [spec.command_id for spec in REQUIRED_COMMANDS]
    if not isinstance(command_ids, dict) or command_ids.get("enum") != expected_ids:
        failures.append("schema.$defs.command_id must contain the exact enum")

    command_names = defs.get("command_name")
    expected_names = [spec.command_name for spec in REQUIRED_COMMANDS]
    if not isinstance(command_names, dict) or command_names.get("enum") != expected_names:
        failures.append("schema.$defs.command_name must contain the exact enum")

    report_schema = defs.get("command_matrix_report")
    if isinstance(report_schema, dict):
        if report_schema.get("required") != list(REPORT_FIELDS):
            failures.append("schema.$defs.command_matrix_report.required is not exact")
    else:
        failures.append("schema.$defs.command_matrix_report must be an object")
    return failures


def _validate_command(
    *,
    repo_root: pathlib.Path,
    command: dict[str, Any],
    spec: CommandSpec,
) -> list[str]:
    label = f"commands[{spec.command_order - 1}]"
    failures = _require_exact_fields(command, set(COMMAND_FIELDS), label)
    expected = _expected_command_entry(repo_root=repo_root, spec=spec)
    for field, expected_value in expected.items():
        if command.get(field) != expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    if _uses_pr_number(command):
        failures.append(f"{label} must not use a PR number as implementation truth")
    if not _path_under_generated(command.get("generated_report_path")):
        failures.append(
            f"{label}.generated_report_path must be under docs/master_plan/generated"
        )
    return failures


def _validate_fixture_shape(
    *,
    repo_root: pathlib.Path,
    fixture: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(fixture, ROOT_FIELDS, "fixture")
    for field, expected in sorted(ROOT_CONST_EXPECTATIONS.items()):
        if fixture.get(field) != expected:
            failures.append(f"fixture.{field} must be {expected}")

    commands = fixture.get("commands")
    if not isinstance(commands, list):
        failures.append("fixture.commands must be a list")
    elif len(commands) != len(REQUIRED_COMMANDS):
        failures.append("fixture.commands must contain exactly the required commands")
    else:
        for command, spec in zip(commands, REQUIRED_COMMANDS):
            if not isinstance(command, dict):
                failures.append(f"commands[{spec.command_order - 1}] must be an object")
                continue
            failures.extend(
                _validate_command(repo_root=repo_root, command=command, spec=spec)
            )

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
        "schema_paths_present_count": len(REQUIRED_COMMANDS),
        "missing_schema_path_count": 0,
        "generated_report_output_count": len(REQUIRED_COMMANDS),
        "generated_report_paths_under_generated_count": len(REQUIRED_COMMANDS),
        "owner_override_supported_command_count": len(REQUIRED_COMMANDS),
        "owner_override_blocked_command_count": 0,
        "validators_block_owner_override_count": 0,
        "codex_blocks_owner_override_count": 0,
        "qtt_agents_block_owner_override_count": 0,
        "generated_reports_block_owner_override_count": 0,
        "validation_gates_block_owner_override_count": 0,
        "forbidden_bundle_command_count": 0,
        "forbidden_bundle_sha_command_count": 0,
        "forbidden_runtime_artifact_command_count": 0,
        "forbidden_live_artifact_command_count": 0,
        "forbidden_order_artifact_command_count": 0,
        "forbidden_quantum_backend_artifact_command_count": 0,
        "forbidden_profit_artifact_command_count": 0,
        "forbidden_source_acceptance_command_count": 0,
        "forbidden_connector_binding_command_count": 0,
        "forbidden_private_state_fetch_command_count": 0,
        "forbidden_secret_materialization_command_count": 0,
        "forbidden_external_repo_clone_command_count": 0,
        "forbidden_package_install_command_count": 0,
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")

    expected_true_fields = (
        "command_order_valid",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "quantum_priority_forward_compatible",
        "quantum_backend_binding_command_covered",
        "quantum_backend_consumer_gate_command_covered",
        "owner_can_force_quantum_priority_in_future_selection_layers",
        "static_command_matrix_ready",
        "qtt_internal_command_matrix_ready",
        "authority_boundary_all_false",
    )
    for field in expected_true_fields:
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")

    expected_false_fields = (
        "blocks_qtt_when_owner_override_present",
        "quantum_backend_artifact_created",
        "final_ready",
        "uses_pr_number_as_authority",
    )
    for field in expected_false_fields:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")

    if report.get("final_qtt_internal_status") != "OWNER_OVERRIDE_SATISFIED":
        failures.append("report.final_qtt_internal_status must be OWNER_OVERRIDE_SATISFIED")
    if (
        report.get("owner_quantum_priority_policy_forward_reference")
        != OWNER_QUANTUM_PRIORITY_POLICY_FORWARD_REFERENCE
    ):
        failures.append(
            "report.owner_quantum_priority_policy_forward_reference is invalid"
        )
    if report.get("deterministic_output") is not True:
        failures.append("report.deterministic_output must be true")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must be deterministic sentinel")
    if report != json.loads(serialize_report(report)):
        failures.append("report output is nondeterministic")
    return failures


def _validate_fixture_expected_readiness(
    *,
    fixture: dict[str, Any] | None,
    report: dict[str, Any],
) -> list[str]:
    if fixture is None:
        return []
    failures: list[str] = []
    for field in (
        "static_command_matrix_ready",
        "qtt_internal_command_matrix_ready",
        "final_ready",
        "final_qtt_internal_status",
        "quantum_priority_forward_compatible",
        "quantum_backend_binding_command_covered",
        "quantum_backend_consumer_gate_command_covered",
        "quantum_backend_artifact_created",
    ):
        if fixture.get(field) != report.get(field):
            failures.append(f"fixture.{field} does not match deterministic report")
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
        failures.extend(
            _validate_fixture_shape(repo_root=root, fixture=fixture, schema=schema)
        )

    report = _empty_report()
    if fixture is not None:
        report = build_report(repo_root=root, fixture=fixture)
    second_report = _empty_report() if fixture is None else build_report(
        repo_root=root,
        fixture=fixture,
    )
    if report != second_report:
        failures.append("generated command matrix report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))
    failures.extend(_validate_fixture_expected_readiness(fixture=fixture, report=report))

    if (root / CANONICAL_BUNDLE).exists():
        failures.append("AtomicRows.bundle.jsonl must not exist")
    if (root / CANONICAL_BUNDLE_SHA).exists():
        failures.append("AtomicRows.bundle.sha256 must not exist")

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: AtomicRows parameter-agent binding command "
            "matrix is static and does not create full production bundle readiness"
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
            f"order_valid={report.get('command_order_valid', False)} "
            f"owner_override_blocked="
            f"{report.get('owner_override_blocked_command_count', 0)}"
        )
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(f"{marker} mode={args.mode}")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
