#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath


def normalize_repo_ref(value: str | Path, *, require_non_empty: bool = True) -> str:
    """Normalize a serialized repo-relative ref to POSIX form."""

    raw = value.as_posix() if isinstance(value, Path) else str(value)
    windows_ref = PureWindowsPath(raw)
    if windows_ref.drive or windows_ref.root:
        raise ValueError(f"repo ref must be relative: {raw}")

    normalized = raw.replace("\\", "/")
    posix_ref = PurePosixPath(normalized)
    if posix_ref.is_absolute():
        raise ValueError(f"repo ref must be relative: {raw}")

    parts = tuple(part for part in posix_ref.parts if part not in {"", "."})
    if require_non_empty and not parts:
        raise ValueError("repo ref must not be empty")
    if any(part == ".." for part in parts):
        raise ValueError(f"repo ref must not contain '..': {raw}")
    return "/".join(parts)


def resolve_repo_ref(repo_root: str | Path, repo_ref: str | Path) -> Path:
    normalized = normalize_repo_ref(repo_ref)
    root = Path(repo_root).resolve()
    candidate = root.joinpath(*normalized.split("/")).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"repo ref escapes repo root: {repo_ref}") from exc
    return candidate


def to_repo_posix(path: str | Path, repo_root: str | Path) -> str:
    root = Path(repo_root).resolve()
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError(f"path is outside repo root: {path}") from exc
    return normalize_repo_ref(candidate)
