from __future__ import annotations

from ._helpers import rows


def test_vs1_overfit_fdr_receipts_use_deterministic_trial_count_penalty():
    receipts = rows("overfit_fdr_control_receipts.jsonl")

    assert receipts
    assert all(row["overfit_fdr_method"] == "VS1_DETERMINISTIC_TRIAL_COUNT_PENALTY" for row in receipts)
    assert all(row["future_dsr_ready_flag"] is True for row in receipts)
    assert all(row["future_pbo_ready_flag"] is True for row in receipts)
    assert all(row["future_bh_fdr_ready_flag"] is True for row in receipts)
    assert all(row["future_purged_embargo_ready_flag"] is True for row in receipts)
