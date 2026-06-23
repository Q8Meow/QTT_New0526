from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_candidate_input_confidence_non_proof() -> None:
    assert_recovery1_valid()
    assert all(row["input_confidence_class"] for row in rows("candidate_input_confidence"))
