from tools.pr168_rp_validator import run_validation


def test_tca_decomposition() -> None:
    run_validation("tca_pnl_math")
