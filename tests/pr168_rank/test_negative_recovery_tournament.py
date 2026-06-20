from tools.pr168_rank_validator import run_validation


def test_negative_recovery_tournament() -> None:
    run_validation("negative_recovery_tournament")
