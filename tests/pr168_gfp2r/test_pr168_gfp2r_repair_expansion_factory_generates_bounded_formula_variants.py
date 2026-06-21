from tests.pr168_gfp2r._helpers import assert_positive_count, rows


def test_pr168_gfp2r_repair_expansion_factory_generates_bounded_formula_variants() -> None:
    variant_rows = rows("formula_variant")
    assert_positive_count("formula_variant_generated_count")
    assert 1 <= len(variant_rows) <= 250
