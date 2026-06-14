from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_quantum_combo_ready_report_contract():
    rows = assert_report_contract("PR166_SM3_QuantumComboReady.report.json", 559)
    assert rows
