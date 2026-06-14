from __future__ import annotations

from .helpers import assert_report_rows
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c


def test_pr166_sm2_route_crosswalk_and_command_matrix_cover_reports():
    assert_report_rows("PR166_SM2_PlanCrosswalk.report.json", len(c.REPORT_FILENAMES))
    cmd = assert_report_rows("PR166_SM2_CmdActionMatrix.report.json", len(c.REPORT_FILENAMES))
    assert all(row["allowed_action"] == "READ_REPORT_AND_ROUTE_DOWNSTREAM_ONLY" for row in cmd)
