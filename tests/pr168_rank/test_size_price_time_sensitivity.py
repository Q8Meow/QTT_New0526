from tools.pr168_rank_validator import run_validation


def test_size_price_time_sensitivity() -> None:
    run_validation("size_price_time_sensitivity")
