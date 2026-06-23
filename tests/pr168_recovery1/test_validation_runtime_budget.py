from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_validation_runtime_budget_scoped() -> None:
    assert_recovery1_valid()
    row = rows("validation_runtime")[0]
    assert row["new_validation_scope_added_flag"] is True
    assert row["currentization_required_flag"] is True
    assert row["github_full_validation_required_flag"] is True
