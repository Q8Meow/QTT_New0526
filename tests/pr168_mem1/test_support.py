from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.qtt.memory.pr168_mem1.models import AUTHORITY_FALSE_FIELDS, JSONL_OUTPUTS


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_mem1"


def read_jsonl(name: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (ARTIFACT_DIR / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_json(name: str) -> dict[str, Any]:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def all_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in JSONL_OUTPUTS:
        rows.extend(read_jsonl(name))
    return rows


def assert_no_authority(row: dict[str, Any]) -> None:
    for field in AUTHORITY_FALSE_FIELDS:
        assert row.get(field) is False, (row.get("row_id"), field, row.get(field))
