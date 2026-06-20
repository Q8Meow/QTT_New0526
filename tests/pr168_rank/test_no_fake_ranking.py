from tools.pr168_rank_validator import run_validation


def test_no_fake_ranking() -> None:
    run_validation("no_fake_ranking")
