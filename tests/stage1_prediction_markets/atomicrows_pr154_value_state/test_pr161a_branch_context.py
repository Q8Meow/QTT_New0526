from tools import ci_branch_context as context


def test_pr161a_branch_context_allows_only_pr161a_scope():
    branch = "pr161a-atomicrows-pr154-value-state-materialization-bridge"
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR161A_FinalValueStateSummary.report.json")
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/QTT_MasterPlan_Current.md")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR160_Unrelated.report.json")

