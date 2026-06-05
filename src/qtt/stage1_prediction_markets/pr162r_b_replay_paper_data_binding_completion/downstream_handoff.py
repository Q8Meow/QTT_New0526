"""Downstream handoff update builders."""

from __future__ import annotations

from typing import Any


def build_handoff_update_rows(row_resolution: list[dict[str, Any]], target_pr: str, family: str) -> list[dict[str, Any]]:
    rows = []
    for row in row_resolution:
        rows.append(
            {
                "handoff_update_id": f"PR162R_B_{target_pr}_HANDOFF_UPDATE::{len(rows) + 1:05d}",
                "target_pr": target_pr,
                "handoff_family": family,
                "candidate_packet_id": row["candidate_packet_id"],
                "binding_task_refs": row["binding_task_refs"],
                "replay_binding_refs": row["replay_binding_refs"],
                "paper_binding_refs": row["paper_binding_refs"],
                "quantum_binding_refs": row["quantum_binding_refs"],
                "source_candidate_refs": row["source_candidate_refs"],
                "normalization_receipt_refs": row["normalization_receipt_refs"],
                "status": "BINDING_MATERIALIZED",
                "result_packet_created_count": 0,
                "profit_evidence_count": 0,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_pr162e_plugin_update_rows(row_resolution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in row_resolution:
        rows.append(
            {
                "plugin_binding_compatibility_update_id": f"PR162R_B_PR162E_PLUGIN_UPDATE::{len(rows) + 1:05d}",
                "target_pr": "PR162E",
                "candidate_packet_id": row["candidate_packet_id"],
                "formulation_ref": row["formulation_ref"],
                "callable_ref": row["callable_ref"],
                "binding_task_refs": row["binding_task_refs"],
                "plugin_intake_recommendation": "BINDING_PACKET_COMPATIBLE_FOR_NONLIVE_PLUGIN_INTAKE",
                "runtime_allowlist_candidate_stage": "NONLIVE_REPLAY_PAPER_BINDING_ONLY",
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows
