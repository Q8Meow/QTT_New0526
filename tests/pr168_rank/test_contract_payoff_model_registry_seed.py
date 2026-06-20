from tools.pr168_rank_validator import run_validation


def test_contract_payoff_model_registry_seed() -> None:
    run_validation("contract_payoff_model_registry_seed")
