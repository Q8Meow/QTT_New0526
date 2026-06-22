from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_candidate_numeric_evidence_is_non_proof() -> None:
    evidence_rows = rows("candidate_numeric_evidence")
    assert evidence_rows
    assert all(row["candidate_only_flag"] is True for row in evidence_rows)
    assert all(row["authority_class"] == "PR168_GFP2R_CANDIDATE_ONLY_NON_PROOF" for row in evidence_rows)
