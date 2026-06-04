"""Path and branch helpers for PR162R-A."""

from __future__ import annotations

from pathlib import Path
import subprocess


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
