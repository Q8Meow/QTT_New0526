from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_external_signals_report_contract():
    rows = assert_report_contract("PR166_SM3_ExternalSignals.report.json", 8)
    assert rows
