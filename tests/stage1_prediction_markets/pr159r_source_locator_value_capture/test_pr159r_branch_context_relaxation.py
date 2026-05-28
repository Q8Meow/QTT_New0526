from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c
from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import validator


REPO_ROOT = Path(__file__).resolve().parents[3]
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


def _git(branch: str, *, ancestry: bool = False):
    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            if branch == "DETACHED_HEAD":
                return 1, "", "detached"
            return 0, branch, ""
        if command[:2] == ("merge-base", "--is-ancestor"):
            return (0, "", "") if ancestry else (1, "", "not ancestor")
        if command[:3] == ("log", "--format=%s", "--fixed-strings"):
            return (
                0,
                f"Merge pull request #1 from Owner/{c.EXPECTED_BRANCH}\n" if ancestry else "",
                "",
            )
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return 0, branch, ""
        raise AssertionError(f"unexpected git command: {command!r}")

    return fake_git_stdout


def test_pr159r_exact_branch_allowed(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setattr(validator, "_git_stdout", _git(c.EXPECTED_BRANCH))
    failures: list[str] = []
    receipts: list[str] = []
    validator._validate_branch(REPO_ROOT, failures, receipts)
    assert failures == []
    assert receipts == []


def test_pr159r_detached_head_pr_context_allowed(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_HEAD_REF", c.EXPECTED_BRANCH)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/159/merge")
    monkeypatch.setattr(validator, "_git_stdout", _git("DETACHED_HEAD"))
    failures: list[str] = []
    receipts: list[str] = []
    validator._validate_branch(REPO_ROOT, failures, receipts)
    assert failures == []
    assert receipts == [c.PR159R_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY]


def test_pr159r_main_push_with_ancestry_allowed(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setattr(validator, "_git_stdout", _git("main", ancestry=True))
    failures: list[str] = []
    receipts: list[str] = []
    validator._validate_branch(REPO_ROOT, failures, receipts)
    assert failures == []
    assert receipts == [c.PR159R_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY]


def test_pr159r_unrelated_branch_blocked(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setattr(validator, "_git_stdout", _git("feature/unrelated", ancestry=True))
    failures: list[str] = []
    receipts: list[str] = []
    validator._validate_branch(REPO_ROOT, failures, receipts)
    assert failures == ["PR159R_BLOCKED_WRONG_BRANCH:feature/unrelated"]
    assert receipts == []
