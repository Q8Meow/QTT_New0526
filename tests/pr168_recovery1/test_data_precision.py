from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_data_precision_has_before_after_values() -> None:
    assert_recovery1_valid()
    assert all(row["before_value_or_gap"] >= row["after_value_or_gap"] for row in rows("data_precision"))
