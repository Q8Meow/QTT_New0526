from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_recovery_factory_creates_bounded_candidates() -> None:
    rows = records("PR168_MAP3_FormulaRecoveryFactory.report.json")
    assert rows
    assert all(row["candidate_only_flag"] is True for row in rows)
    assert all(row["live_candidate_allowed_flag"] is False for row in rows)
