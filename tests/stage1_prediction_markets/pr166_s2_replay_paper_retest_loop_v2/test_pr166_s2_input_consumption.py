from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_input_consumption_reads_required_roots_and_shards():
    rows = assert_report_rows("PR166_S2_InputAudit.report.json")
    assert any(row["upstream_report_ref"] == "PR166_SF_RepairedCandidateRetestQueue.report.json" for row in rows)
    assert all(row["read_total_row_count"] >= 1 for row in rows)
