from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_source_provenance_candidate_usable_without_truth_authority() -> None:
    assert_recovery1_valid()
    assert len(rows("source_provenance")) == 5
    assert all(row["candidate_only_flag"] and not row["accepted_truth_flag"] for row in rows("source_provenance"))
