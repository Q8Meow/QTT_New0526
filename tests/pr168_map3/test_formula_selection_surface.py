from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_selection_surface_is_candidate_only() -> None:
    rows = records("PR168_MAP3_FormulaSelectionSurface.report.json")
    assert rows
    assert all(row["confidence_state"] == "CANDIDATE_ONLY" for row in rows)
    assert all(row["not_profit_proof_flag"] is True for row in rows)
