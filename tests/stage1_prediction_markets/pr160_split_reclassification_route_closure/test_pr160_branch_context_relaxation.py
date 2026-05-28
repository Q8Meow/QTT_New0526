from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import (
    validator,
)


BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)
REPO_ROOT = Path(__file__).resolve().parents[3]
PR160_REPAIR_BRANCH = "repair/pr160-main-push-branch-context-relaxation"
PR159R_BRANCH_CONTEXT_REPAIR_BRANCH = "repair/pr159r-detached-head-branch-context"


def _clear_branch_context_env(monkeypatch):
    for env_name in BRANCH_CONTEXT_ENV:
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


def _git_responses(
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
            return 0, branch, ""
        if command[:2] == ("merge-base", "--is-ancestor"):
            ancestor_branch = _branch_from_ref(command[2], branches)
            return (0, "", "") if ancestor_branch else (1, "", "not ancestor")
        if command[:3] == ("log", "--format=%s", "--fixed-strings"):
            grep = command[3].removeprefix("--grep=/")
            if grep in branches:
                return (
                    0,
                    f"Merge pull request #172 from Q8Meow/{grep}\n",
                    "",
                )
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    return fake_git_stdout


def _branch_outcome(
    monkeypatch,
    branch: str,
    *,
    ancestry_present: bool = False,
    ancestry_branches: set[str] | None = None,
):
    failures: list[str] = []
    receipts: list[str] = []
    monkeypatch.setattr(
        validator,
        "_git_stdout",
        _git_responses(
            branch,
            ancestry_present=ancestry_present,
            ancestry_branches=ancestry_branches,
        ),
    )
    validator._validate_branch(REPO_ROOT, failures, receipts)
    return tuple(failures), tuple(receipts)


def test_pr160_exact_branch_allows_without_ci_receipt(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    failures, receipts = _branch_outcome(
        monkeypatch,
        c.EXPECTED_BRANCH,
        ancestry_present=False,
    )

    assert failures == ()
    assert receipts == ()


def test_pr160_detached_head_ci_with_valid_branch_context_emits_relaxation_receipt(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/172/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "172/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", c.EXPECTED_BRANCH)

    failures, receipts = _branch_outcome(
        monkeypatch,
        "HEAD",
        ancestry_present=False,
    )

    assert failures == ()
    assert receipts == (c.PR160_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr160_detached_head_ci_with_repair_head_ref_emits_branch_only_relaxation_receipt(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/172/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "172/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", PR160_REPAIR_BRANCH)

    failures, receipts = _branch_outcome(
        monkeypatch,
        "HEAD",
        ancestry_present=False,
    )

    assert failures == ()
    assert receipts == (c.PR160_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr160_detached_head_ci_with_pr159r_repair_head_ref_emits_branch_only_relaxation_receipt(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/172/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "172/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", PR159R_BRANCH_CONTEXT_REPAIR_BRANCH)

    failures, receipts = _branch_outcome(
        monkeypatch,
        "HEAD",
        ancestry_present=False,
    )

    assert failures == ()
    assert receipts == (c.PR160_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr160_detached_head_ci_pr159r_repair_ref_name_without_head_ref_remains_blocked(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/172/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", PR159R_BRANCH_CONTEXT_REPAIR_BRANCH)

    failures, receipts = _branch_outcome(
        monkeypatch,
        "HEAD",
        ancestry_present=False,
    )

    assert failures == ("PR160_BLOCKED_WRONG_BRANCH:DETACHED_HEAD",)
    assert receipts == ()


def test_pr160_detached_head_ci_without_head_ref_or_ancestry_fails_closed(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/172/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "172/merge")

    failures, receipts = _branch_outcome(
        monkeypatch,
        "HEAD",
    )

    assert failures == ("PR160_BLOCKED_WRONG_BRANCH:DETACHED_HEAD",)
    assert receipts == ()


def test_pr160_detached_head_ci_unrelated_head_ref_remains_blocked(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/172/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "172/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/unrelated")

    failures, receipts = _branch_outcome(
        monkeypatch,
        "HEAD",
        ancestry_branches={
            c.EXPECTED_BRANCH,
            PR160_REPAIR_BRANCH,
            PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        },
    )

    assert failures == ("PR160_BLOCKED_WRONG_BRANCH:DETACHED_HEAD",)
    assert receipts == ()


def test_pr160_detached_head_ci_without_head_ref_accepts_valid_repair_ancestry(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/172/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "172/merge")

    failures, receipts = _branch_outcome(
        monkeypatch,
        "HEAD",
        ancestry_branches={PR160_REPAIR_BRANCH},
    )

    assert failures == ()
    assert receipts == (c.PR160_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,)


def test_pr160_main_push_with_valid_ancestry_emits_relaxation_receipt(monkeypatch):
    _clear_branch_context_env(monkeypatch)
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
    assert receipts == (c.PR160_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY,)


def test_pr160_main_push_without_valid_ancestry_fails_closed(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")

    failures, receipts = _branch_outcome(
        monkeypatch,
        "main",
        ancestry_present=False,
    )

    assert failures == ("PR160_BLOCKED_WRONG_BRANCH:main",)
    assert receipts == ()


def test_pr160_unrelated_branch_remains_blocked_even_with_pr160_ancestry(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    failures, receipts = _branch_outcome(
        monkeypatch,
        "feature/unrelated",
        ancestry_branches={
            c.EXPECTED_BRANCH,
            PR160_REPAIR_BRANCH,
            PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        },
    )

    assert failures == ("PR160_BLOCKED_WRONG_BRANCH:feature/unrelated",)
    assert receipts == ()


def test_pr160_unrelated_repair_branch_remains_blocked_even_with_pr160_ancestry(
    monkeypatch,
):
    _clear_branch_context_env(monkeypatch)

    failures, receipts = _branch_outcome(
        monkeypatch,
        "repair/pr161-unrelated-future-branch",
        ancestry_branches={
            c.EXPECTED_BRANCH,
            PR160_REPAIR_BRANCH,
            PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        },
    )

    assert failures == ("PR160_BLOCKED_WRONG_BRANCH:repair/pr161-unrelated-future-branch",)
    assert receipts == ()


def test_pr160_same_pr_repair_branch_requires_ancestry(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    failures, receipts = _branch_outcome(
        monkeypatch,
        PR160_REPAIR_BRANCH,
        ancestry_branches={PR160_REPAIR_BRANCH},
    )

    assert failures == ()
    assert receipts == ()

    failures, receipts = _branch_outcome(
        monkeypatch,
        PR160_REPAIR_BRANCH,
    )

    assert failures == (
        "PR160_BLOCKED_WRONG_BRANCH:repair/pr160-main-push-branch-context-relaxation",
    )
    assert receipts == ()


def test_pr160_pr159r_repair_branch_remains_blocked_as_current_branch(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    failures, receipts = _branch_outcome(
        monkeypatch,
        PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
        ancestry_branches={PR159R_BRANCH_CONTEXT_REPAIR_BRANCH},
    )

    assert failures == (
        f"PR160_BLOCKED_WRONG_BRANCH:{PR159R_BRANCH_CONTEXT_REPAIR_BRANCH}",
    )
    assert receipts == ()
