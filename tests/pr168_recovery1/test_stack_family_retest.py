from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_stack_family_retest_has_baseline_and_repaired_stack() -> None:
    assert_recovery1_valid()
    assert all(row["baseline_stack_ref"] and row["repaired_stack_ref"] for row in rows("stack_family_retest"))
