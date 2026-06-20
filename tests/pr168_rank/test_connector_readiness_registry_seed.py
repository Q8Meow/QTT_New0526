from tools.pr168_rank_validator import run_validation


def test_connector_readiness_registry_seed() -> None:
    run_validation("connector_readiness_registry_seed")
