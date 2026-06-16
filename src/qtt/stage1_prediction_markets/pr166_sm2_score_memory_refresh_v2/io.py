"""JSON, path, branch, and shard helpers for PR166-SM2."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
from typing import Any

from tools import ci_branch_context

from . import constants as c

_ALLOWED_BRANCH_CONTEXTS = frozenset(
    {
        c.EXPECTED_BRANCH,
        c.BASE_BRANCH,
        "pr166-sf-r2-targeted-conversion-repair-retest",
        "pr166-sm3-score-memory-refresh-v3",
        "pr165-d3-quantum-aware-scenario-selection-v3",
    }
)


def json_text(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, indent=None if compact else 2, separators=separators, sort_keys=True) + "\n"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_text(payload, compact=compact), encoding="utf-8")


def normalize_repo_ref(value: str | Path) -> str:
    raw = value.as_posix() if isinstance(value, (PurePosixPath, PureWindowsPath)) else str(value)
    windows_ref = PureWindowsPath(raw)
    if windows_ref.drive or windows_ref.root:
        raise ValueError(f"repo ref must be relative: {raw}")
    normalized = raw.replace("\\", "/")
    posix_ref = PurePosixPath(normalized)
    if posix_ref.is_absolute():
        raise ValueError(f"repo ref must be relative: {raw}")
    parts = tuple(part for part in posix_ref.parts if part != ".")
    if not parts or any(part == ".." for part in parts):
        raise ValueError(f"invalid repo ref: {raw}")
    return "/".join(parts)


def resolve_repo_relative(repo_root: Path, repo_ref: str | Path) -> Path:
    return repo_root.joinpath(*normalize_repo_ref(repo_ref).split("/"))


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()
    if branch:
        return branch
    if not ci_branch_context.github_actions_active():
        return branch
    resolved = ci_branch_context.current_branch_context(
        repo_root,
        env_candidates=("GITHUB_HEAD_REF", "GITHUB_REF_NAME"),
        git_stdout=lambda _repo_root, _args: (0, "", ""),
    )
    return resolved.branch


def ensure_branch(repo_root: Path) -> None:
    branch = current_branch(repo_root)
    if branch not in _ALLOWED_BRANCH_CONTEXTS:
        allowed = ", ".join(sorted(_ALLOWED_BRANCH_CONTEXTS))
        raise RuntimeError(f"{c.PR_ID} must build on one of {allowed}, got {branch}")


def records_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("payload records must be a list")
    return list(records)


def records_from_report_payload(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_ref in payload.get("shard_files") or payload.get("shard_paths") or []:
        normalized_shard = normalize_repo_ref(shard_ref)
        shard_payload = read_json(resolve_repo_relative(repo_root, normalized_shard))
        for row in records_from_payload(shard_payload):
            annotated = dict(row)
            annotated.setdefault("input_shard_refs", [normalized_shard])
            annotated["_source_shard_ref"] = normalized_shard
            rows.append(annotated)
    return rows
