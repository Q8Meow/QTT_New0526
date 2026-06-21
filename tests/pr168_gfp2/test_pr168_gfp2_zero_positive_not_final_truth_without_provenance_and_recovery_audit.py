from tests.pr168_gfp2.pr168_gfp2_test_support import validate_zero_positive_not_final


def test_zero_positive_not_final_truth_without_provenance_and_recovery_audit() -> None:
    validate_zero_positive_not_final()
