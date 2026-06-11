from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tools import build_pr165_d2_score_refreshed_scenario_selection_v2 as pr165_d2_builder
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import io as pr165_d2_io

REPO_ROOT = Path(__file__).resolve().parents[3]


class _BranchResult:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


def _clear_branch_env(monkeypatch):
    for env_name in ("GITHUB_ACTIONS", "GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        monkeypatch.delenv(env_name, raising=False)


def _stub_git_branch(monkeypatch, stdout: str) -> None:
    monkeypatch.setattr(
        pr165_d2_io.subprocess,
        "run",
        lambda *args, **kwargs: _BranchResult(stdout),
    )


def test_builder_verify_idempotent(monkeypatch, capsys):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", c.BASE_BRANCH)
    _stub_git_branch(monkeypatch, "")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            c.BUILDER_REF,
            "--repo-root",
            str(REPO_ROOT),
            "--verify-idempotent",
        ],
    )

    assert pr165_d2_builder.main() == 0
    assert "PR165_D2_SCORE_REFRESHED_SELECTION_IDEMPOTENT" in capsys.readouterr().out


def test_branch_guard_accepts_local_expected_branch(monkeypatch):
    _clear_branch_env(monkeypatch)
    _stub_git_branch(monkeypatch, c.EXPECTED_BRANCH)

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.EXPECTED_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_accepts_local_main_post_merge_context(monkeypatch):
    _clear_branch_env(monkeypatch)
    _stub_git_branch(monkeypatch, c.BASE_BRANCH)

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.BASE_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_rejects_local_wrong_branch(monkeypatch):
    _clear_branch_env(monkeypatch)
    _stub_git_branch(monkeypatch, "feature/not-pr165-d2")

    with pytest.raises(RuntimeError, match=c.EXPECTED_BRANCH):
        pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_rejects_local_empty_branch_without_github_actions(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_HEAD_REF", c.EXPECTED_BRANCH)
    _stub_git_branch(monkeypatch, "")

    assert pr165_d2_io.current_branch(REPO_ROOT) == ""
    with pytest.raises(RuntimeError, match=c.EXPECTED_BRANCH):
        pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_accepts_ci_detached_head_ref(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", c.EXPECTED_BRANCH)
    monkeypatch.setenv("GITHUB_REF_NAME", "refs-pull-fallback-not-used")
    _stub_git_branch(monkeypatch, "")

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.EXPECTED_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_accepts_ci_detached_main_ref_name(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REF_NAME", c.BASE_BRANCH)
    _stub_git_branch(monkeypatch, "")

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.BASE_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_rejects_wrong_ci_detached_branch_context(monkeypatch):
    _clear_branch_env(monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/not-pr165-d2")
    monkeypatch.setenv("GITHUB_REF_NAME", "release/not-pr165-d2")
    _stub_git_branch(monkeypatch, "")

    with pytest.raises(RuntimeError, match=c.EXPECTED_BRANCH):
        pr165_d2_io.ensure_branch(REPO_ROOT)
