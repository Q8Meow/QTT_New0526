from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_recovery_attribution_has_changed_and_unchanged_inputs() -> None:
    assert_recovery1_valid()
    assert all(row["changed_input_refs"] and row["unchanged_input_refs"] for row in rows("recovery_attribution"))
