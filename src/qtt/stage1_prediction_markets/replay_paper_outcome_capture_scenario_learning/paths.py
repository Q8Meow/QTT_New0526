"""Path normalization and traversal protections for PR161E shards."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


def repo_relative_posix(repo_root: Path, path: Path) -> str:
    root = repo_root.resolve(strict=False)
    candidate = path.resolve(strict=False)
    return candidate.relative_to(root).as_posix()


def normalize_shard_ref(repo_root: Path, shard_ref: Any) -> str:
    raw_path = str(shard_ref)
    normalized = raw_path.replace("\\", "/")
    windows_path = PureWindowsPath(normalized)
    posix_path = PurePosixPath(normalized)
    if normalized.startswith("//") or normalized.startswith("\\\\"):
        raise ValueError(f"PR161E shard path must not be UNC: {raw_path}")
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ValueError(f"PR161E shard path must be relative: {raw_path}")
    if any(part == ".." for part in posix_path.parts):
        raise ValueError(f"PR161E shard path must not contain '..': {raw_path}")
    candidate = repo_root.joinpath(*posix_path.parts)
    resolved_root = repo_root.resolve(strict=False)
    try:
        candidate.resolve(strict=False).relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"PR161E shard path escapes repo root: {raw_path}") from exc
    return posix_path.as_posix()


def resolve_repo_relative(repo_root: Path, relative_ref: Any) -> Path:
    normalized = normalize_shard_ref(repo_root, relative_ref)
    return repo_root.joinpath(*PurePosixPath(normalized).parts)
