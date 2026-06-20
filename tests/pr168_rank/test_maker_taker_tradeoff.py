from tools.pr168_rank_validator import run_validation


def test_maker_taker_tradeoff() -> None:
    run_validation("maker_taker_tradeoff")
