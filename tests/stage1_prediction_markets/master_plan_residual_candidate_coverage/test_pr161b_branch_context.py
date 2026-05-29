from tools import ci_branch_context as context


def test_pr161b_branch_context_allows_only_pr161b_scope():
    branch = "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR161B_ResidualCoverageFinalSummary.report.json")
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json")
    assert context.is_explicit_downstream_repair_changed_path(branch, "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/QTT_MasterPlan_Current.md")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR160_Unrelated.report.json")
