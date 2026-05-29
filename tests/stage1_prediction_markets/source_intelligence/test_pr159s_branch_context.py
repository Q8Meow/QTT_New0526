from tools import ci_branch_context as context


def test_pr159s_branch_context_uses_central_ci_helper():
    branch = "pr159s-open-source-intelligence-candidate-completion"
    assert context.is_pr_or_later_branch(branch, minimum_pr=159) is True
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR159S_SourceProfitProvenanceClassification.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )

