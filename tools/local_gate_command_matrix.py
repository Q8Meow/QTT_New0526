#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any, Sequence

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from qtt.core.testing.gate_result import (  # noqa: E402
    STATIC_AUTHORITY_FLAGS,
    require_exact_fields,
    static_metadata,
    true_claim_failures,
    write_json,
)

SUCCESS_MARKER = "LOCAL_GATE_COMMAND_MATRIX_OK"
FAILURE_MARKER = "LOCAL_GATE_COMMAND_MATRIX_FAILED"

MATRIX_TYPE = "LOCAL_GATE_COMMAND_MATRIX"
MATRIX_VERSION = "PR37_LOCAL_GATE_COMMAND_MATRIX_V1"
VALIDATION_HOOK = "LOCAL_GATE_COMMAND_MATRIX_STATIC_AUDIT"

ROOT_FIELDS = {
    "matrix_type",
    "matrix_version",
    "status",
    "metadata",
    "command_order_locked",
    "manual_skip_forbidden",
    "failure_blocks_pr_handoff",
    "local_gate_output_authority",
    "pytest_policy",
    "commands",
    "validation_hook_ids",
}

METADATA_FIELDS = set(STATIC_AUTHORITY_FLAGS) | {
    "generated_by",
    "generated_at_utc",
    "authority_class",
}

OUTPUT_AUTHORITY_FLAGS = {
    "local_gate_output_creates_source_fact_acceptance": False,
    "local_gate_output_creates_connector_semantics": False,
    "local_gate_output_creates_runtime_resolver_snapshot": False,
    "local_gate_output_executes_replay_or_paper": False,
    "local_gate_output_creates_live_reachability": False,
    "local_gate_output_creates_runtime_cash_or_usable_cash": False,
    "local_gate_output_creates_atomicrows_bundle_or_4183_rows": False,
    "local_gate_output_reduces_blockers": False,
    "local_gate_output_creates_profit_evidence": False,
}

PYTEST_POLICY = {
    "bare_pytest_is_canonical_when_full_validation_required": False,
    "canonical_full_validation_command": ".\\.venv\\Scripts\\python.exe tools\\run_validation_gates.py",
    "pytest_only_helper_when_needed": ".\\.venv\\Scripts\\python.exe tools\\run_pytest_fresh_basetemp.py -q",
}

COMMAND_FIELDS = {
    "order",
    "command_id",
    "command",
    "shell",
    "required",
    "manual_skip_allowed",
    "failure_blocks_pr_handoff",
    "creates_source_fact_acceptance",
    "creates_connector_semantics",
    "creates_runtime_resolver_snapshot",
    "executes_replay_or_paper",
    "creates_live_reachability",
    "creates_runtime_cash_or_usable_cash",
    "creates_atomicrows_bundle_or_4183_rows",
    "reduces_blockers",
    "creates_profit_evidence",
}

EXPECTED_COMMANDS = [
    (
        "full_validation_gates",
        ".\\.venv\\Scripts\\python.exe tools\\run_validation_gates.py",
        "powershell",
    ),
    (
        "compileall_tools_tests",
        ".\\.venv\\Scripts\\python.exe -m compileall -q tools tests",
        "powershell",
    ),
    ("git_diff_check", "git diff --check", "powershell"),
    (
        "atomicrows_bundle_absence_check",
        "Test-Path docs\\master_plan\\atomic_rows\\AtomicRows.bundle.jsonl",
        "powershell",
    ),
    (
        "atomicrows_bundle_sha_absence_check",
        "Test-Path docs\\master_plan\\atomic_rows\\AtomicRows.bundle.sha256",
        "powershell",
    ),
]

FORBIDDEN_TRUE_FIELDS = set(STATIC_AUTHORITY_FLAGS) | set(OUTPUT_AUTHORITY_FLAGS) | {
    "manual_skip_allowed",
    "bare_pytest_is_canonical_when_full_validation_required",
}


def _static_flag_failures(value: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    for field, expected in sorted(STATIC_AUTHORITY_FLAGS.items()):
        if value.get(field) is not expected:
            failures.append(f"{label}.{field} must be {expected}")
    return failures


def _command_record(index: int, command_id: str, command: str, shell: str) -> dict[str, Any]:
    record = {
        "order": index,
        "command_id": command_id,
        "command": command,
        "shell": shell,
        "required": True,
        "manual_skip_allowed": False,
        "failure_blocks_pr_handoff": True,
    }
    record.update(STATIC_AUTHORITY_FLAGS)
    return record


def build_matrix(*, repo_root: pathlib.Path) -> dict[str, Any]:
    del repo_root
    return {
        "matrix_type": MATRIX_TYPE,
        "matrix_version": MATRIX_VERSION,
        "status": "PASS",
        "metadata": static_metadata("tools/local_gate_command_matrix.py"),
        "command_order_locked": True,
        "manual_skip_forbidden": True,
        "failure_blocks_pr_handoff": True,
        "local_gate_output_authority": dict(OUTPUT_AUTHORITY_FLAGS),
        "pytest_policy": dict(PYTEST_POLICY),
        "commands": [
            _command_record(index, command_id, command, shell)
            for index, (command_id, command, shell) in enumerate(EXPECTED_COMMANDS, 1)
        ],
        "validation_hook_ids": [VALIDATION_HOOK],
    }


def _validate_command(command: Any, expected: tuple[str, str, str], index: int) -> list[str]:
    label = f"commands[{index - 1}]"
    if not isinstance(command, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(command, COMMAND_FIELDS, label)
    command_id, command_text, shell = expected
    if command.get("order") != index:
        failures.append(f"{label}.order must be {index}")
    if command.get("command_id") != command_id:
        failures.append(f"{label}.command_id must be {command_id}")
    if command.get("command") != command_text:
        failures.append(f"{label}.command must be {command_text}")
    if command.get("shell") != shell:
        failures.append(f"{label}.shell must be {shell}")
    if command.get("required") is not True:
        failures.append(f"{label}.required must be true")
    if command.get("manual_skip_allowed") is not False:
        failures.append(f"{label}.manual_skip_allowed must be false")
    if command.get("failure_blocks_pr_handoff") is not True:
        failures.append(f"{label}.failure_blocks_pr_handoff must be true")
    failures.extend(_static_flag_failures(command, label))
    return failures


def validate_matrix(matrix: dict[str, Any]) -> list[str]:
    failures = require_exact_fields(matrix, ROOT_FIELDS, "local gate command matrix")
    if matrix.get("matrix_type") != MATRIX_TYPE:
        failures.append(f"matrix_type must be {MATRIX_TYPE}")
    if matrix.get("matrix_version") != MATRIX_VERSION:
        failures.append(f"matrix_version must be {MATRIX_VERSION}")
    if matrix.get("status") != "PASS":
        failures.append("status must be PASS")
    for field in [
        "command_order_locked",
        "manual_skip_forbidden",
        "failure_blocks_pr_handoff",
    ]:
        if matrix.get(field) is not True:
            failures.append(f"{field} must be true")

    metadata = matrix.get("metadata")
    if not isinstance(metadata, dict):
        failures.append("metadata must be an object")
    else:
        failures.extend(require_exact_fields(metadata, METADATA_FIELDS, "metadata"))
        failures.extend(_static_flag_failures(metadata, "metadata"))
        if metadata.get("authority_class") != "STATIC_REPORT_ONLY_NOT_TRADING_AUTHORITY":
            failures.append("metadata.authority_class must be static report only")

    authority = matrix.get("local_gate_output_authority")
    if not isinstance(authority, dict):
        failures.append("local_gate_output_authority must be an object")
    else:
        failures.extend(
            require_exact_fields(
                authority,
                OUTPUT_AUTHORITY_FLAGS,
                "local_gate_output_authority",
            )
        )
        for field, expected in sorted(OUTPUT_AUTHORITY_FLAGS.items()):
            if authority.get(field) is not expected:
                failures.append(f"local_gate_output_authority.{field} must be {expected}")

    pytest_policy = matrix.get("pytest_policy")
    if not isinstance(pytest_policy, dict):
        failures.append("pytest_policy must be an object")
    else:
        failures.extend(require_exact_fields(pytest_policy, PYTEST_POLICY, "pytest_policy"))
        for field, expected in sorted(PYTEST_POLICY.items()):
            if pytest_policy.get(field) != expected:
                failures.append(f"pytest_policy.{field} must be {expected}")

    commands = matrix.get("commands")
    if not isinstance(commands, list):
        failures.append("commands must be a list")
    elif len(commands) != len(EXPECTED_COMMANDS):
        failures.append("commands must contain exactly the locked local gate command set")
    else:
        for index, (command, expected) in enumerate(
            zip(commands, EXPECTED_COMMANDS),
            1,
        ):
            failures.extend(_validate_command(command, expected, index))

    failures.extend(
        true_claim_failures(
            matrix,
            forbidden_true_fields=FORBIDDEN_TRUE_FIELDS,
            label="local gate command matrix",
        )
    )
    if matrix.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    matrix = build_matrix(repo_root=repo_root)
    failures = validate_matrix(matrix)
    write_json(repo_root / pathlib.Path(args.out), matrix)

    if failures:
        print(FAILURE_MARKER)
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
