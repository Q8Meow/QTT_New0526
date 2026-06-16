from __future__ import annotations

from pathlib import Path
from typing import Sequence

from tools import validate_repair_pr_changed_file_scope as validator


def test_changed_files_from_git_prefers_worktree_status(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_git(
        repo_root: Path,
        args: Sequence[str],
    ) -> tuple[int, str, str]:
        calls.append(tuple(args))
        if tuple(args) == ("status", "--porcelain", "--untracked-files=all"):
            return (
                0,
                "\n".join(
                    (
                        " M tools/ci_branch_context.py",
                        "M tests/tools/test_validate_repair_pr_changed_file_scope.py",
                        "?? src/qtt/stage1_prediction_markets/bounded_idempotence.py",
                        "R  old_name.py -> tests/tools/test_ci_branch_context.py",
                    )
                ),
                "",
            )
        raise AssertionError(f"unexpected fallback diff query: {tuple(args)!r}")

    monkeypatch.setattr(validator, "_git", fake_git)

    assert validator._changed_files_from_git(Path(".")) == (
        "src/qtt/stage1_prediction_markets/bounded_idempotence.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validate_repair_pr_changed_file_scope.py",
        "tools/ci_branch_context.py",
    )
    assert calls == [("status", "--porcelain", "--untracked-files=all")]


def test_changed_files_from_git_falls_back_to_committed_diff(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_git(
        repo_root: Path,
        args: Sequence[str],
    ) -> tuple[int, str, str]:
        calls.append(tuple(args))
        if tuple(args) == ("status", "--porcelain", "--untracked-files=all"):
            return 0, "", ""
        if tuple(args) == ("diff", "--name-only", "HEAD^1", "HEAD"):
            return 0, "tools/ci_branch_context.py\n", ""
        raise AssertionError(f"unexpected diff query: {tuple(args)!r}")

    monkeypatch.setattr(validator, "_git", fake_git)

    assert validator._changed_files_from_git(Path(".")) == (
        "tools/ci_branch_context.py",
    )
    assert calls == [
        ("status", "--porcelain", "--untracked-files=all"),
        ("diff", "--name-only", "HEAD^1", "HEAD"),
    ]
