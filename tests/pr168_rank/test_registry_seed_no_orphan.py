from tools.pr168_rank_validator import run_validation


def test_registry_seed_no_orphan() -> None:
    run_validation("registry_seed_no_orphan")
