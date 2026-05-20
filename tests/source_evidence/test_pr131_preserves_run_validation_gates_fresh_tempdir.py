from tools import run_validation_gates as runner
from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_preserves_run_validation_gates_fresh_tempdir():
    command_names = [command[1] for command in runner.build_validation_commands()]

    assert any(
        "credential_alias_secret_no_capture_readiness_validate.py" in name
        for name in command_names
    )
    assert support.main_report()["PR131_VALIDATION_EVIDENCE"]["run_validation_gates_uses_fresh_pytest_basetemp"] is True
