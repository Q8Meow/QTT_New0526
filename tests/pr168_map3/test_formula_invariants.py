from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_formula_invariants_exist_without_failures() -> None:
    rows = records("PR168_MAP3_Invariants.report.json")
    assert len(rows) == summary()["formula_invariant_row_count"]
    assert summary()["formula_invariant_failure_count"] == 0
