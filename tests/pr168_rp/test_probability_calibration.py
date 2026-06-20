from tools.pr168_rp_validator import run_validation


def test_probability_calibration() -> None:
    run_validation("probability_calibration")
