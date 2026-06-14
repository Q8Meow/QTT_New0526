from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_still_neg_recovery_report_contract():
    rows = assert_report_contract("PR166_SM3_StillNegRecovery.report.json", 3065)
    assert rows
