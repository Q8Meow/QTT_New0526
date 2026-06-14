from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_positive_negative_edge_counts_do_not_inflate():
    positives = assert_report_rows("PR166_SM2_PosEdgeRegistry.report.json", 2)
    negatives = assert_report_rows("PR166_SM2_NegEdgeRegistry.report.json", 3213)
    assert all(row["profit_evidence_count"] == 0 for row in positives)
    assert all(row["break_even_gap"] >= 0 for row in negatives[:50])
