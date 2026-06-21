from tools.pr168_data1_validator import run_validation


def test_pr168_data1_data_readiness_states_are_valid() -> None:
    run_validation("data_readiness_states_are_valid")
