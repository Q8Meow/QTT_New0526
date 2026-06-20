from tools.pr168_rp_validator import run_validation


def test_regime_conditioned_memory() -> None:
    run_validation("regime_memory")
