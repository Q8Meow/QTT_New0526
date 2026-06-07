from tools import ci_branch_context as context
from src.qtt.stage1_prediction_markets.atomicrows_pr154_value_state.pr161a_materialization_bridge import (
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
PR162R_B_DOWNSTREAM_BRANCH = (
    "pr162r-b-replay-paper-data-binding-completion"
)
PR163_DOWNSTREAM_BRANCH = (
    "pr163-generic-paper-adapter-capture-framework"
)
PR163_C_MAIN_CONTEXT_REPAIR_BRANCH = (
    context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH
)
REPO_ROOT = validator.Path(__file__).resolve().parents[3]
BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)


def _clear_env(monkeypatch):
    for env_name in BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def _set_pull_request_detached_env(monkeypatch, *, head_ref: str):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/200/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "200/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", head_ref)


def _detached_branch_outcome(monkeypatch, *, head_ref: str):
    _set_pull_request_detached_env(monkeypatch, head_ref=head_ref)

    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    failures: list[str] = []
    receipts: list[str] = []
    monkeypatch.setattr(validator, "_git_stdout", fake_git_stdout)
    validator._validate_branch(REPO_ROOT, failures, receipts)
    return tuple(failures), tuple(receipts)


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


def test_pr161a_pr162d_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162D_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161a_pr162d_r1_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162D_R1_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161a_pr162r_a_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162R_A_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161a_pr162d_r2a_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162D_R2A_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161a_pr162r_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162R_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161a_pr162r_b_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR162R_B_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161a_pr163_downstream_branch_allows_cumulative_validation():
    assert (
        validator._branch_context_allowed(
            validator.Path(__file__).resolve().parents[3],
            PR163_DOWNSTREAM_BRANCH,
        )
        is True
    )


def test_pr161a_detached_head_pr163_c_repair_pr_context_allowed(monkeypatch):
    failures, receipts = _detached_branch_outcome(
        monkeypatch,
        head_ref=PR163_C_MAIN_CONTEXT_REPAIR_BRANCH,
    )

    assert failures == ()
    assert receipts == ("PR161A_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY",)


def test_pr161a_detached_head_unrelated_repair_head_ref_remains_blocked(
    monkeypatch,
):
    failures, receipts = _detached_branch_outcome(
        monkeypatch,
        head_ref="repair/pr163-c-unrelated-context",
    )

    assert failures == ("PR161A_BLOCKED_WRONG_BRANCH:DETACHED_HEAD",)
    assert receipts == ()
