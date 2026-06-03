"""Convert PR162C required-field blockers into PR162D candidate targets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .candidate_status_model import progress_status_for_index
from .deterministic_id import deterministic_id
from .preflight_reader import load_report_records


def pr162c_ledger_records(repo_root: Path) -> list[dict[str, Any]]:
    return load_report_records(
        repo_root,
        "docs/master_plan/generated/PR162C_DataRequirementClassificationLedger.report.json",
    )


def reinterpret_pr162c_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        qku_id = str(record.get("qku_id") or f"UNKNOWN-QKU-{index + 1:05d}")
        progress_status = progress_status_for_index(index)
        output.append(
            {
                "reinterpretation_id": deterministic_id(
                    "PR162D-REINTERPRETATION", qku_id, record.get("handoff_id"), size=10
                ),
                "source_pr162c_classification_id": record.get("classification_id"),
                "source_pr162c_handoff_id": record.get("handoff_id"),
                "qku_id": qku_id,
                "source_pr162c_state_label": c.REINTERPRETED_REQUIRED_FIELD_TARGET_LABEL,
                "pr162d_progress_status": progress_status,
                "candidate_materialization_target_flag": True,
                "candidate_field_fill_progress_flag": True,
                "acquisition_blocker_flag": False,
                "generic_required_fields_blocker_remaining_flag": False,
                "partial_materialization_allowed_flag": True,
                "non_official_source_allowed_flag": True,
                "replay_paper_candidate_flag": True,
                "live_order_authority": False,
                "agent_route_required_flag": True,
                "created_by_pr": c.PR_ID,
            }
        )
    return output
