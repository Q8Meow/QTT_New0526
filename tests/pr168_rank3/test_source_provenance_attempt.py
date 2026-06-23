from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_all_source_review_formulas_attempt_candidate_provenance() -> None:
    assert_rank3_valid()
    attempts = rows("source_provenance_attempt")
    assert len(attempts) == 5
    assert all(row["official_source_required_flag"] is False for row in attempts)
