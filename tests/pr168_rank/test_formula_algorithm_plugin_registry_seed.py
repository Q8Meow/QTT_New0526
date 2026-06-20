from tools.pr168_rank_validator import run_validation


def test_formula_algorithm_plugin_registry_seed() -> None:
    run_validation("formula_algorithm_plugin_registry_seed")
