from tools.pr168_rank_validator import run_validation


def test_no_orphan() -> None:
    run_validation("no_orphan")
