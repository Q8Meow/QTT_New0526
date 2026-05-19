from pathlib import Path

from tools import run_validation_gates
from tests.source_evidence.pr127_execution_lifecycle_support import (
    REPO_ROOT,
    main_report,
)


def test_pr127_preserves_run_validation_gates_fresh_tempdir():
    report = main_report()
    commands = run_validation_gates.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    assert "validate_per_venue_execution_lifecycle_model.py" in command_names
    assert report["run_validation_gates_uses_fresh_pytest_basetemp"] is True
    assert report["fixed_tmp_run_validation_gates_pytest_reused"] is False

    runner_text = (REPO_ROOT / "tools/run_validation_gates.py").read_text(
        encoding="utf-8"
    )
    assert 'prefix="run_validation_gates_pytest_"' in runner_text
    assert '"run_validation_gates_pytest"' in runner_text
