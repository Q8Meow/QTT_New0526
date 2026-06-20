from tools.pr168_rank_validator import run_validation


def test_dag_orchestration() -> None:
    run_validation("dag_orchestration")
