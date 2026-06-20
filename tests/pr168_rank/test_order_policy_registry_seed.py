from tools.pr168_rank_validator import run_validation


def test_order_policy_registry_seed() -> None:
    run_validation("order_policy_registry_seed")
