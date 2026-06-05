"""Replay/paper data-binding requirement matrix for PR162R."""

from __future__ import annotations

from typing import Any


def build_data_binding_rows(
    packets: list[dict[str, Any]],
    missing_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions_by_packet: dict[str, list[dict[str, Any]]] = {}
    for action in missing_actions:
        actions_by_packet.setdefault(str(action.get("candidate_packet_id")), []).append(action)
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        packet_id = str(packet.get("candidate_packet_id"))
        actions = actions_by_packet.get(packet_id, [])
        rows.append(
            {
                "data_binding_requirement_id": f"PR162R_DATA_BINDING::{index:05d}",
                "candidate_packet_ref": packet_id,
                "qku_id": _first_qku(packet),
                "formulation_ref": packet.get("formulation_ref"),
                "callable_ref": packet.get("callable_ref"),
                "required_inputs": list(packet.get("inputs", [])) + [
                    "historical_replay_market_data_binding",
                    "paper_current_or_simulated_market_state_binding",
                    "benchmark_latency_measurement",
                ],
                "available_inputs": [
                    "PR162D_R2A_TestVectorRegistry.synthetic_inputs",
                    "PR162D_R2A_FormulationRecordRegistry.callable_ref",
                ],
                "synthetic_test_vector_status": "SYNTHETIC_TEST_VECTOR_READY" if packet.get("test_vectors") else "DATA_BINDING_FILL_REQUIRED",
                "replay_data_binding_status": "DATA_BINDING_FILL_REQUIRED",
                "paper_data_binding_status": "DATA_BINDING_FILL_REQUIRED",
                "data_binding_status": "DATA_BINDING_FILL_REQUIRED",
                "missing_replay_inputs": ["historical_replay_market_data_binding"],
                "missing_paper_inputs": ["paper_current_or_simulated_market_state_binding"],
                "missing_latency_inputs": ["benchmark_latency_measurement"],
                "data_binding_refs": [],
                "fill_action_refs": [row["action_id"] for row in actions],
                "route_ready_treated_as_data_ready_flag": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def binding_by_packet(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("candidate_packet_ref")): row for row in rows}


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""
