from tests.pr168_rp5b._helpers import final_summary


def test_no_trade_simulation() -> None:
    assert final_summary()["trade_simulation_count"] == 0
