from tools.pr168_data1_validator import run_validation


def test_pr168_data1_agent_crosswalk_required_and_consumed() -> None:
    run_validation("agent_crosswalk_required_and_consumed")
