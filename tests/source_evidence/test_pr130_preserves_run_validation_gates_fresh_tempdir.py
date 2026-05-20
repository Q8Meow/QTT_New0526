from tools import run_validation_gates as runner
from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_preserves_run_validation_gates_fresh_tempdir():
    commands = runner.build_validation_commands()
    command_names = [command[1] for command in commands]

    assert any("private_state_read_receipt_gate_validate.py" in name for name in command_names)
    assert support.main_report()["run_validation_gates_uses_fresh_pytest_basetemp"] is True
    assert support.main_report()["fixed_tmp_run_validation_gates_pytest_reused"] is False
