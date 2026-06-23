from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report, rows


def test_merge_readiness_decision_blocks_report_count_only_merges():
    assert_recovery1_valid()
    audit = report("PR168_RECOVERY1_ProductivityAudit.report.json")["records"]
    merge_rows = rows("merge_readiness_decision")

    assert merge_rows
    decision = merge_rows[0]
    assert audit["productivity_assessment"] != "REPORT_COUNT_ONLY"
    assert decision["merge_readiness_state"] == "RECOVERY1_PRODUCTIVE_READY_TO_MERGE"
    assert decision["github_pr_ci_green_required_flag"] is True
    assert decision["allowed_to_auto_merge_if_ci_green_flag"] is True
    assert decision["owner_acceptance_required_flag"] is False
    assert decision["do_not_merge_flag"] is False
