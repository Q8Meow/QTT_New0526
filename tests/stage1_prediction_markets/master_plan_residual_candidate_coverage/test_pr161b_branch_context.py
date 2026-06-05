from tools import ci_branch_context as context
from src.qtt.stage1_prediction_markets.master_plan_residual_candidate_coverage import (
    validator,
)


PR162C_DOWNSTREAM_BRANCH = (
    "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage"
)
PR162D_DOWNSTREAM_BRANCH = (
    "pr162d-aggressive-qku-candidate-materialization-agent-routing"
)
PR162D_R1_DOWNSTREAM_BRANCH = (
    "pr162d-r1-external-formula-data-quantum-acquisition-expansion"
)
PR162R_A_DOWNSTREAM_BRANCH = (
    "pr162r-a-replay-paper-executability-classification-audit"
)
PR162D_R2A_DOWNSTREAM_BRANCH = (
    "pr162d-r2a-real-computable-formulations-redo"
)
PR162R_DOWNSTREAM_BRANCH = (
    "pr162r-generic-replay-paper-adapter-rerun"
)


def test_pr161b_branch_context_allows_only_pr161b_scope():
    branch = "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR161B_ResidualCoverageFinalSummary.report.json")
    assert context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json")
    assert context.is_explicit_downstream_repair_changed_path(branch, "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage/validator.py")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/QTT_MasterPlan_Current.md")
    assert not context.is_explicit_downstream_repair_changed_path(branch, "docs/master_plan/generated/PR160_Unrelated.report.json")


def test_pr161b_pr162c_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162C_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161b_pr162d_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162D_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161b_pr162d_r1_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162D_R1_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161b_pr162r_a_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162R_A_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161b_pr162d_r2a_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162D_R2A_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161b_pr162r_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162R_DOWNSTREAM_BRANCH,
        )
        is True
    )
