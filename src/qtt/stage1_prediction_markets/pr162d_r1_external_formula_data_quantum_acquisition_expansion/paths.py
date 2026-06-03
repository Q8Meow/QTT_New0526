"""Path helpers for PR162D-R1."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def resolve_repo_relative(repo_root: Path, ref: str) -> Path:
    if "\\" in ref or PureWindowsPath(ref).drive:
        raise ValueError(f"non-portable repository reference: {ref}")
    return repo_root / ref
