import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation import paths as p


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_BRANCH = "pr163-c-pretrade-infrastructure-rejection-remediation"
MAIN_BRANCH = "main"
BRANCH_CONTEXT_ENV = (
    "CI",
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
    "GITHUB_BASE_REF",
)


def _clear_branch_context_env(monkeypatch):
    for env_name in BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def _stub_git_branch(monkeypatch, branch: str) -> None:
    def fake_run(args, cwd, check, capture_output, text):
        assert args == ["git", "branch", "--show-current"]
        assert cwd == REPO_ROOT
        assert check is True
        assert capture_output is True
        assert text is True
        return SimpleNamespace(returncode=0, stdout=branch, stderr="")

    monkeypatch.setattr(p.subprocess, "run", fake_run)


def _set_github_pull_request_env(monkeypatch, head_ref: str) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/1000/merge")
    monkeypatch.setenv("GITHUB_REF_NAME", "1000/merge")
    monkeypatch.setenv("GITHUB_HEAD_REF", head_ref)
    monkeypatch.setenv("GITHUB_BASE_REF", "main")


def _github_main_push_env() -> dict[str, str]:
    return {
        "CI": "true",
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REF_NAME": "main",
    }


def _set_github_main_push_env(monkeypatch) -> None:
    for name, value in _github_main_push_env().items():
        monkeypatch.setenv(name, value)


def _branch_error(branch: str) -> str:
    return (
        f"PR163-C build must run on {EXPECTED_BRANCH} or {MAIN_BRANCH}; "
        f"current branch is {branch}"
    )


def test_pr163_c_repeat_run_determinism():
    env = os.environ.copy()
    env.update(_github_main_push_env())
    result = subprocess.run(
        [
            sys.executable,
            "tools/build_pr163_c_pretrade_infrastructure_rejection_remediation.py",
            "--verify-idempotent",
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    assert "PR163_C_PRETRADE_INFRA_REPAIR_IDEMPOTENT" in result.stdout


def test_pr163_c_local_named_branch_passes_branch_context_check(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, EXPECTED_BRANCH)

    assert p.current_branch(REPO_ROOT) == EXPECTED_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_main_branch_passes_post_merge_branch_context_check(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, MAIN_BRANCH)

    assert p.current_branch(REPO_ROOT) == MAIN_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_ci_main_push_detached_head_passes_branch_context_check(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")
    _set_github_main_push_env(monkeypatch)

    assert p.current_branch(REPO_ROOT) == MAIN_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_ci_detached_head_uses_github_head_ref(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")
    _set_github_pull_request_env(monkeypatch, EXPECTED_BRANCH)

    assert p.current_branch(REPO_ROOT) == EXPECTED_BRANCH
    p.ensure_branch(REPO_ROOT)


def test_pr163_c_wrong_local_branch_still_fails(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "feature/not-pr163-c")

    with pytest.raises(RuntimeError) as excinfo:
        p.ensure_branch(REPO_ROOT)

    assert _branch_error("feature/not-pr163-c") in str(excinfo.value)


def test_pr163_c_wrong_ci_head_branch_still_fails(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")
    _set_github_pull_request_env(monkeypatch, "feature/not-pr163-c")

    with pytest.raises(RuntimeError) as excinfo:
        p.ensure_branch(REPO_ROOT)

    assert _branch_error("feature/not-pr163-c") in str(excinfo.value)


def test_pr163_c_empty_branch_outside_ci_still_fails(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    _stub_git_branch(monkeypatch, "")

    with pytest.raises(RuntimeError) as excinfo:
        p.ensure_branch(REPO_ROOT)

    assert _branch_error("") in str(excinfo.value)
