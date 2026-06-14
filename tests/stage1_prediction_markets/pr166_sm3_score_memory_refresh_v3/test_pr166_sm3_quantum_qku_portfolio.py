from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_quantum_qku_portfolio_report_contract():
    rows = assert_report_contract("PR166_SM3_QuantumQKUPortfolio.report.json", 559)
    assert rows
