from tools.pr168_data1_validator import run_validation


def test_pr168_data1_forward_l2_capture_bootstrap_exists() -> None:
    run_validation("forward_l2_capture_bootstrap_exists")
