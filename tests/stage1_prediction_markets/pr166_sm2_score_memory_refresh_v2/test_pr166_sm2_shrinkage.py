from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_shrinkage_ledger_applies_evidence_depth():
    rows = assert_report_rows("PR166_SM2_ShrinkageLedger.report.json", 3215)
    assert all(row["empirical_bayes_style_shrinkage_applied"] for row in rows[:100])
