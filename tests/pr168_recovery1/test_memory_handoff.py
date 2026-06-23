from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_memory_handoff_rows_have_conditions() -> None:
    assert_recovery1_valid()
    assert all(row["condition_id"] and row["before_after_refs"] for row in rows("learning_memory"))
