from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_memory_ledger_is_condition_scoped():
    rows = assert_report_rows("PR166_SM2_MemoryLedger.report.json", 3215)
    assert all(row["condition_scoped_memory_only"] for row in rows)
    assert all(not row["global_permanent_ban_created"] for row in rows)
