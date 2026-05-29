from .pr161a_test_support import REPO_ROOT, report


def test_pr161a_pr152_deterministic_audit_currentization_path_allowed():
    path = REPO_ROOT / "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    assert path.exists()
    audit = report("branch_context_audit")["records"][0]
    assert audit["pr152_currentization_allowed_by_pr161a_flag"] is True

