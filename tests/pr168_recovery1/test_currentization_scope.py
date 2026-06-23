from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_currentization_required_for_recovery1_scope_registration() -> None:
    assert_recovery1_valid()
    records = report("PR168_RECOVERY1_CurrentizationNeedAudit.report.json")["records"]
    assert records["status"] == "required_and_currentized"
    assert (
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
        in records["allowed_shared_currentization_files"]
    )
