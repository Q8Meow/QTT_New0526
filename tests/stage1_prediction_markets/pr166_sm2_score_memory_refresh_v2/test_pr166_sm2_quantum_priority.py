from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_quantum_priority_preserves_backend_boundary():
    priority = assert_report_rows("PR166_SM2_QuantumPriority.report.json", 559)
    structure = assert_report_rows("PR166_SM2_QuantumStructure.report.json", 559)
    assert all(not row["quantum_backend_execution_allowed"] for row in priority[:100])
    assert all(row["backend_execution_status"] == "NOT_EXECUTED_ROUTE_ONLY" for row in structure[:100])
