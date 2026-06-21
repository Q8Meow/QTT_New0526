from tests.pr168_gfp2.pr168_gfp2_test_support import BASELINE_COUNTS, load


def test_unselected_qkus_are_reopened_or_exactly_routed() -> None:
    rows = load("PR168_GFP2_UnselectedQKUReopenLedger.report.json")
    assert len(rows) == BASELINE_COUNTS["formula_assignment_count"]
    assert all(row["requires_real_market_recompute_flag"] for row in rows[:1000])
