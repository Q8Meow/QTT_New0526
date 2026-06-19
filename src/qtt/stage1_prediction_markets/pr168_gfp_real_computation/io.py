"""File IO helpers for PR168-GFP generated reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GENERATED_DIR = Path("docs/master_plan/generated")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_report(repo_root: Path, filename: str, payload: dict[str, Any]) -> Path:
    output_path = repo_root / GENERATED_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return output_path


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()
