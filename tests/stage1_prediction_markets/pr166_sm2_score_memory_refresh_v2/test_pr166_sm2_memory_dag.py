from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_memory_dag_rows_are_connected():
    rows = assert_report_rows("PR166_SM2_MemoryDAGLedger.report.json", 3215)
    assert all(row["dag_connected"] for row in rows[:100])
