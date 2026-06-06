from tools import run_validation_gates


def test_run_validation_gates_includes_pr163_validator():
    command_names = [command[1].replace("\\", "/").split("/")[-1] for command in run_validation_gates.build_validation_commands()]
    assert command_names.count("validate_pr163_generic_paper_adapter_capture_framework.py") == 1
