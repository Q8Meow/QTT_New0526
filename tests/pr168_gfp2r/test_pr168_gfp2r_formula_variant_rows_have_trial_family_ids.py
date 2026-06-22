from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_formula_variant_rows_have_trial_family_ids() -> None:
    assert all(row["trial_family_id"] and row["parameter_family_id"] for row in rows("formula_variant"))
