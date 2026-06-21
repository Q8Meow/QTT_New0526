from tests.pr168_gfp2.pr168_gfp2_test_support import validate_gap_repair_recovery


def test_every_negative_or_unverified_candidate_has_recovery_ladder_or_structural_proof() -> None:
    validate_gap_repair_recovery()
