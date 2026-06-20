from tools.pr168_rank_validator import run_validation


def test_venue_cost_model_registry_seed() -> None:
    run_validation("venue_cost_model_registry_seed")
