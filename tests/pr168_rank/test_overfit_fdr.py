from tools.pr168_rank_validator import run_validation


def test_overfit_fdr() -> None:
    run_validation("overfit_fdr")
