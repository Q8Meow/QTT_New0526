from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_net_edge_results_are_execution_adjusted():
    rows = assert_report_rows("PR166_S2_NetEdgeResultLedger.report.json", 3215)
    positives = [row for row in rows if row["replay_paper_net_edge_after_costs"] > 0]
    assert len(positives) == summary()["positive_replay_paper_net_edge_rows"]
    assert all(row["positive_simulated_edge_is_profit_evidence"] is False for row in positives)
