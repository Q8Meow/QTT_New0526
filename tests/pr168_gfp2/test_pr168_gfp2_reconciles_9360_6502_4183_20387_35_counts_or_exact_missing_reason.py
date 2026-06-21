from tests.pr168_gfp2.pr168_gfp2_test_support import validate_counts


def test_reconciles_counts_or_exact_missing_reason() -> None:
    validate_counts()
