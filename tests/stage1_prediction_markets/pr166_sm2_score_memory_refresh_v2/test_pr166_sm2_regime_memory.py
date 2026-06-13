from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_regime_memory_is_not_global_ban():
    rows = assert_report_rows("PR166_SM2_RegimeMemoryLedger.report.json", 3215)
    assert all(not row["global_permanent_ban_created"] for row in rows)
