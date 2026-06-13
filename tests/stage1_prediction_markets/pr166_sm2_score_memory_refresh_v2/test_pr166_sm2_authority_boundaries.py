from __future__ import annotations

from .helpers import assert_report_rows, summary
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2.authority import ZERO_AUTHORITY_KEYS


def test_pr166_sm2_authority_counts_are_zero():
    row = assert_report_rows("PR166_SM2_AuthorityAudit.report.json", 1)[0]
    for key in ZERO_AUTHORITY_KEYS:
        assert row[key] == 0
        assert summary()[key] == 0
