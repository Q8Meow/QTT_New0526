from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_ablation_covers_positive_and_high_priority_convertibles():
    rows = assert_report_rows("PR166_SM2_AblationLedger.report.json", 52)
    assert {row["ablation_subject_class"] for row in rows} >= {"POSITIVE_SEED", "HIGH_PRIORITY_CONVERTIBLE_NEGATIVE"}
