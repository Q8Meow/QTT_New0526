"""Paper risk policy receipt construction."""

from __future__ import annotations

from .authority_policy import no_authority_fields, plain_ref


def build_risk_policy_receipt(index: int, candidate_packet_id: str, qku_ids: list[str], scenario_id: str) -> dict:
    return {
        "risk_policy_receipt_ref": plain_ref("RISK_POLICY_RECEIPT", index),
        "candidate_packet_id": candidate_packet_id,
        "qku_ids": qku_ids,
        "scenario_id": scenario_id,
        "risk_policy_ref": "PR163_PAPER_RISK_POLICY::CAPITAL_EXPOSURE_LIMITS_V1",
        "max_loss_limit": 250.0,
        "position_limit": 100000.0,
        "event_exposure_limit": 100000.0,
        "category_exposure_limit": 250000.0,
        "venue_exposure_limit": 500000.0,
        "capital_budget_limit": 10000.0,
        "risk_policy_status": "PAPER_RISK_POLICY_EVALUATED",
        "validation_status": "PASS",
        **no_authority_fields(),
    }
