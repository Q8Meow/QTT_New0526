"""PR162D consumption audit for PR162D-R1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json


def current_branch(repo_root: Path) -> str:
    import subprocess

    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def pr162d_consumption_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for ref in (*c.PR162D_REQUIRED_INPUTS, *c.UPSTREAM_CONTEXT_INPUTS):
        path = repo_root / ref
        present = path.exists()
        record_count = None
        if present and path.suffix == ".json":
            payload = read_json(path)
            if isinstance(payload, dict):
                record_count = payload.get("record_count") or payload.get("total_record_count")
        records.append(
            {
                "input_ref": ref,
                "present_flag": present,
                "record_count": record_count,
                "consumption_mode": "CONSUME_EXISTING_OUTPUT_NO_REBUILD" if ref.startswith("docs/master_plan/generated/PR162D") else "UPSTREAM_CONTEXT_READ_ONLY",
                "missing_input_note": None if present else "MISSING_INPUT_CONTINUE_WHEN_PR162D_ROUTE_FALLBACK_AVAILABLE",
                "live_order_authority": False,
            }
        )
    return records


def missing_input_notes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "input_ref": record["input_ref"],
            "missing_input_status": record["missing_input_note"],
            "route_impossible_flag": False,
        }
        for record in records
        if not record["present_flag"]
    ]
