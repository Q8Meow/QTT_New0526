from __future__ import annotations

from tests.pr168_recovery1._helpers import assert_recovery1_valid, report, rows


def test_zero_improvement_root_cause_is_only_required_for_zero_productivity():
    assert_recovery1_valid()
    audit = report("PR168_RECOVERY1_ProductivityAudit.report.json")["records"]
    root_cause_report = report("PR168_RECOVERY1_ZeroImprovementRootCause.report.json")["records"]

    assert audit["actual_numeric_improvement_flag"] is True
    assert audit["infrastructure_only_flag"] is False
    assert root_cause_report["root_cause_required_flag"] is False
    assert rows("zero_improvement_root_cause") == []
