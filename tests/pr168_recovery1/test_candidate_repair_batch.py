from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_candidate_repair_batch_is_bounded() -> None:
    assert_recovery1_valid()
    assert all(row["bounded_variant_count"] == 1 for row in rows("candidate_repair_batch"))
