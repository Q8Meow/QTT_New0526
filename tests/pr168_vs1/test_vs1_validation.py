from __future__ import annotations

from ._helpers import assert_vs1_valid, report


def test_vs1_validator_passes_and_run_report_counts_core_materialized_artifacts():
    result = assert_vs1_valid()
    run = report("vs1_run_receipt.report.json")

    assert result["validation"] == "PR168_VS1_TRADING_INTELLIGENCE_SLICE_OK"
    assert 10 <= run["selected_identity_count"] <= 50
    assert run["metadata_only_selected_count"] == 0
    assert run["trade_plan_candidate_count"] > 0
    assert run["paper_intent_preview_count"] > 0
