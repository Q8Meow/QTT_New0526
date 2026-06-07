"""QKU identity reconciliation against CandidatePacketV1 and PR161C inventory."""

from __future__ import annotations

from typing import Any

from .central_reason_codes import EXACT_REASON_CODES
from .deterministic_ids import plain_ref
from .market_scope_classifier import classify_market_scope
from .stage1_activation_dormancy import classify_activation


def build_identity_records(
    master_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidate_by_qku: dict[str, dict[str, Any]] = {}
    for candidate in candidate_rows:
        for qku_id in candidate.get("qku_ids") or []:
            candidate_by_qku[str(qku_id)] = candidate

    records: list[dict[str, Any]] = []
    for index, master in enumerate(sorted(master_rows, key=lambda row: row["qku_id"]), 1):
        qku_id = str(master["qku_id"])
        candidate = candidate_by_qku.get(qku_id)
        market_scope = classify_market_scope(master, candidate)
        activation_state, activation_reason = classify_activation(market_scope)
        in_current = candidate is not None
        records.append(
            {
                "qku_identity_record_ref": plain_ref("QKU_IDENTITY", index),
                "qku_id": qku_id,
                "candidate_id": str(candidate["candidate_packet_id"]) if candidate else "",
                "evidence_id": (
                    f"PR163B_PR164_HANDOFF::{int(str(candidate['candidate_packet_id']).split('::')[-1]):06d}"
                    if candidate
                    else ""
                ),
                "canonical_identity_status": (
                    "CANONICAL_CURRENT_CANDIDATE_PACKET"
                    if in_current
                    else "CANONICAL_HISTORICAL_QKU_NOT_IN_CURRENT_CANDIDATE_PACKET"
                ),
                "identity_reconciliation_reason": (
                    EXACT_REASON_CODES["CURRENT_CANDIDATE_CANONICAL"]
                    if in_current
                    else EXACT_REASON_CODES["HISTORICAL_QKU_NOT_IN_CURRENT_PACKET"]
                ),
                "qku_name": master.get("qku_name", ""),
                "qku_type": master.get("qku_type", ""),
                "qku_source_artifact_path": master.get("qku_source_artifact_path", ""),
                "historical_inventory_ref": "PR161C_QKUMasterInventoryBridge.report.json",
                "current_candidate_packet_ref": candidate.get("candidate_packet_id", "") if candidate else "",
                "market_scope": market_scope,
                "market_scope_reason": _market_scope_reason(master, market_scope),
                "activation_state": activation_state,
                "activation_reason": activation_reason,
                "primary_downstream_pr_route": (
                    "ROUTE_TO_PR165_SCORING"
                    if in_current
                    else "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR"
                ),
                "no_orphan_state": True,
                "validation_status": "PASS",
            }
        )
    return records


def _market_scope_reason(master: dict[str, Any], market_scope: str) -> str:
    return (
        f"PR161C qku_market_primary={master.get('qku_market_primary')} and "
        f"qku_type={master.get('qku_type')} classified to {market_scope}."
    )
