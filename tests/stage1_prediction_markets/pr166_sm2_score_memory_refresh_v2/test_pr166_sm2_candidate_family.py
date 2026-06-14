from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_candidate_family_rows_have_action():
    rows = assert_report_rows("PR166_SM2_FamilyRegistry.report.json", 3215)
    assert all(row["family_action"] in {"EXPAND_AND_RETEST", "REPAIR_OR_CONVERT_AND_RETEST"} for row in rows[:100])
