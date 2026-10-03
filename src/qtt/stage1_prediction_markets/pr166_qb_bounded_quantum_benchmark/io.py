"""I/O helpers for PR166-QB generated artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from . import constants as c
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _expand_report_records_v1
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _report_json_object_v1, _report_read_json_v1


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
    return _report_read_json_v1(path, family='QB')


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_text(payload, compact=compact), encoding="utf-8")


def records_from_report_payload(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    return _expand_report_records_v1(repo_root, payload, read_json)


def ensure_branch(repo_root: Path) -> None:
    branch = _current_branch(repo_root)
    if branch in {c.EXPECTED_BRANCH, c.BASE_BRANCH}:
        return
    ci_branch = _ci_branch_context(repo_root)
    if ci_branch in {c.EXPECTED_BRANCH, c.BASE_BRANCH, ""}:
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
