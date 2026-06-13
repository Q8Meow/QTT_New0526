from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_overfit_and_rank_stability_are_bounded():
    overfit = assert_report_rows("PR166_S2_OverfitFDRLedger.report.json", 3215)
    rank = assert_report_rows("PR166_S2_RankStabilityLedger.report.json", 3215)
    assert all(0 <= row["false_discovery_risk_adjustment"] <= 1 for row in overfit[:200])
    assert all(0 <= row["rank_stability_score"] <= 1 for row in rank[:200])
