from tests.pr168_gfp2.pr168_gfp2_test_support import BASELINE_COUNTS, full_universe_count


def test_full_universe_not_selected35_only() -> None:
    assert full_universe_count() == BASELINE_COUNTS["formula_assignment_count"]
    assert full_universe_count() > BASELINE_COUNTS["selected_formula_count"]
