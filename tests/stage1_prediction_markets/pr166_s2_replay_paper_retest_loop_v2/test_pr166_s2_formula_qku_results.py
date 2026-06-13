from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_formula_qku_results_are_routed():
    rows = assert_report_rows("PR166_S2_FormulaQKUResultLedger.report.json", 3215)
    assert all(row["qku_id"].startswith("QKU-") for row in rows[:100])
    assert all(row["downstream_pr_refs"] for row in rows[:100])
