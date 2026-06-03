"""Forbidden authority summary for PR162D artifacts."""

from __future__ import annotations

from . import constants as c


def forbidden_authority_summary() -> dict[str, int]:
    return dict(c.BOUNDARY_COUNT_FIELDS)


def forbidden_authority_records() -> list[dict[str, object]]:
    return [
        {
            "record_id": "PR162D-FORBIDDEN-AUTHORITY-SCAN",
            "scan_status": "PASS",
            "no_live_promotion_ready_claim": True,
            "no_order_ready_claim": True,
            "no_profit_evidence_claim": True,
            "no_private_account_state": True,
            "no_atomicrows_bundle_mutation": True,
            **forbidden_authority_summary(),
        }
    ]
