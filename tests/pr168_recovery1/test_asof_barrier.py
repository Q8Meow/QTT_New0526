from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_asof_barrier_fields_exist() -> None:
    assert_recovery1_valid()
    assert all(row["decision_time_utc"] and row["data_asof_utc"] and row["max_input_timestamp_utc"] for row in rows("retest_before_after"))
