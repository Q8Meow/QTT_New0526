"""Source risk quarantine ledger."""

from __future__ import annotations

from typing import Any


def source_risk_quarantine_records() -> list[dict[str, Any]]:
    return [
        {
            "quarantine_audit_id": "PR162D_R1_SOURCE_RISK_QUARANTINE_AUDIT",
            "quarantined_unsafe_private_illegal_unmappable_material_count": 0,
            "credential_or_private_account_dependent_source_count": 0,
            "malware_or_executable_unknown_repo_count": 0,
            "duplicate_low_value_garbage_count": 0,
            "live_order_authority": False,
        }
    ]
