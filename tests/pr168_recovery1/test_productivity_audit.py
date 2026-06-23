from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report, rows


def test_productivity_audit_exists_and_proves_non_infrastructure_output():
    assert_recovery1_valid()
    audit = report("PR168_RECOVERY1_ProductivityAudit.report.json")["records"]

    assert audit["productivity_assessment"] == "PRODUCTIVE_NUMERIC_AND_USABILITY_IMPROVEMENT_NON_PROOF"
    assert audit["actual_numeric_improvement_flag"] is True
    assert audit["actual_usability_improvement_flag"] is True
    assert audit["actual_downstream_batch_strengthened_flag"] is True
    assert audit["infrastructure_only_flag"] is False
    assert audit["merge_productivity_pass_flag"] is True
    assert audit["sum_delta_net_expected_pnl_candidate"] > 0
    assert audit["sum_delta_fill_adjusted_expected_pnl"] > 0
    assert audit["sum_delta_execution_adjusted_edge"] > 0
    assert audit["sum_delta_no_trade_margin_candidate"] > 0
    assert audit["sum_delta_TCA_total_candidate"] < 0
    assert rows("productivity_audit")[0]["no_orphan_status"] == "NO_ORPHAN"
