from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_retirement_is_non_destructive() -> None:
    rows = records("PR168_MAP3_FormulaRetirementCandidates.report.json")
    assert rows
    assert all(row["historical_record_preserved_flag"] is True for row in rows)
    assert all(row["deletion_performed_flag"] is False for row in rows)
