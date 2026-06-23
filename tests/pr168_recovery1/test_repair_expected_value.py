from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_repair_expected_value_non_negative() -> None:
    assert_recovery1_valid()
    assert all(row["repair_expected_value_non_proof"] >= 0 for row in rows("repair_expected_value"))
