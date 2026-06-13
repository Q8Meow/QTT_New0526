from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_execution_readiness_routes_every_primary_row():
    rows = assert_report_rows("PR166_S2_ExecReadinessAudit.report.json", 3215)
    allowed = {"EXECUTION_READY_FOR_REPLAY_PAPER_V2", "NO_FILL_SIMULATION_ONLY_WITH_REASON", "ROUTE_BACK_TO_PR166_SF_R2_WITH_REASON", "ROUTE_TO_PR162D_R3_GAP_WITH_REASON", "TERMINAL_BY_NATURE_WITH_REASON"}
    assert all(row["readiness_state"] in allowed for row in rows)
