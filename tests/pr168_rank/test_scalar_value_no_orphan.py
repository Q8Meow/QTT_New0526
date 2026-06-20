from tools.pr168_rank_validator import run_validation


def test_scalar_value_no_orphan() -> None:
    run_validation("scalar_value_no_orphan")
