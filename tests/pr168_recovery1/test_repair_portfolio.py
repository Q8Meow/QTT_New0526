from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_repair_portfolio_selected_by_utility() -> None:
    assert_recovery1_valid()
    assert any(row["selected_for_repair_now_flag"] for row in rows("repair_portfolio"))
