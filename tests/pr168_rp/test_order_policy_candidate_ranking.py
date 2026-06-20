from tools.pr168_rp_validator import run_validation


def test_order_policy_candidate_ranking() -> None:
    run_validation("order_policy_candidate_ranking")
