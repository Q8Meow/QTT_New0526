from tools import ci_branch_context as context


def test_ci_branch_context_allows_pr163_b_canonical_paths(monkeypatch):
    branch = "pr163-b-paired-replay-paper-concurrent-executor"
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor/report_builder.py",
    )
    assert context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR163_B_FinalSummary.report.json",
    )
    assert not context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
