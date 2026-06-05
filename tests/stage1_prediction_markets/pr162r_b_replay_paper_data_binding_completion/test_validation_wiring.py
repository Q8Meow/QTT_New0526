from tools import run_validation_gates


def test_validation_wiring():
    command_names = [command[1].replace("\\", "/").split("/")[-1] for command in run_validation_gates.build_validation_commands()]
    assert command_names.count("validate_pr162r_b_replay_paper_data_binding_completion.py") == 1
