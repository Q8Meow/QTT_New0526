from __future__ import annotations


def test_pr162r_a_no_replay_or_paper_execution_occurs(summary, records):
    audit = records("PR162R_A_NoReplayPaperExecutionAudit.report.json")[0]
    assert summary["replay_execution_count"] == 0
    assert summary["paper_execution_count"] == 0
    assert audit["adapter_invocation_count"] == 0
