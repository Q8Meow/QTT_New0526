from tools.pr168_rp_validator import run_validation


def test_no_forced_negative_to_positive() -> None:
    run_validation("no_forced_negative_to_positive")
