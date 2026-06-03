from tools import ci_branch_context as context
from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import (
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


def test_pr159s_pr162c_downstream_branch_allows_cumulative_validation(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.delenv("GITHUB_REF", raising=False)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)

    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, PR162C_DOWNSTREAM_BRANCH, ""
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, PR162C_DOWNSTREAM_BRANCH, ""
        if command[:2] == ("merge-base", "--is-ancestor"):
            return 1, "", "not ancestor"
        if command[:3] == ("log", "--format=%s", "--fixed-strings"):
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    failures: list[str] = []
    receipts: list[str] = []
    monkeypatch.setattr(validator, "_git_stdout", fake_git_stdout)

    validator._validate_branch(validator.Path(__file__).resolve().parents[3], failures, receipts)

    assert failures == []
    assert receipts == []


def test_pr159s_pr162d_downstream_branch_allows_cumulative_validation(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.delenv("GITHUB_REF", raising=False)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)

    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, PR162D_DOWNSTREAM_BRANCH, ""
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, PR162D_DOWNSTREAM_BRANCH, ""
        if command[:2] == ("merge-base", "--is-ancestor"):
            return 1, "", "not ancestor"
        if command[:3] == ("log", "--format=%s", "--fixed-strings"):
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    failures: list[str] = []
    receipts: list[str] = []
    monkeypatch.setattr(validator, "_git_stdout", fake_git_stdout)

    validator._validate_branch(validator.Path(__file__).resolve().parents[3], failures, receipts)

    assert failures == []
    assert receipts == []


def test_pr159s_pr162d_r1_downstream_branch_allows_cumulative_validation(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.delenv("GITHUB_REF", raising=False)
    monkeypatch.delenv("GITHUB_REF_NAME", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)

    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, PR162D_R1_DOWNSTREAM_BRANCH, ""
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, PR162D_R1_DOWNSTREAM_BRANCH, ""
        if command[:2] == ("merge-base", "--is-ancestor"):
            return 1, "", "not ancestor"
        if command[:3] == ("log", "--format=%s", "--fixed-strings"):
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    failures: list[str] = []
    receipts: list[str] = []
    monkeypatch.setattr(validator, "_git_stdout", fake_git_stdout)

    validator._validate_branch(validator.Path(__file__).resolve().parents[3], failures, receipts)

    assert failures == []
    assert receipts == []

