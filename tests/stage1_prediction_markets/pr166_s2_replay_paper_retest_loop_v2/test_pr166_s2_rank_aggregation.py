from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_rank_aggregation_uses_stress_ranks():
    row = assert_report_rows("PR166_S2_RankAggregationLedger.report.json", 3215)[0]
    assert row["base_rank"] >= 1
    assert row["aggregate_rank"] >= row["base_rank"]
    assert "rank_method_disagreement" in row
