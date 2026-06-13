from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_time_to_resolution_risk_is_classified():
    row = assert_report_rows("PR166_S2_TTRiskLedger.report.json", 3215)[0]
    assert row["time_to_resolution_bucket"] in {"NEAR", "MID", "FAR"}
    assert row["settlement_uncertainty"] >= 0
