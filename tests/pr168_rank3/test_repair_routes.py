from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_repair_routes_preserve_no_trade_dominated_rows() -> None:
    assert_rank3_valid()
    assert len(rows("repair_route")) == 35
