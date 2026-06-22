from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_quantum_formula_lift_has_interpret_back_and_fallback() -> None:
    rows = records("PR168_MAP3_QFormulaLift.report.json")
    assert rows
    assert all(row["interpret_back_map_exists"] is True for row in rows)
    assert all(row["classical_fallback_exists"] is True for row in rows)
