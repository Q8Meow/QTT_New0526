from tools.pr168_rank_validator import run_validation


def test_downstream_orchestration() -> None:
    run_validation("downstream_orchestration")
