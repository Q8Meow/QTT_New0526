from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_stack_repair_has_causal_action_family() -> None:
    assert_recovery1_valid()
    assert all(row["failure_cause_family"] and row["repair_action_family"] for row in rows("stack_repair"))
