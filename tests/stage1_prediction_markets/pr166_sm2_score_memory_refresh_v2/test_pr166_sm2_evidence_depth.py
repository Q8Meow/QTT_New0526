from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_evidence_depth_has_replay_paper_boundary():
    rows = assert_report_rows("PR166_SM2_EvidenceDepth.report.json", 3215)
    assert all(row["replay_paper_only_evidence_boundary"] for row in rows[:100])
