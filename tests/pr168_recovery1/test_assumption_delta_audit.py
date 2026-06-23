from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_assumption_delta_no_silent_weakening() -> None:
    assert_recovery1_valid()
    assert all(not row["silent_assumption_weakening_flag"] for row in rows("assumption_delta"))
