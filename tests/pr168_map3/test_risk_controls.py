from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_risk_control_rows_are_nonproof_priority_inputs() -> None:
    rows = records("PR168_MAP3_RiskControls.report.json")
    assert rows
    assert all(row["not_profit_proof_flag"] is True for row in rows)
