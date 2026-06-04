"""Forbidden authority audit records."""

from __future__ import annotations

from typing import Any

from . import constants as c


def forbidden_authority_summary() -> dict[str, int]:
    return dict(c.BOUNDARY_COUNT_FIELDS)


def forbidden_authority_records(audit_id: str) -> list[dict[str, Any]]:
    return [
        {
            "audit_id": audit_id,
            "replay_execution_count": 0,
            "paper_execution_count": 0,
            "result_packet_created_count": 0,
            "live_order_authority_count": 0,
            "order_ready_count": 0,
            "live_promotion_ready_count": 0,
            "profit_evidence_count": 0,
            "private_state_fetch_count": 0,
            "qtt_sha_freeze_checksum_authority_count": 0,
            "atomicrows_bundle_mutation_count": 0,
            "quantum_advantage_claim_count": 0,
            "validation_status": "PASS",
            "live_order_authority": False,
        }
    ]
