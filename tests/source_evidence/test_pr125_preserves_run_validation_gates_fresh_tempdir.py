from __future__ import annotations

from pathlib import Path

from tools import run_validation_gates


def _pytest_basetemp_from_commands(commands: list[list[str]]) -> Path:
    pytest_command = next(
        command
        for command in commands
        if Path(command[1]).name == "run_pytest_fresh_basetemp.py"
    )
    return Path(pytest_command[pytest_command.index("--basetemp") + 1])


def test_pr125_preserves_fresh_unique_pytest_basetemp_command_shape():
    validation_dir = Path(".tmp") / "pr125_validation_temp_contract"
    pytest_basetemp = validation_dir / "run_validation_gates_pytest_PR125_UNIQUE"

    commands = run_validation_gates.build_validation_commands(validation_dir, pytest_basetemp)

    assert _pytest_basetemp_from_commands(commands) == pytest_basetemp
    assert pytest_basetemp.name != "run_validation_gates_pytest"
    assert Path(".tmp") / "run_validation_gates_pytest" != pytest_basetemp
