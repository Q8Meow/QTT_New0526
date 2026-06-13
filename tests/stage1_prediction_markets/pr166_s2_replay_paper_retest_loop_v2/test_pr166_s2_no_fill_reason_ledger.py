from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_no_fill_reason_ledger_has_exact_reasons():
    rows = assert_report_rows("PR166_S2_NoFillReasonLedger.report.json", summary()["no_fill_reason_rows"])
    assert all(row["no_fill_reason"] != "" for row in rows)
    assert all(row["repair_or_terminal_route"] for row in rows)
