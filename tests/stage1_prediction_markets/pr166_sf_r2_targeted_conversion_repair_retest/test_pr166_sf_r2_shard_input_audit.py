from __future__ import annotations

from .helpers import assert_all_rows_connected


def test_pr166_sf_r2_shard_input_audit():
    rows = assert_all_rows_connected("PR166_SF_R2_ShardInputAudit.report.json", allow_empty=False)
    if not False:
        assert rows
