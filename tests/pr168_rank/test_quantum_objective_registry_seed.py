from tools.pr168_rank_validator import run_validation


def test_quantum_objective_registry_seed() -> None:
    run_validation("quantum_objective_registry_seed")
