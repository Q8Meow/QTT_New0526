from tools.pr168_rank_validator import run_validation


def test_registry_anti_scatter() -> None:
    run_validation("registry_anti_scatter")
