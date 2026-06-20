from tools.pr168_rp_validator import run_validation


def test_no_trade_candidate() -> None:
    run_validation("no_trade_candidate")
