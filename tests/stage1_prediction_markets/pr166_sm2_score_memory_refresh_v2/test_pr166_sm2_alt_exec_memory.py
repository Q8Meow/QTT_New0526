from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_alt_exec_memory_covers_negative_rows():
    rows = assert_report_rows("PR166_SM2_AltExecMemory.report.json", 3213)
    assert all(row["execution_path_requires_replay_paper_retest"] for row in rows[:100])
