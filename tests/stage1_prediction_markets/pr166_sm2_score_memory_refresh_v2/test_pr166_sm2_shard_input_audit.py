from __future__ import annotations

from .helpers import assert_report_rows
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c


def test_pr166_sm2_shard_input_audit_reads_declared_shards():
    rows = assert_report_rows("PR166_SM2_ShardInputAudit.report.json", len(c.REQUIRED_INPUT_REPORTS))
    assert all(row["continuation_allowed"] for row in rows)
    assert all(not row["row_count_mismatch_flag"] for row in rows)
