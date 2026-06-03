"""Path helpers for PR162D."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath


def normalize_repo_relative_ref(path: str | Path) -> str:
    normalized = str(path).replace("\\", "/")
    return normalized[2:] if normalized.startswith("./") else normalized


def resolve_repo_relative(repo_root: Path, ref: str | Path) -> Path:
    normalized = normalize_repo_relative_ref(ref)
    if PureWindowsPath(normalized).drive or Path(normalized).is_absolute():
        raise ValueError(f"absolute paths are not accepted in PR162D artifacts: {ref}")
    return repo_root / normalized
