from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_selection_pressure_enforces_family_quota():
    rows = assert_report_rows("PR166_SM2_SelectionPressure.report.json", 32)
    assert all(row["family_quota"] == 16 for row in rows)
    assert all(row["fdr_adjusted"] for row in rows)
