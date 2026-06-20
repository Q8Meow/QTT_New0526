from tools.pr168_rank_validator import run_validation


def test_market_adapter_registry_seed() -> None:
    run_validation("market_adapter_registry_seed")
