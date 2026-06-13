from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_implementation_shortfall_rows_are_computable():
    rows = assert_report_rows("PR166_S2_ImplShortfallLedger.report.json", 3215)
    assert all("implementation_shortfall" in row for row in rows[:100])
    assert all(row["implementation_shortfall_ref"].startswith("PR166_S2_IMPL_SHORTFALL::") for row in rows[:100])
