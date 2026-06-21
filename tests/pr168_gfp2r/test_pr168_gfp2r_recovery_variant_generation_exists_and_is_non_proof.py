from tests.pr168_gfp2r._helpers import assert_positive_count, rows


def test_pr168_gfp2r_recovery_variant_generation_exists_and_is_non_proof() -> None:
    assert_positive_count("recovery_variant_generated_count")
    assert all(row["authority_class"] == "PR168_GFP2R_CANDIDATE_ONLY_NON_PROOF" for row in rows("recovery_variant"))
