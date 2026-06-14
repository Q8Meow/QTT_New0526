from __future__ import annotations

from .helpers import assert_report_contract, summary


def test_pr166_sm3_no_orphan_audit_is_zero():
    assert_report_contract("PR166_SM3_OrphanAudit.report.json", 1)
    assert_report_contract("PR166_SM3_RowDAG.report.json", 109)
    assert summary()["orphan_count"] == 0
