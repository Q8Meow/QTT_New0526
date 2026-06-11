from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import io as pr165_d2_io

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_builder_verify_idempotent():
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "tools/build_pr165_d2_score_refreshed_scenario_selection_v2.py",
            "--verify-idempotent",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PR165_D2_SCORE_REFRESHED_SELECTION_IDEMPOTENT" in result.stdout


def test_branch_guard_accepts_ci_detached_head_ref(monkeypatch):
    class Result:
        stdout = ""

    monkeypatch.setenv("GITHUB_HEAD_REF", c.EXPECTED_BRANCH)
    monkeypatch.setattr(pr165_d2_io.subprocess, "run", lambda *args, **kwargs: Result())

    assert pr165_d2_io.current_branch(REPO_ROOT) == c.EXPECTED_BRANCH
    pr165_d2_io.ensure_branch(REPO_ROOT)


def test_branch_guard_rejects_wrong_ci_detached_head_ref(monkeypatch):
    class Result:
        stdout = ""

    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/not-pr165-d2")
    monkeypatch.setattr(pr165_d2_io.subprocess, "run", lambda *args, **kwargs: Result())

    with pytest.raises(RuntimeError, match=c.EXPECTED_BRANCH):
        pr165_d2_io.ensure_branch(REPO_ROOT)
