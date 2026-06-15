"""I/O helpers for PR166-SM3 artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from . import constants as c


def resolve_repo_relative(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def normalize_repo_ref(value: str | Path) -> str:
    return str(value).replace("\\", "/")


def json_text(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, indent=None if compact else 2, sort_keys=True, separators=separators) + "\n"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_text(payload, compact=compact), encoding="utf-8")


def records_from_report_payload(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(payload.get("records") or [])
    for shard_ref in payload.get("shard_files") or payload.get("shard_paths") or []:
        shard_path = resolve_repo_relative(repo_root, shard_ref)
        if shard_path.exists():
            shard_payload = read_json(shard_path)
            rows.extend(shard_payload.get("records") or [])
    return rows


def ensure_branch(repo_root: Path) -> None:
    branch = _current_branch(repo_root)
    downstream_validation_branches = {"pr165-d3-quantum-aware-scenario-selection-v3"}
    if branch in {c.EXPECTED_BRANCH, c.BASE_BRANCH, *downstream_validation_branches}:
        return
    ci_branch = _ci_branch_context(repo_root)
    if ci_branch in {c.EXPECTED_BRANCH, c.BASE_BRANCH, *downstream_validation_branches, ""}:
        return
    raise RuntimeError(
        f"{c.PR_ID} builder must run on {c.EXPECTED_BRANCH} or {c.BASE_BRANCH}; "
        f"current branch context is {branch or ci_branch or 'UNKNOWN'}"
    )


def _current_branch(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _ci_branch_context(repo_root: Path) -> str:
    try:
        from tools.ci_branch_context import current_branch_context
    except Exception:
        return ""
    try:
        return current_branch_context(repo_root).branch
    except Exception:
        return ""
