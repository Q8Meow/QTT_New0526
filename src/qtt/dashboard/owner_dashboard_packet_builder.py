"""Packet and queue builders derived from the owner surface registry."""

from __future__ import annotations

from typing import Any

from .owner_surface_models import AUTHORITY_BOUNDARY_REF, projection_trace


SEVERITY_ORDER = {"S4_CRITICAL": 0, "S3_HIGH": 1, "S2_REVIEW": 2, "S1_NOTICE": 3, "S0_INFO": 4}


def severity_for_row(row: dict[str, Any]) -> str:
    label = f"{row.get('canonical_label', '')} {row.get('panel_id', '')}".upper()
    if "KILL" in label or "LIVE" in label or "LAUNCH" in label:
        return "S4_CRITICAL"
    if "RISK" in label or "SOURCE" in label or "QKU" in label or "QUANTUM" in label:
        return "S3_HIGH"
    if "REPLAY" in label or "PAPER" in label or "RESEARCH" in label:
        return "S2_REVIEW"
    if "ACK" in label:
        return "S1_NOTICE"
    return "S0_INFO"


def build_owner_dashboard_packet(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_id = "OWNER_DASHBOARD_PACKET_V1"
    return [
        {
            **projection_trace(feature_id),
            "packet_id": "OwnerDashboardPacketV1",
            "packet_version": "v1",
            "fixed_order_layers": [
                "OWNER_HEADER_STRIP",
                "OWNER_DECISION_QUEUE",
                "OWNER_ACTIONABLE_CARDS",
                "OWNER_PANEL_PROJECTIONS",
                "OWNER_AUDIT_FOOTER",
            ],
            "surface_registry_row_count": len(registry_rows),
            "decision_queue_ref": "owner_decision_queue.generated.jsonl",
            "action_registry_ref": "owner_action_registry.generated.jsonl",
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        }
    ]


def build_header_strip(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feature_id = "OWNER_HEADER_STRIP_V1"
    severities = [severity_for_row(row) for row in registry_rows]
    return [
        {
            **projection_trace(feature_id),
            "header_id": "OwnerHeaderStripV1",
            "packet_id": "OwnerDashboardPacketV1",
            "timestamp_policy": "provider_snapshot_timestamp_required",
            "timezone_policy": "owner_timezone_display_required",
            "live_mode_status_policy": "display_only_no_order_authority",
            "capital_state_policy": "snapshot_ref_only_no_private_read",
            "awaiting_decision_count_ref": "owner_decision_queue.generated.jsonl",
            "highest_severity": sorted(severities, key=SEVERITY_ORDER.get)[0],
            "latest_change_or_proposal_ref": "owner_audit_trail_seed.generated.jsonl",
            "last_owner_action_timestamp_ref": "owner_action_receipt_template.generated.jsonl",
        }
    ]


def build_decision_queue(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(registry_rows):
        feature_id = str(row["feature_id"])
        severity = severity_for_row(row)
        gate_priority = 0 if "EXECUTION" in feature_id or "LIVE" in feature_id else 1
        rows.append(
            {
                **projection_trace(feature_id),
                "queue_item_id": f"DASH1_QUEUE_{index + 1:04d}",
                "feature_id": feature_id,
                "panel_id": row["panel_id"],
                "severity_badge": severity,
                "severity_rank": SEVERITY_ORDER[severity],
                "gate_priority": gate_priority,
                "unresolved_order": index + 1,
                "owner_action_code_refs": row.get("action_code_refs", []),
                "canonical_packet_ref": "OwnerDashboardPacketV1",
                "evidence_refs": row.get("upstream_artifact_refs", []),
                "no_actionable_card_outside_decision_queue": True,
                "acknowledgment_is_not_live_approval": True,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            int(item["severity_rank"]),
            int(item["gate_priority"]),
            int(item["unresolved_order"]),
        ),
    )


def build_actionable_cards(registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for index, row in enumerate(registry_rows):
        if not row.get("action_code_refs"):
            continue
        feature_id = str(row["feature_id"])
        cards.append(
            {
                **projection_trace(feature_id),
                "card_id": f"DASH1_CARD_{index + 1:04d}",
                "feature_id": feature_id,
                "card_type": row["card_type"],
                "underlying_action_code": row["action_code_refs"][0],
                "owner_action_code_refs": row["action_code_refs"],
                "canonical_packet_ref": "OwnerDashboardPacketV1",
                "evidence_refs": row.get("upstream_artifact_refs", []),
                "decision_queue_ref": "owner_decision_queue.generated.jsonl",
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            }
        )
    return cards
