"""Read-only input consumption audit for PR162R-A."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json


def consumption_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for ref in c.ALL_CONSUMPTION_INPUTS:
        path = repo_root / ref
        present = path.exists()
        record_count = None
        report_id = None
        if present and path.suffix == ".json":
            payload = read_json(path)
            if isinstance(payload, dict):
                record_count = payload.get("record_count") or payload.get("total_record_count")
                report_id = payload.get("report_id")
        mode = "UPSTREAM_CONTEXT_READ_ONLY"
        if ref.startswith("docs/master_plan/generated/PR162D_R1"):
            mode = "CONSUME_PR162D_R1_OUTPUT_NO_REBUILD"
        elif ref.startswith("docs/master_plan/generated/PR162D"):
            mode = "CONSUME_PR162D_OUTPUT_NO_REBUILD"
        elif ref.startswith("docs/master_plan/generated/PR162") or ref.startswith(
            "docs/master_plan/generated/PR161F"
        ):
            mode = "CONSUME_REPLAY_PAPER_CONTRACT_NO_EXECUTION"
        records.append(
            {
                "input_ref": ref,
                "present_flag": present,
                "record_count": record_count,
                "report_id": report_id,
                "consumption_mode": mode,
                "missing_input_note": None
                if present
                else "MISSING_INPUT_CONTINUE_WHEN_PR162D_PR162D_R1_FALLBACK_DATA_SUFFICIENT",
                "route_impossible_flag": False,
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
