from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_search_audit_has_receipts():
    rows = assert_report_rows("PR166_S2_SearchAudit.report.json", 10)
    assert {row["search_receipt_status"] for row in rows} <= {"USEFUL_SIGNAL_RECEIPT", "NO_USEFUL_SIGNAL_RECEIPT", "UNAVAILABLE_RECEIPT"}
