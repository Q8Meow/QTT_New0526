from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_hidden_binding_does_not_promote_unproven_exact_identity() -> None:
    rows = records("PR168_MAP3_HiddenBind.report.json")
    assert summary()["hidden_exact_binding_promoted_count"] == 0
    assert all(row["exact_repaired_existing_qku_formula_binding_flag"] is False for row in rows)
