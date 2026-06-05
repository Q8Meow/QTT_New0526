from tools import ci_branch_context as context


def test_ci_branch_context_pr162r_b():
    branch = "pr162r-b-replay-paper-data-binding-completion"
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162R_B_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
