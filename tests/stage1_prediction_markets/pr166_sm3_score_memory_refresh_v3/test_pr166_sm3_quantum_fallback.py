from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_quantum_fallback_report_contract():
    rows = assert_report_contract("PR166_SM3_QuantumFallback.report.json", 559)
    assert rows
