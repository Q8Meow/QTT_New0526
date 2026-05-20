from pathlib import Path

from tools import run_validation_gates
from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_preserves_run_validation_gates_fresh_tempdir():
    command_names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]

    assert "runtime_cash_component_field_map_validate.py" in command_names
    assert support.main_report()["run_validation_gates_uses_fresh_pytest_basetemp"] is True
    assert support.main_report()["fixed_tmp_run_validation_gates_pytest_reused"] is False
