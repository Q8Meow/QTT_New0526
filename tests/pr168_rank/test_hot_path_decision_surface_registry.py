from tools.pr168_rank_validator import run_validation


def test_hot_path_decision_surface_registry() -> None:
    run_validation("hot_path_decision_surface_registry")
