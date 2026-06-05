from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c
from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import validator


REPO_ROOT = Path(__file__).resolve().parents[3]
REPAIR_BRANCH = "repair/pr159r-detached-head-branch-context"
PR160_REPAIR_BRANCH = "repair/pr160-main-ancestry-after-pr176"
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
GITHUB_BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)


def _clear_env(monkeypatch):
    for env_name in GITHUB_BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def _branch_ref_candidates(branch: str) -> set[str]:
    return {
        branch,
        f"refs/heads/{branch}",
        f"origin/{branch}",
        f"refs/remotes/origin/{branch}",
    }


def _branch_from_ref(ref: str, branches: set[str]) -> str:
    for branch in branches:
        if ref in _branch_ref_candidates(branch):
            return branch
    return ""


def _git(
    branch: str,
    *,
    ancestry_present: bool = False,
    ancestry_branches: set[str] | None = None,
):
    branches = set(ancestry_branches or set())
    if ancestry_present:
        branches.add(c.EXPECTED_BRANCH)

    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            if branch == "DETACHED_HEAD":
                return 0, "", ""
            return 0, branch, ""
        if command[:2] == ("merge-base", "--is-ancestor"):
            ancestor_branch = _branch_from_ref(command[2], branches)
            return (0, "", "") if ancestor_branch else (1, "", "not ancestor")
        if command[:3] == ("log", "--format=%s", "--fixed-strings"):
            grep = command[3].removeprefix("--grep=/")
            if grep in branches:
                return 0, f"Merge pull request #1 from Owner/{grep}\n", ""
            return (
                0,
                "",
                "",
            )
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, "HEAD" if branch == "DETACHED_HEAD" else branch, ""
        raise AssertionError(f"unexpected git command: {command!r}")

    return fake_git_stdout


def _branch_outcome(
    monkeypatch,
    branch: str,
    *,
    ancestry_present: bool = False,
    ancestry_branches: set[str] | None = None,
):
    monkeypatch.setattr(
        validator,
        "_git_stdout",
        _git(
            branch,
            ancestry_present=ancestry_present,
            ancestry_branches=ancestry_branches,
        ),
    )
    failures: list[str] = []
    receipts: list[str] = []
    validator._validate_branch(REPO_ROOT, failures, receipts)
    return tuple(failures), tuple(receipts)


def _set_pull_request_detached_env(monkeypatch, *, head_ref: str | None = None):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/159/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "159/merge")
    if head_ref is not None:
        monkeypatch.setenv("GITHUB_HEAD_REF", head_ref)


def test_pr159r_exact_branch_allowed(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, c.EXPECTED_BRANCH)

    assert failures == ()
    assert receipts == ()


def test_pr159r_pr162c_downstream_branch_allows_cumulative_validation(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, PR162C_DOWNSTREAM_BRANCH)

    assert failures == ()
    assert receipts == ()


def test_pr159r_pr162d_downstream_branch_allows_cumulative_validation(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, PR162D_DOWNSTREAM_BRANCH)

    assert failures == ()
    assert receipts == ()


def test_pr159r_pr162d_r1_downstream_branch_allows_cumulative_validation(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, PR162D_R1_DOWNSTREAM_BRANCH)

    assert failures == ()
    assert receipts == ()


def test_pr159r_pr162r_a_downstream_branch_allows_cumulative_validation(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, PR162R_A_DOWNSTREAM_BRANCH)

    assert failures == ()
    assert receipts == ()


def test_pr159r_pr162d_r2a_downstream_branch_allows_cumulative_validation(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, PR162D_R2A_DOWNSTREAM_BRANCH)

    assert failures == ()
    assert receipts == ()


def test_pr159r_detached_head_pr_context_allowed(monkeypatch):
    _set_pull_request_detached_env(monkeypatch, head_ref=c.EXPECTED_BRANCH)
    failures, receipts = _branch_outcome(monkeypatch, "DETACHED_HEAD")

    assert failures == ()
    assert receipts == (c.PR159R_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr159r_detached_head_current_repair_pr_context_allowed(monkeypatch):
    _set_pull_request_detached_env(monkeypatch, head_ref=REPAIR_BRANCH)
    failures, receipts = _branch_outcome(monkeypatch, "DETACHED_HEAD")

    assert failures == ()
    assert receipts == (c.PR159R_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr159r_detached_head_pr160_repair_pr_context_allowed(monkeypatch):
    _set_pull_request_detached_env(monkeypatch, head_ref=PR160_REPAIR_BRANCH)
    failures, receipts = _branch_outcome(monkeypatch, "DETACHED_HEAD")

    assert failures == ()
    assert receipts == (c.PR159R_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr159r_detached_head_without_head_ref_or_ancestry_fails_closed(
    monkeypatch,
):
    _set_pull_request_detached_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, "DETACHED_HEAD")

    assert failures == ("PR159R_BLOCKED_WRONG_BRANCH:DETACHED_HEAD",)
    assert receipts == ()


def test_pr159r_detached_head_unrelated_head_ref_remains_blocked(monkeypatch):
    _set_pull_request_detached_env(monkeypatch, head_ref="feature/unrelated")
    failures, receipts = _branch_outcome(
        monkeypatch,
        "DETACHED_HEAD",
        ancestry_branches={c.EXPECTED_BRANCH, REPAIR_BRANCH},
    )

    assert failures == ("PR159R_BLOCKED_WRONG_BRANCH:DETACHED_HEAD",)
    assert receipts == ()


def test_pr159r_detached_head_without_head_ref_accepts_valid_ancestry(monkeypatch):
    _set_pull_request_detached_env(monkeypatch)
    failures, receipts = _branch_outcome(
        monkeypatch,
        "DETACHED_HEAD",
        ancestry_present=True,
    )

    assert failures == ()
    assert receipts == (c.PR159R_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr159r_main_push_with_ancestry_allowed(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    failures, receipts = _branch_outcome(
        monkeypatch,
        "main",
        ancestry_present=True,
    )

    assert failures == ()
    assert receipts == (c.PR159R_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY,)


def test_pr159r_main_push_without_valid_ancestry_fails_closed(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    failures, receipts = _branch_outcome(monkeypatch, "main")

    assert failures == ("PR159R_BLOCKED_WRONG_BRANCH:main",)
    assert receipts == ()


def test_pr159r_unrelated_branch_blocked(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(
        monkeypatch,
        "feature/unrelated",
        ancestry_branches={c.EXPECTED_BRANCH, REPAIR_BRANCH},
    )

    assert failures == ("PR159R_BLOCKED_WRONG_BRANCH:feature/unrelated",)
    assert receipts == ()


def test_pr159r_unrelated_detached_head_commit_blocked(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(monkeypatch, "DETACHED_HEAD")

    assert failures == ("PR159R_BLOCKED_WRONG_BRANCH:DETACHED_HEAD",)
    assert receipts == ()


def test_pr159r_current_repair_branch_requires_ancestry(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(
        monkeypatch,
        REPAIR_BRANCH,
        ancestry_branches={REPAIR_BRANCH},
    )

    assert failures == ()
    assert receipts == ()

    failures, receipts = _branch_outcome(monkeypatch, REPAIR_BRANCH)

    assert failures == (f"PR159R_BLOCKED_WRONG_BRANCH:{REPAIR_BRANCH}",)
    assert receipts == ()


def test_pr159r_pr160_repair_branch_not_allowed_as_local_branch(monkeypatch):
    _clear_env(monkeypatch)
    failures, receipts = _branch_outcome(
        monkeypatch,
        PR160_REPAIR_BRANCH,
        ancestry_branches={c.EXPECTED_BRANCH, REPAIR_BRANCH},
    )

    assert failures == (f"PR159R_BLOCKED_WRONG_BRANCH:{PR160_REPAIR_BRANCH}",)
    assert receipts == ()
