from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_conversion_math_has_exact_levers():
    rows = assert_report_rows("PR166_SM2_ConversionMath.report.json", 3213)
    assert all(row["minimum_edge_uplift_needed_to_cross_zero"] > 0 for row in rows[:100])
    assert all(row["candidate_parameter_perturbation_plan"] for row in rows[:100])
