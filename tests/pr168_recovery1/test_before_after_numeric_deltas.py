from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report, rows


def test_before_after_numeric_deltas_are_exact_from_retest_rows():
    assert_recovery1_valid()
    delta_rows = rows("before_after_delta")
    audit = report("PR168_RECOVERY1_ProductivityAudit.report.json")["records"]

    assert delta_rows
    assert len(delta_rows) == audit["retest_before_after_count"]
    for row in delta_rows:
        assert round(row["after_net_expected_pnl_candidate"] - row["before_net_expected_pnl_candidate"], 8) == row["delta_net_expected_pnl_candidate"]
        assert round(row["after_fill_adjusted_expected_pnl"] - row["before_fill_adjusted_expected_pnl"], 8) == row["delta_fill_adjusted_expected_pnl"]
        assert round(row["after_execution_adjusted_edge"] - row["before_execution_adjusted_edge"], 8) == row["delta_execution_adjusted_edge"]
        assert round(row["after_no_trade_margin_candidate"] - row["before_no_trade_margin_candidate"], 8) == row["delta_no_trade_margin_candidate"]
        assert round(row["after_TCA_total_candidate"] - row["before_TCA_total_candidate"], 8) == row["delta_TCA_total_candidate"]
        assert row["invalid_cost_fill_probability_assumption_flag"] is False
        assert row["fill_defaulted_to_one_flag"] is False
        assert row["cost_defaulted_to_zero_flag"] is False
