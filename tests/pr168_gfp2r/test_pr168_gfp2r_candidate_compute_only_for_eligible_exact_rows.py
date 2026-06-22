from tests.pr168_gfp2r._helpers import rows


def test_pr168_gfp2r_candidate_compute_only_for_eligible_exact_rows() -> None:
    exact_variants = [row for row in rows("formula_variant") if row["exact_candidate_compute_eligible_flag"]]
    exact_executions = [row for row in rows("formula_execution") if row["compute_lane"] == "EXACT_QKU_FORMULA"]
    assert exact_variants == []
    assert exact_executions == []
