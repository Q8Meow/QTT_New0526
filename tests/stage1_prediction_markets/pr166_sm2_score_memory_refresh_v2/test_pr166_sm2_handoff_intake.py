from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_handoff_intake_consumed_from_shards():
    rows = assert_report_rows("PR166_SM2_HandoffIntake.report.json", 3215)
    assert all(row["score_memory_ready_flag"] for row in rows)
    assert any(row["handoff_consumed_from_shard"] for row in rows)
