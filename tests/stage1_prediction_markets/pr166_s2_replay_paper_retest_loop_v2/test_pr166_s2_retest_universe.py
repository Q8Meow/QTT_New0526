from __future__ import annotations

from .helpers import assert_common_replay_row, assert_report_rows


def test_pr166_s2_retest_universe_has_expected_primary_rows():
    rows = assert_report_rows("PR166_S2_RetestUniverse.report.json", 3215)
    assert len({row["candidate_packet_id"] for row in rows}) == 3215
    assert all(row["retest_target_class"] for row in rows)
    assert_common_replay_row(rows[0])
