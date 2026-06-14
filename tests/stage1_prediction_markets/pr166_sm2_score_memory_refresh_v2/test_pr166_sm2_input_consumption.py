from __future__ import annotations

from .helpers import assert_report_rows
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c


def test_pr166_sm2_input_consumption_covers_required_reports():
    rows = assert_report_rows("PR166_SM2_InputAudit.report.json", len(c.REQUIRED_INPUT_REPORTS))
    assert all(row["required_input_present"] for row in rows)
    assert any(row["sharded_input_consumed"] for row in rows)
