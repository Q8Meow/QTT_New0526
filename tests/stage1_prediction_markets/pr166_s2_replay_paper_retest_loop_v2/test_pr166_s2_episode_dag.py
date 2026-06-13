from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_episode_dag_connects_retest_flow():
    row = assert_report_rows("PR166_S2_EpisodeDAGLedger.report.json", 3215)[0]
    assert "ORDER_INTENT_TO_FILL_OR_NO_FILL" in row["dag_edges"]
    assert len(row["dag_nodes"]) >= 8
