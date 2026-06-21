from tests.pr168_gfp2.pr168_gfp2_test_support import BASELINE_COUNTS, full_universe_count


def test_no_selected_35_only_pass() -> None:
    assert full_universe_count() > BASELINE_COUNTS["selected_formula_count"]
