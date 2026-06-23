from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_source_provenance_candidate_resolution_is_non_proof() -> None:
    assert_rank3_valid()
    resolutions = rows("source_provenance_resolution")
    assert {row["source_provenance_status"] for row in resolutions} == {"CANDIDATE_SOURCE_USABLE_NON_PROOF"}
    assert all(row["accepted_truth_flag"] is False for row in resolutions)
