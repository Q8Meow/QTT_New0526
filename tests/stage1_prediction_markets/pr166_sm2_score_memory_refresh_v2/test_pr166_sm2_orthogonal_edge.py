from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_orthogonal_edge_suppresses_redundant_clones():
    rows = assert_report_rows("PR166_SM2_OrthogonalEdge.report.json", 52)
    assert all(row["redundant_clone_suppression_required"] for row in rows)
