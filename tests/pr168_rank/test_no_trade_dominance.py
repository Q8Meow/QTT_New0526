from tools.pr168_rank_validator import run_validation


def test_no_trade_dominance() -> None:
    run_validation("no_trade_dominance")
