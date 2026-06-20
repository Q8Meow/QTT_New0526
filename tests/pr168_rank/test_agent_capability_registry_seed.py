from tools.pr168_rank_validator import run_validation


def test_agent_capability_registry_seed() -> None:
    run_validation("agent_capability_registry_seed")
