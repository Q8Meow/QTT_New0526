from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_learning_feedback_is_condition_scoped() -> None:
    assert_rank3_valid()
    assert all(row["condition_scope"] for row in rows("learning_feedback"))
