from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_quantum_objective_readiness_report_contract():
    rows = assert_report_contract("PR166_SM3_QuantumObjectiveReady.report.json", 559)
    assert rows
