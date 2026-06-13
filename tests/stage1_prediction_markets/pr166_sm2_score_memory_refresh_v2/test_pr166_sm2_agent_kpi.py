from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_agent_kpi_reports_conversion_coverage():
    rows = assert_report_rows("PR166_SM2_AgentKPIAudit.report.json", 8)
    assert all(row["negative_conversion_plan_coverage_pct"] == 1.0 for row in rows)
