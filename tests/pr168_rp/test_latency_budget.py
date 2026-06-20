from tools.pr168_rp_validator import run_validation


def test_latency_budget() -> None:
    run_validation("latency_budget")
