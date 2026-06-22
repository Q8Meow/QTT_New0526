from tests.pr168_gfp2r._helpers import assert_positive_count, rows


def test_pr168_gfp2r_formula_variants_have_unit_dimension_validation() -> None:
    variant_rows = rows("formula_variant")
    assert all("formula_dimension_validation_state" in row for row in variant_rows)
    assert any(row["formula_units_valid_flag"] is False for row in variant_rows)
    assert_positive_count("formula_variant_unit_invalid_count")
