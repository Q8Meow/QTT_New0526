from tools.pr168_rank_validator import run_validation


def test_centralized_systems_coverage() -> None:
    run_validation("centralized_systems_coverage")
