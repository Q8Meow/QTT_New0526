from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_shard_input_audit_proves_declared_shards_read():
    rows = assert_report_rows("PR166_S2_ShardInputAudit.report.json")
    sharded = [row for row in rows if row["records_omitted_for_sharding_flag"]]
    assert sharded
    assert all(row["declared_shard_count"] == row["read_shard_count"] for row in sharded)
    assert all(row["declared_total_row_count"] == row["read_total_row_count"] for row in sharded)
