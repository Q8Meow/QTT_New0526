from tools.pr168_data1_validator import run_validation


def test_pr168_data1_ci_does_not_require_live_network() -> None:
    run_validation("ci_does_not_require_live_network")
