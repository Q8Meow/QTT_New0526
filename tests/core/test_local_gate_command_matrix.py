from __future__ import annotations

from pathlib import Path

import pytest

from tools import local_gate_command_matrix


def _matrix() -> dict:
    return local_gate_command_matrix.build_matrix(repo_root=Path("."))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_local_gate_command_matrix_valid_static_matrix_passes():
    matrix = _matrix()

    assert local_gate_command_matrix.validate_matrix(matrix) == []


def test_local_gate_command_matrix_declares_required_commands_in_locked_order():
    matrix = _matrix()
    commands = [item["command"] for item in matrix["commands"]]

    assert commands == [
        ".\\.venv\\Scripts\\python.exe tools\\run_validation_gates.py",
        ".\\.venv\\Scripts\\python.exe -m compileall -q tools tests",
        "git diff --check",
        "Test-Path docs\\master_plan\\atomic_rows\\AtomicRows.bundle.jsonl",
        "Test-Path docs\\master_plan\\atomic_rows\\AtomicRows.bundle.sha256",
    ]
    assert matrix["command_order_locked"] is True
    assert matrix["failure_blocks_pr_handoff"] is True


def test_local_gate_command_matrix_disallows_manual_skip_and_bare_pytest():
    matrix = _matrix()
    matrix["commands"][0]["manual_skip_allowed"] = True
    matrix["pytest_policy"]["bare_pytest_is_canonical_when_full_validation_required"] = True

    failures = local_gate_command_matrix.validate_matrix(matrix)

    _assert_failure_contains(failures, "manual_skip_allowed")
    _assert_failure_contains(
        failures,
        "bare_pytest_is_canonical_when_full_validation_required",
    )


@pytest.mark.parametrize(
    "flag",
    sorted(local_gate_command_matrix.OUTPUT_AUTHORITY_FLAGS),
)
def test_local_gate_command_matrix_disallows_forbidden_authority_claims(flag):
    matrix = _matrix()
    matrix["local_gate_output_authority"][flag] = True

    failures = local_gate_command_matrix.validate_matrix(matrix)

    _assert_failure_contains(failures, flag)


def test_local_gate_command_matrix_schema_is_closed_at_root():
    import json

    schema = json.loads(
        Path("src/qtt/core/schemas/local_gate_command_matrix.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "commands" in schema["required"]

