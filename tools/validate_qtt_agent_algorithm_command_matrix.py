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

from tools.build_master_plan_section_coverage_report import (  # noqa: E402
    RegistryParseError,
    load_yaml_subset,
)
from tools.validate_master_plan_section_coverage import (  # noqa: E402
    validate_json_schema_subset,
)

DEFAULT_SCHEMA = (
    pathlib.Path("schemas")
    / "agent_algorithm"
    / "qtt_agent_algorithm_command_matrix.schema.json"
)
DEFAULT_MATRIX = (
    pathlib.Path("docs")
    / "master_plan"
    / "agent_algorithm"
    / "QTTAgentAlgorithmCommandMatrix.yaml"
)
DEFAULT_FIXTURE = (
    pathlib.Path("tests")
    / "fixtures"
    / "agent_algorithm"
    / "synthetic_qtt_agent_algorithm_command_matrix.v1.fixture.json"
)
DEFAULT_REPORT = (
    pathlib.Path("docs")
    / "master_plan"
    / "generated"
    / "QTTAgentAlgorithmCommandMatrix.json"
)

MASTER_PLAN = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"
CANONICAL_BUNDLE = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.jsonl"
)
CANONICAL_BUNDLE_SHA = (
    pathlib.Path("docs") / "master_plan" / "atomic_rows" / "AtomicRows.bundle.sha256"
)

SCHEMA_VERSION = "v1"
MODE = "SOURCE_REQUIRED"
EXECUTION = "DISABLED"
COMMAND_MATRIX_TYPE = "QTT_AGENT_ALGORITHM_COMMAND_MATRIX"
REPORT_TYPE = "QTT_AGENT_ALGORITHM_COMMAND_MATRIX_REPORT"
DETERMINISTIC_GENERATED_AT = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
OWNER_OVERRIDE_BASIS = (
    "OWNER_GLOBAL_OVERRIDE_SATISFIES_QTT_INTERNAL_WORKFLOW_REQUIREMENTS_"
    "WITHOUT_FABRICATING_EXTERNAL_FACTS_OR_EVIDENCE"
)
SUCCESS_MARKER = "QTT_AGENT_ALGORITHM_COMMAND_MATRIX_OK"
FAILURE_MARKER = "QTT_AGENT_ALGORITHM_COMMAND_MATRIX_FAILED"
FINAL_INCOMPLETE_MARKER = "QTT_AGENT_ALGORITHM_COMMAND_MATRIX_FINAL_INCOMPLETE"


@dataclass(frozen=True)
class CommandSpec:
    ordinal: int
    command_id: str
    command_type: str
    tool_path: str | None
    success_marker: str | None
    validation_scope: str
    quantum_forward_compatible: bool
    expected_outputs: tuple[str, ...] = ()


REQUIRED_COMMANDS = (
    CommandSpec(
        ordinal=1,
        command_id="QTT_AGENT_ALGORITHM_COMMAND_001_OWNER_GLOBAL_OVERRIDE_AUTHORITY",
        command_type="VALIDATOR",
        tool_path="tools/validate_qtt_owner_global_override_authority.py",
        success_marker="QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY_VALIDATION_OK",
        validation_scope="owner global override authority",
        quantum_forward_compatible=False,
    ),
    CommandSpec(
        ordinal=2,
        command_id=(
            "QTT_AGENT_ALGORITHM_COMMAND_002_AGENT_ROLE_OPERATING_CHARTER_REGISTRY"
        ),
        command_type="VALIDATOR",
        tool_path="tools/validate_qtt_agent_role_operating_charter_registry.py",
        success_marker="QTT_AGENT_ROLE_OPERATING_CHARTER_REGISTRY_OK",
        validation_scope="QTT agent role operating charter registry",
        quantum_forward_compatible=False,
    ),
    CommandSpec(
        ordinal=3,
        command_id="QTT_AGENT_ALGORITHM_COMMAND_003_ALGORITHM_FORMULA_FAMILY_REGISTRY",
        command_type="VALIDATOR",
        tool_path="tools/validate_qtt_algorithm_formula_family_registry.py",
        success_marker="QTT_ALGORITHM_FORMULA_FAMILY_REGISTRY_OK",
        validation_scope="QTT algorithm/formula family registry",
        quantum_forward_compatible=True,
    ),
    CommandSpec(
        ordinal=4,
        command_id="QTT_AGENT_ALGORITHM_COMMAND_004_AGENT_ALGORITHM_BINDING_REGISTRY",
        command_type="VALIDATOR",
        tool_path="tools/validate_qtt_agent_algorithm_binding_registry.py",
        success_marker="QTT_AGENT_ALGORITHM_BINDING_REGISTRY_OK",
        validation_scope="QTT agent-algorithm binding registry",
        quantum_forward_compatible=True,
    ),
    CommandSpec(
        ordinal=5,
        command_id="QTT_AGENT_ALGORITHM_COMMAND_005_AGENT_ALGORITHM_CONSUMER_GATE",
        command_type="VALIDATOR",
        tool_path="tools/validate_qtt_agent_algorithm_consumer_gate.py",
        success_marker="QTT_AGENT_ALGORITHM_CONSUMER_GATE_OK",
        validation_scope="QTT agent-algorithm consumer gate",
        quantum_forward_compatible=True,
    ),
    CommandSpec(
        ordinal=6,
        command_id=(
            "QTT_AGENT_ALGORITHM_COMMAND_006_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE"
        ),
        command_type="VALIDATOR",
        tool_path="tools/validate_qtt_agent_algorithm_cumulative_readiness_gate.py",
        success_marker="QTT_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE_OK",
        validation_scope="QTT agent-algorithm cumulative readiness gate",
        quantum_forward_compatible=True,
    ),
    CommandSpec(
        ordinal=7,
        command_id=(
            "QTT_AGENT_ALGORITHM_COMMAND_007_RUN_VALIDATION_GATES_CUMULATIVE_HANDOFF"
        ),
        command_type="VALIDATION_HANDOFF",
        tool_path="tools/run_validation_gates.py",
        success_marker="QTT_VALIDATION_GATES_OK",
        validation_scope="cumulative validation handoff",
        quantum_forward_compatible=True,
    ),
    CommandSpec(
        ordinal=8,
        command_id="QTT_AGENT_ALGORITHM_COMMAND_008_POST_MERGE_OWNER_VERIFICATION",
        command_type="OWNER_MANUAL_COMMAND_SEQUENCE",
        tool_path=None,
        success_marker=None,
        validation_scope="post-merge owner verification sequence",
        quantum_forward_compatible=True,
        expected_outputs=(
            "compileall no output",
            "git diff --check no output",
            "git diff -- docs/master_plan/QTT_MasterPlan_Current.md no output",
            "AtomicRows.bundle.jsonl False",
            "AtomicRows.bundle.sha256 False",
            "old coverage-ledger grep no output",
            "git status --short no output",
        ),
    ),
)

COMMAND_FIELDS = (
    "command_id",
    "ordinal",
    "command_type",
    "tool_path",
    "success_marker",
    "validation_scope",
    "owner_override_supported",
    "quantum_forward_compatible",
    "creates_runtime_artifact",
    "creates_live_artifact",
    "creates_order_artifact",
    "creates_profit_evidence",
    "creates_quantum_backend_artifact",
    "creates_source_acceptance_artifact",
    "creates_connector_binding_artifact",
    "creates_runtime_resolver_snapshot",
    "creates_replay_execution",
    "creates_paper_execution",
    "creates_cash_receipt",
    "creates_sha_freeze_authority",
)
COMMAND_SCHEMA_REQUIRED_FIELDS = tuple(
    field for field in COMMAND_FIELDS if field not in {"tool_path", "success_marker"}
)
COMMAND_8_EXTRA_FIELDS = ("expected_outputs",)

ROOT_FALSE_FIELDS = (
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "cash_receipt_artifact_created",
    "sha_freeze_authority_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
)

ROOT_FIELDS = (
    "schema_version",
    "mode",
    "execution",
    "command_matrix_type",
    "source_of_command_matrix_substance",
    "deterministic_output",
    "generated_at_utc",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "owner_override_basis",
    "quantum_forward_design_supported",
    *ROOT_FALSE_FIELDS,
    "authority_boundary_all_false",
    "commands",
)

REPORT_FIELDS = (
    "report_type",
    "deterministic_output",
    "generated_at_utc",
    "source_of_command_matrix_substance",
    "command_matrix_type",
    "owner_global_override_authority",
    "owner_override_satisfies_all_qtt_internal_requirements",
    "command_count",
    "required_command_count",
    "required_commands_present_count",
    "missing_command_count",
    "invalid_command_order_count",
    "commands_with_tool_path_count",
    "commands_with_success_marker_count",
    "owner_global_override_command_present",
    "agent_role_command_present",
    "algorithm_formula_command_present",
    "agent_algorithm_binding_command_present",
    "agent_algorithm_consumer_gate_command_present",
    "agent_algorithm_cumulative_readiness_command_present",
    "validation_gate_handoff_command_present",
    "post_merge_owner_verification_command_present",
    "quantum_forward_design_supported",
    "quantum_evidence_claim_created",
    "alpha_evidence_claim_created",
    "profit_evidence_claim_created",
    "latency_superiority_evidence_claim_created",
    "execution_superiority_evidence_claim_created",
    "runtime_artifact_created",
    "live_artifact_created",
    "order_artifact_created",
    "source_acceptance_artifact_created",
    "connector_binding_artifact_created",
    "runtime_resolver_snapshot_created",
    "replay_execution_created",
    "paper_execution_created",
    "quantum_backend_artifact_created",
    "cash_receipt_artifact_created",
    "sha_freeze_authority_created",
    "bundle_file_present",
    "bundle_sha_present",
    "uses_pr_number_as_authority",
    "final_ready",
    "authority_boundary_all_false",
    "command_ids",
    "commands",
)

COMMAND_FLAG_TO_REPORT_FIELD = {
    "creates_runtime_artifact": "runtime_artifact_created",
    "creates_live_artifact": "live_artifact_created",
    "creates_order_artifact": "order_artifact_created",
    "creates_profit_evidence": "profit_evidence_claim_created",
    "creates_quantum_backend_artifact": "quantum_backend_artifact_created",
    "creates_source_acceptance_artifact": "source_acceptance_artifact_created",
    "creates_connector_binding_artifact": "connector_binding_artifact_created",
    "creates_runtime_resolver_snapshot": "runtime_resolver_snapshot_created",
    "creates_replay_execution": "replay_execution_created",
    "creates_paper_execution": "paper_execution_created",
    "creates_cash_receipt": "cash_receipt_artifact_created",
    "creates_sha_freeze_authority": "sha_freeze_authority_created",
}

COMMAND_ID_TO_REPORT_FIELD = {
    "QTT_AGENT_ALGORITHM_COMMAND_001_OWNER_GLOBAL_OVERRIDE_AUTHORITY": (
        "owner_global_override_command_present"
    ),
    "QTT_AGENT_ALGORITHM_COMMAND_002_AGENT_ROLE_OPERATING_CHARTER_REGISTRY": (
        "agent_role_command_present"
    ),
    "QTT_AGENT_ALGORITHM_COMMAND_003_ALGORITHM_FORMULA_FAMILY_REGISTRY": (
        "algorithm_formula_command_present"
    ),
    "QTT_AGENT_ALGORITHM_COMMAND_004_AGENT_ALGORITHM_BINDING_REGISTRY": (
        "agent_algorithm_binding_command_present"
    ),
    "QTT_AGENT_ALGORITHM_COMMAND_005_AGENT_ALGORITHM_CONSUMER_GATE": (
        "agent_algorithm_consumer_gate_command_present"
    ),
    "QTT_AGENT_ALGORITHM_COMMAND_006_AGENT_ALGORITHM_CUMULATIVE_READINESS_GATE": (
        "agent_algorithm_cumulative_readiness_command_present"
    ),
    "QTT_AGENT_ALGORITHM_COMMAND_007_RUN_VALIDATION_GATES_CUMULATIVE_HANDOFF": (
        "validation_gate_handoff_command_present"
    ),
    "QTT_AGENT_ALGORITHM_COMMAND_008_POST_MERGE_OWNER_VERIFICATION": (
        "post_merge_owner_verification_command_present"
    ),
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


def serialize_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_json(value), encoding="utf-8")


def _normalize_path(value: pathlib.Path | str | None) -> str | None:
    if value is None:
        return None
    return str(value).replace("\\", "/")


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _commands(value: dict[str, Any]) -> list[dict[str, Any]]:
    commands = value.get("commands")
    if not isinstance(commands, list):
        return []
    return [command for command in commands if isinstance(command, dict)]


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


def load_matrix(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError(f"command matrix must contain an object: {path}")
        return value
    return load_yaml_subset(path)


def _load_matrix(path: pathlib.Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"command matrix file is missing: {path}"]
    try:
        return load_matrix(path), []
    except (json.JSONDecodeError, RegistryParseError, ValueError) as exc:
        return None, [f"command matrix file is invalid: {path}: {exc}"]


def _uses_pr_number(value: Any) -> bool:
    if isinstance(value, str):
        return PR_NUMBER_PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(_uses_pr_number(item) for item in value.values())
    if isinstance(value, list):
        return any(_uses_pr_number(item) for item in value)
    return False


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


def _expected_command(spec: CommandSpec) -> dict[str, Any]:
    command: dict[str, Any] = {
        "command_id": spec.command_id,
        "ordinal": spec.ordinal,
        "command_type": spec.command_type,
        "tool_path": spec.tool_path,
        "success_marker": spec.success_marker,
        "validation_scope": spec.validation_scope,
        "owner_override_supported": True,
        "quantum_forward_compatible": spec.quantum_forward_compatible,
        "creates_runtime_artifact": False,
        "creates_live_artifact": False,
        "creates_order_artifact": False,
        "creates_profit_evidence": False,
        "creates_quantum_backend_artifact": False,
        "creates_source_acceptance_artifact": False,
        "creates_connector_binding_artifact": False,
        "creates_runtime_resolver_snapshot": False,
        "creates_replay_execution": False,
        "creates_paper_execution": False,
        "creates_cash_receipt": False,
        "creates_sha_freeze_authority": False,
    }
    if spec.expected_outputs:
        command["expected_outputs"] = list(spec.expected_outputs)
    return command


def build_matrix() -> dict[str, Any]:
    matrix: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mode": MODE,
        "execution": EXECUTION,
        "command_matrix_type": COMMAND_MATRIX_TYPE,
        "source_of_command_matrix_substance": MASTER_PLAN.as_posix(),
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "owner_global_override_authority": True,
        "owner_override_satisfies_all_qtt_internal_requirements": True,
        "owner_override_basis": OWNER_OVERRIDE_BASIS,
        "quantum_forward_design_supported": True,
        "authority_boundary_all_false": True,
        "commands": [_expected_command(spec) for spec in REQUIRED_COMMANDS],
    }
    for field in ROOT_FALSE_FIELDS:
        matrix[field] = False
    return {field: matrix[field] for field in ROOT_FIELDS}


def _empty_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "report_type": REPORT_TYPE,
        "deterministic_output": True,
        "generated_at_utc": DETERMINISTIC_GENERATED_AT,
        "source_of_command_matrix_substance": MASTER_PLAN.as_posix(),
        "command_matrix_type": COMMAND_MATRIX_TYPE,
        "owner_global_override_authority": False,
        "owner_override_satisfies_all_qtt_internal_requirements": False,
        "command_count": 0,
        "required_command_count": len(REQUIRED_COMMANDS),
        "required_commands_present_count": 0,
        "missing_command_count": len(REQUIRED_COMMANDS),
        "invalid_command_order_count": len(REQUIRED_COMMANDS),
        "commands_with_tool_path_count": 0,
        "commands_with_success_marker_count": 0,
        "quantum_forward_design_supported": False,
        "authority_boundary_all_false": False,
        "command_ids": [],
        "commands": [],
    }
    for field in COMMAND_ID_TO_REPORT_FIELD.values():
        report[field] = False
    for field in ROOT_FALSE_FIELDS:
        report[field] = False
    return {field: report[field] for field in REPORT_FIELDS}


def _invalid_command_order_count(commands: Sequence[dict[str, Any]]) -> int:
    required_ids = [spec.command_id for spec in REQUIRED_COMMANDS]
    required_ordinals = [spec.ordinal for spec in REQUIRED_COMMANDS]
    actual_ids = [command.get("command_id") for command in commands]
    actual_ordinals = [command.get("ordinal") for command in commands]
    if actual_ids == required_ids and actual_ordinals == required_ordinals:
        return 0
    mismatches = 0
    for index, expected_id in enumerate(required_ids):
        if index >= len(actual_ids) or actual_ids[index] != expected_id:
            mismatches += 1
    for index, expected_ordinal in enumerate(required_ordinals):
        if index >= len(actual_ordinals) or actual_ordinals[index] != expected_ordinal:
            mismatches += 1
    if len(commands) != len(REQUIRED_COMMANDS):
        mismatches += abs(len(commands) - len(REQUIRED_COMMANDS)) or 1
    return max(mismatches, 1)


def build_report(*, repo_root: pathlib.Path, matrix: dict[str, Any]) -> dict[str, Any]:
    root = repo_root.resolve()
    commands = _commands(matrix)
    command_ids = [str(command.get("command_id") or "") for command in commands]
    required_ids = [spec.command_id for spec in REQUIRED_COMMANDS]
    present_count = sum(1 for command_id in required_ids if command_id in command_ids)
    report = _empty_report()
    report.update(
        {
            "owner_global_override_authority": (
                matrix.get("owner_global_override_authority") is True
            ),
            "owner_override_satisfies_all_qtt_internal_requirements": (
                matrix.get("owner_override_satisfies_all_qtt_internal_requirements")
                is True
            ),
            "command_count": len(commands),
            "required_commands_present_count": present_count,
            "missing_command_count": len(REQUIRED_COMMANDS) - present_count,
            "invalid_command_order_count": _invalid_command_order_count(commands),
            "commands_with_tool_path_count": sum(
                1 for command in commands if isinstance(command.get("tool_path"), str)
            ),
            "commands_with_success_marker_count": sum(
                1
                for command in commands
                if isinstance(command.get("success_marker"), str)
            ),
            "quantum_forward_design_supported": (
                matrix.get("quantum_forward_design_supported") is True
            ),
            "command_ids": command_ids,
            "commands": commands,
        }
    )
    for command_id, report_field in COMMAND_ID_TO_REPORT_FIELD.items():
        report[report_field] = command_id in command_ids

    for root_field in ROOT_FALSE_FIELDS:
        report[root_field] = matrix.get(root_field) is True
    for command in commands:
        for command_flag, report_field in COMMAND_FLAG_TO_REPORT_FIELD.items():
            if command.get(command_flag) is True:
                report[report_field] = True
    report["bundle_file_present"] = (
        report["bundle_file_present"] or (root / CANONICAL_BUNDLE).exists()
    )
    report["bundle_sha_present"] = (
        report["bundle_sha_present"] or (root / CANONICAL_BUNDLE_SHA).exists()
    )
    report["uses_pr_number_as_authority"] = (
        report["uses_pr_number_as_authority"] or _uses_pr_number(matrix)
    )
    command_boundary_clear = all(
        command.get(command_flag) is False
        for command in commands
        for command_flag in COMMAND_FLAG_TO_REPORT_FIELD
    )
    false_fields_clear = all(report[field] is False for field in ROOT_FALSE_FIELDS)
    report["authority_boundary_all_false"] = (
        matrix.get("authority_boundary_all_false") is True
        and false_fields_clear
        and command_boundary_clear
    )
    return {field: report[field] for field in REPORT_FIELDS}


def build_schema() -> dict[str, Any]:
    true_bool = {"const": True}
    false_bool = {"const": False}
    command_properties: dict[str, Any] = {
        "command_id": {"$ref": "#/$defs/command_id"},
        "ordinal": {"enum": [spec.ordinal for spec in REQUIRED_COMMANDS]},
        "command_type": {
            "enum": [
                "VALIDATOR",
                "VALIDATION_HANDOFF",
                "OWNER_MANUAL_COMMAND_SEQUENCE",
            ]
        },
        "tool_path": {"type": ["string", "null"]},
        "success_marker": {"type": ["string", "null"]},
        "validation_scope": {"type": "string"},
        "owner_override_supported": true_bool,
        "quantum_forward_compatible": {"type": "boolean"},
        "expected_outputs": {
            "type": "array",
            "minItems": len(REQUIRED_COMMANDS[-1].expected_outputs),
            "items": {"type": "string"},
        },
    }
    for command_flag in COMMAND_FLAG_TO_REPORT_FIELD:
        command_properties[command_flag] = false_bool

    properties: dict[str, Any] = {
        "schema_version": {"const": SCHEMA_VERSION},
        "mode": {"const": MODE},
        "execution": {"const": EXECUTION},
        "command_matrix_type": {"const": COMMAND_MATRIX_TYPE},
        "source_of_command_matrix_substance": {"const": MASTER_PLAN.as_posix()},
        "deterministic_output": true_bool,
        "generated_at_utc": {"const": DETERMINISTIC_GENERATED_AT},
        "owner_global_override_authority": true_bool,
        "owner_override_satisfies_all_qtt_internal_requirements": true_bool,
        "owner_override_basis": {"const": OWNER_OVERRIDE_BASIS},
        "quantum_forward_design_supported": true_bool,
        "authority_boundary_all_false": true_bool,
        "commands": {
            "type": "array",
            "minItems": len(REQUIRED_COMMANDS),
            "maxItems": len(REQUIRED_COMMANDS),
            "items": {"$ref": "#/$defs/command"},
        },
    }
    for field in ROOT_FALSE_FIELDS:
        properties[field] = false_bool

    report_properties: dict[str, Any] = {
        "report_type": {"const": REPORT_TYPE},
        "deterministic_output": true_bool,
        "generated_at_utc": {"const": DETERMINISTIC_GENERATED_AT},
        "source_of_command_matrix_substance": {"const": MASTER_PLAN.as_posix()},
        "command_matrix_type": {"const": COMMAND_MATRIX_TYPE},
        "owner_global_override_authority": true_bool,
        "owner_override_satisfies_all_qtt_internal_requirements": true_bool,
        "command_count": {"const": len(REQUIRED_COMMANDS)},
        "required_command_count": {"const": len(REQUIRED_COMMANDS)},
        "required_commands_present_count": {"const": len(REQUIRED_COMMANDS)},
        "missing_command_count": {"const": 0},
        "invalid_command_order_count": {"const": 0},
        "commands_with_tool_path_count": {"type": "integer"},
        "commands_with_success_marker_count": {"type": "integer"},
        "quantum_forward_design_supported": true_bool,
        "authority_boundary_all_false": true_bool,
        "command_ids": {
            "type": "array",
            "minItems": len(REQUIRED_COMMANDS),
            "items": {"$ref": "#/$defs/command_id"},
        },
        "commands": {
            "type": "array",
            "minItems": len(REQUIRED_COMMANDS),
            "maxItems": len(REQUIRED_COMMANDS),
            "items": {"$ref": "#/$defs/command"},
        },
    }
    for field in COMMAND_ID_TO_REPORT_FIELD.values():
        report_properties[field] = true_bool
    for field in ROOT_FALSE_FIELDS:
        report_properties[field] = false_bool

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://qtt.local/schemas/agent_algorithm/"
            "qtt_agent_algorithm_command_matrix.schema.json"
        ),
        "title": "QTT Agent Algorithm Command Matrix",
        "description": (
            "Static deterministic command matrix for QTT agent-role and "
            "algorithm validation order. The matrix validates command references "
            "and artifact boundaries without executing command rows."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": list(ROOT_FIELDS),
        "properties": properties,
        "$defs": {
            "command_id": {
                "enum": [spec.command_id for spec in REQUIRED_COMMANDS],
            },
            "command": {
                "type": "object",
                "additionalProperties": False,
                "required": list(COMMAND_SCHEMA_REQUIRED_FIELDS),
                "properties": command_properties,
            },
            "command_matrix_report": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REPORT_FIELDS),
                "properties": report_properties,
            },
        },
    }


def _validate_schema_surface(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if schema.get("additionalProperties") is not False:
        failures.append("schema.additionalProperties must be false")
    if schema.get("required") != list(ROOT_FIELDS):
        failures.append("schema.required must match command matrix root fields")
    commands_schema = _mapping(_mapping(schema.get("properties")).get("commands"))
    if commands_schema.get("minItems") != len(REQUIRED_COMMANDS):
        failures.append("schema.commands.minItems must be 8")
    if commands_schema.get("maxItems") != len(REQUIRED_COMMANDS):
        failures.append("schema.commands.maxItems must be 8")
    defs = _mapping(schema.get("$defs"))
    command_id = _mapping(defs.get("command_id"))
    if command_id.get("enum") != [spec.command_id for spec in REQUIRED_COMMANDS]:
        failures.append("schema.$defs.command_id enum must be canonical")
    command_schema = _mapping(defs.get("command"))
    if command_schema.get("required") != list(COMMAND_SCHEMA_REQUIRED_FIELDS):
        failures.append("schema.$defs.command.required must be canonical")
    report_schema = _mapping(defs.get("command_matrix_report"))
    if report_schema.get("required") != list(REPORT_FIELDS):
        failures.append("schema.$defs.command_matrix_report.required must be canonical")
    return failures


def _validate_command(
    *,
    repo_root: pathlib.Path,
    command: dict[str, Any],
    spec: CommandSpec,
) -> list[str]:
    index = spec.ordinal - 1
    label = f"commands[{index}]"
    if spec.ordinal == 8:
        required_fields = (
            set(COMMAND_FIELDS)
            - {"tool_path", "success_marker"}
            | set(COMMAND_8_EXTRA_FIELDS)
        )
        allowed_fields = required_fields | {"tool_path", "success_marker"}
        missing = sorted(required_fields - set(command))
        unexpected = sorted(set(command) - allowed_fields)
        failures: list[str] = []
        if missing:
            failures.append(f"{label} missing required fields: {', '.join(missing)}")
        if unexpected:
            failures.append(f"{label} has unexpected fields: {', '.join(unexpected)}")
    else:
        expected_fields = set(COMMAND_FIELDS)
        failures = _require_exact_fields(command, expected_fields, label)
    expected = _expected_command(spec)
    for field, expected_value in expected.items():
        if spec.ordinal == 8 and field in {"tool_path", "success_marker"} and field not in command:
            continue
        if command.get(field) != expected_value:
            failures.append(f"{label}.{field} must be {expected_value}")
    if spec.ordinal <= 7:
        if not isinstance(command.get("tool_path"), str) or not command.get("tool_path"):
            failures.append(f"{label}.tool_path is required for commands 1 through 7")
        if not isinstance(command.get("success_marker"), str) or not command.get(
            "success_marker"
        ):
            failures.append(
                f"{label}.success_marker is required for commands 1 through 7"
            )
    if spec.ordinal == 8:
        if command.get("command_type") != "OWNER_MANUAL_COMMAND_SEQUENCE":
            failures.append("commands[7].command_type must be OWNER_MANUAL_COMMAND_SEQUENCE")
        if command.get("tool_path") is not None:
            failures.append("commands[7].tool_path must be null")
        if command.get("success_marker") is not None:
            failures.append("commands[7].success_marker must be null")
        if command.get("expected_outputs") != list(spec.expected_outputs):
            failures.append("commands[7].expected_outputs must be canonical")
    tool_path = command.get("tool_path")
    if isinstance(tool_path, str) and not (repo_root / pathlib.Path(tool_path)).is_file():
        failures.append(f"{label}.tool_path does not exist: {tool_path}")
    if _uses_pr_number(command):
        failures.append(f"{label} must not use a PR number as implementation truth")
    return failures


def _validate_matrix_shape(
    *,
    repo_root: pathlib.Path,
    matrix: dict[str, Any],
    label: str,
    schema: dict[str, Any] | None,
) -> list[str]:
    failures = _require_exact_fields(matrix, set(ROOT_FIELDS), label)
    expected_values = build_matrix()
    expected_without_commands = {
        field: value for field, value in expected_values.items() if field != "commands"
    }
    for field, expected in expected_without_commands.items():
        if matrix.get(field) != expected:
            failures.append(f"{label}.{field} must be {expected}")
    commands = matrix.get("commands")
    if not isinstance(commands, list):
        failures.append(f"{label}.commands must be a list")
    elif len(commands) != len(REQUIRED_COMMANDS):
        failures.append(f"{label}.commands must contain exactly 8 commands")
    else:
        for command, spec in zip(commands, REQUIRED_COMMANDS):
            if not isinstance(command, dict):
                failures.append(f"{label}.commands[{spec.ordinal - 1}] must be an object")
                continue
            failures.extend(
                _validate_command(repo_root=repo_root, command=command, spec=spec)
            )
    if _uses_pr_number(matrix):
        failures.append(f"{label} must not use PR numbers as implementation truth")
    if schema is not None:
        failures.extend(validate_json_schema_subset(matrix, schema))
    return failures


def _validate_report_schema(
    report: dict[str, Any],
    schema: dict[str, Any] | None,
) -> list[str]:
    if schema is None:
        return []
    report_schema = _mapping(_mapping(schema.get("$defs")).get("command_matrix_report"))
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
        "invalid_command_order_count": 0,
        "commands_with_tool_path_count": 7,
        "commands_with_success_marker_count": 7,
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            failures.append(f"report.{field} must be {expected}")
    for field in (
        "deterministic_output",
        "owner_global_override_authority",
        "owner_override_satisfies_all_qtt_internal_requirements",
        "owner_global_override_command_present",
        "agent_role_command_present",
        "algorithm_formula_command_present",
        "agent_algorithm_binding_command_present",
        "agent_algorithm_consumer_gate_command_present",
        "agent_algorithm_cumulative_readiness_command_present",
        "validation_gate_handoff_command_present",
        "post_merge_owner_verification_command_present",
        "quantum_forward_design_supported",
        "authority_boundary_all_false",
    ):
        if report.get(field) is not True:
            failures.append(f"report.{field} must be true")
    for field in ROOT_FALSE_FIELDS:
        if report.get(field) is not False:
            failures.append(f"report.{field} must be false")
    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report.report_type must be {REPORT_TYPE}")
    if report.get("generated_at_utc") != DETERMINISTIC_GENERATED_AT:
        failures.append("report.generated_at_utc must be deterministic sentinel")
    if report.get("command_matrix_type") != COMMAND_MATRIX_TYPE:
        failures.append(f"report.command_matrix_type must be {COMMAND_MATRIX_TYPE}")
    if report.get("source_of_command_matrix_substance") != MASTER_PLAN.as_posix():
        failures.append("report.source_of_command_matrix_substance is invalid")
    if report.get("command_ids") != [spec.command_id for spec in REQUIRED_COMMANDS]:
        failures.append("report.command_ids must be canonical")
    if report != json.loads(serialize_json(report)):
        failures.append("report serialization must be deterministic")
    return failures


def validate(
    *,
    mode: str,
    repo_root: pathlib.Path,
    schema_path: pathlib.Path = DEFAULT_SCHEMA,
    matrix_path: pathlib.Path = DEFAULT_MATRIX,
    fixture_path: pathlib.Path = DEFAULT_FIXTURE,
    output_path: pathlib.Path | None = DEFAULT_REPORT,
) -> ValidationResult:
    root = repo_root.resolve()
    failures: list[str] = []
    schema, schema_failures = _load_json(root / schema_path)
    matrix, matrix_failures = _load_matrix(root / matrix_path)
    fixture, fixture_failures = _load_json(root / fixture_path)
    failures.extend(schema_failures)
    failures.extend(matrix_failures)
    failures.extend(fixture_failures)

    if schema is not None:
        failures.extend(_validate_schema_surface(schema))
    if matrix is not None:
        failures.extend(
            _validate_matrix_shape(
                repo_root=root,
                matrix=matrix,
                label="command_matrix",
                schema=schema,
            )
        )
    if fixture is not None:
        failures.extend(
            _validate_matrix_shape(
                repo_root=root,
                matrix=fixture,
                label="fixture",
                schema=schema,
            )
        )

    report = _empty_report() if matrix is None else build_report(repo_root=root, matrix=matrix)
    second_report = _empty_report() if matrix is None else build_report(
        repo_root=root,
        matrix=matrix,
    )
    if report != second_report:
        failures.append("generated command matrix report is not deterministic")
    failures.extend(_validate_report_schema(report, schema))
    failures.extend(_report_safety_failures(report))

    if mode == "final" and report.get("final_ready") is not True:
        failures.append(
            "final mode incomplete: command matrix is static command sequencing, "
            "not final production readiness"
        )

    if output_path is not None and not failures:
        write_json(root / output_path, report)

    return ValidationResult(mode=mode, failures=tuple(failures), report=report)


def write_static_artifacts(repo_root: pathlib.Path) -> None:
    root = repo_root.resolve()
    matrix = build_matrix()
    schema = build_schema()
    report = build_report(repo_root=root, matrix=matrix)
    write_json(root / DEFAULT_SCHEMA, schema)
    write_json(root / DEFAULT_MATRIX, matrix)
    write_json(root / DEFAULT_FIXTURE, matrix)
    write_json(root / DEFAULT_REPORT, report)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dev", "final"], default="dev")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--out", default=str(DEFAULT_REPORT))
    parser.add_argument("--write-static-artifacts", action="store_true")
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    if args.write_static_artifacts:
        write_static_artifacts(repo_root)

    result = validate(
        mode=args.mode,
        repo_root=repo_root,
        schema_path=pathlib.Path(args.schema),
        matrix_path=pathlib.Path(args.matrix),
        fixture_path=pathlib.Path(args.fixture),
        output_path=pathlib.Path(args.out),
    )
    if result.ok:
        print(SUCCESS_MARKER)
        return 0

    marker = FINAL_INCOMPLETE_MARKER if args.mode == "final" else FAILURE_MARKER
    print(marker)
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
