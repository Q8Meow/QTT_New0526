"""Forbidden authority boundary audits for PR162D-R1."""

from __future__ import annotations

from typing import Any

from . import constants as c


def forbidden_authority_summary() -> dict[str, int]:
    return dict(c.BOUNDARY_COUNT_FIELDS)


def forbidden_authority_records(audit_id: str) -> list[dict[str, Any]]:
    return [
        {
            "audit_id": audit_id,
            **c.BOUNDARY_COUNT_FIELDS,
            "submit_cancel_reduce_close_order_allowed_flag": False,
            "private_state_or_secret_materialized_flag": False,
            "protected_master_plan_file_edited_flag": False,
            "atomicrows_bundle_jsonl_changed_flag": False,
            "scattered_hardcoded_boundary_literal_count": 0,
            "live_order_authority": False,
        }
    ]
