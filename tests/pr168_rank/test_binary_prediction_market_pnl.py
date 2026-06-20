from tools.pr168_rank_validator import run_validation


def test_binary_prediction_market_pnl() -> None:
    run_validation("binary_prediction_market_pnl")
