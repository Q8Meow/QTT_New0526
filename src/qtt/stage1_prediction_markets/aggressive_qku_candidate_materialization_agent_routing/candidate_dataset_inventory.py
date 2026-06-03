"""Candidate dataset inventory expansion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .deterministic_id import deterministic_id
from .preflight_reader import load_report_records


def candidate_dataset_records(repo_root: Path) -> list[dict[str, Any]]:
    base = load_report_records(repo_root, "docs/master_plan/generated/PR162C_NormalizedDatasetInventory.report.json")
    records = []
    for index, record in enumerate(base, start=1):
        records.append(
            {
                "dataset_candidate_id": deterministic_id(
                    "PR162D-DATASET-CANDIDATE", record.get("record_id"), index
                ),
                "source_dataset_ref": record.get("dataset_id"),
                "source_record_ref": record.get("record_id"),
                "venue_scope": record.get("venue_scope"),
                "provided_required_fields": record.get("provided_required_fields") or [],
                "candidate_missing_value_fields": record.get("missing_value_flags") or [],
                "candidate_field_fill_expansion_flag": True,
                "replay_paper_candidate_flag": True,
                "agent_route_refs": ["QKU_DATA_ACQUISITION_AGENT", "REPLAY_PAPER_CANDIDATE_ROUTER"],
                "live_order_authority": False,
            }
        )
    return records
