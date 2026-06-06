from pathlib import Path

from tools import run_validation_gates


def test_run_validation_gates_includes_pr163_b_validator():
    command_names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]
    assert command_names.count("validate_pr163_b_paired_replay_paper_concurrent_executor.py") == 1
