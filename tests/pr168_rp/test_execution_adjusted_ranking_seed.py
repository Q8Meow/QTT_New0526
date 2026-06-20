from tools.pr168_rp_validator import run_validation


def test_execution_adjusted_ranking_seed() -> None:
    run_validation("order_policy_candidate_ranking")
