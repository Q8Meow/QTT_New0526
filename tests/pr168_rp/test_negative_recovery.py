from tools.pr168_rp_validator import run_validation


def test_negative_recovery() -> None:
    run_validation("negative_recovery")
