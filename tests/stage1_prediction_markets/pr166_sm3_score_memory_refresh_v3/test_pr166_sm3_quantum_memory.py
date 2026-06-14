from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_quantum_memory_report_contract():
    rows = assert_report_contract("PR166_SM3_QuantumMemory.report.json", 559)
    assert rows
