from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_parameter_uplift_rows_have_plan():
    rows = assert_report_rows("PR166_SM2_ParamUpliftLedger.report.json", 3213)
    assert all(row["candidate_parameter_perturbation_plan"] for row in rows[:100])
