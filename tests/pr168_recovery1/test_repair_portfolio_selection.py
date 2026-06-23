from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_repair_portfolio_selection_has_expected_value() -> None:
    assert_recovery1_valid()
    assert all(row["expected_repair_value_non_proof"] >= 0 for row in rows("repair_portfolio"))
