from tools.pr168_rank_validator import run_validation


def test_runtime_allowlist_seed_registry() -> None:
    run_validation("runtime_allowlist_seed_registry")
