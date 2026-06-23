from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_missing_value_repair_no_fake_defaults() -> None:
    assert_recovery1_valid()
    assert all(not row["fill_defaulted_to_one_flag"] and not row["cost_defaulted_to_zero_flag"] for row in rows("missing_value_repair"))
