from tools.pr168_rank_validator import run_validation


def test_agent_work_orders() -> None:
    run_validation("agent_work_orders")
