from tools import ci_branch_context as context
from src.qtt.stage1_prediction_markets.atomicrows_pr154_value_state.pr161a_materialization_bridge import (
    validator,
)


PR162C_DOWNSTREAM_BRANCH = (
    "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage"
)


def test_pr161a_branch_context_allows_only_pr161a_scope():
    branch = "pr161a-atomicrows-pr154-value-state-materialization-bridge"
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR161A_FinalValueStateSummary.report.json")
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/QTT_MasterPlan_Current.md")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR160_Unrelated.report.json")


def test_pr161a_pr162c_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162C_DOWNSTREAM_BRANCH,
        )
        is True
    )

