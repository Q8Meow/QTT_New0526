from __future__ import annotations

from ._helpers import REPORT_NAMES, assert_hard_zero_report, load_report


def test_rp5c_hard_zero_counters_remain_zero_on_all_reports() -> None:
    for report_name in REPORT_NAMES:
        assert_hard_zero_report(load_report(report_name))

    final = load_report("PR168_RP5C_FinalSummary.report.json")
    assert final["runtime_stack_generation_count"] == 0
    assert final["trade_simulation_count"] == 0
    assert final["formula_profit_ranking_count"] == 0
    assert final["qopt_batch_count"] == 0
    assert final["live_order_authority_created_count"] == 0
    assert final["source_truth_authority_created_count"] == 0
    assert final["quantum_backend_execution_count"] == 0
