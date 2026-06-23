from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_tca_fill_capacity_no_default_one_or_zero() -> None:
    assert_recovery1_valid()
    assert all(not row["fill_defaulted_to_one_flag"] and not row["cost_defaulted_to_zero_flag"] for row in rows("tca_fill_capacity_retest"))
