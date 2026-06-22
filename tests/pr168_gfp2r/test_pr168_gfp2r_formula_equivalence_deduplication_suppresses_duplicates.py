from tests.pr168_gfp2r._helpers import assert_positive_count, rows


def test_pr168_gfp2r_formula_equivalence_deduplication_suppresses_duplicates() -> None:
    equivalence_rows = rows("formula_equivalence")
    assert any(row["deduplication_decision"] == "SUPPRESS_DUPLICATE" for row in equivalence_rows)
    assert_positive_count("formula_variant_duplicate_suppressed_count")
