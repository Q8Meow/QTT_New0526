from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_repair_priority_has_expected_impact() -> None:
    assert_rank3_valid()
    assert all(row["expected_utility_recovery_score"] > 0 for row in rows("repair_priority"))
