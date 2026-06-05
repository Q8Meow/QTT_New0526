"""QKU-agent replay/paper handoff matrix for PR162R."""

from __future__ import annotations

from typing import Any


def build_agent_handoff_rows(
    packets: list[dict[str, Any]],
    replay_inputs: list[dict[str, Any]],
    paper_inputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    replay_by_packet = {row["candidate_packet_ref"]: row for row in replay_inputs}
    paper_by_packet = {row["candidate_packet_ref"]: row for row in paper_inputs}
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        packet_id = str(packet.get("candidate_packet_id"))
        is_quantum = packet.get("candidate_type") == "QUANTUM_FORMULATION"
        downstream = [
            "QKU Compute Engine",
            "Formula/Algorithm Runtime candidate lane",
            "Replay/Paper Candidate Router",
            "PR163 paper adapter handoff seed",
            "PR164 review/provenance handoff seed",
            "PR165 scoring/ranking handoff seed",
            "PR162E plugin compatibility seed",
            "PR162D-R2 materialization expansion queue",
            "Execution Router boundary only after later gates and explicit owner approval",
        ]
        if is_quantum:
            downstream.extend(["Quantum Advisory / Quantum Mapping Agent", "Risk Manager", "Capital Allocation"])
        rows.append(
            {
                "handoff_id": f"PR162R_QKU_AGENT_HANDOFF::{index:05d}",
                "candidate_packet_ref": packet_id,
                "qku_id": _first_qku(packet),
                "qku_ids": list(packet.get("qku_ids", [])),
                "formulation_ref": packet.get("formulation_ref"),
                "callable_ref": packet.get("callable_ref"),
                "upstream_refs": [
                    "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json",
                    "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json",
                    "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json",
                    "docs/master_plan/generated/PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json",
                    "docs/master_plan/generated/PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json",
                    "docs/master_plan/generated/PR162R_A_PR162RAdapterRerunInputPack.report.json",
                ],
                "agent_refs": list(packet.get("downstream_agent_refs", [])),
                "downstream_refs": downstream,
                "replay_adapter_input_ref": replay_by_packet[packet_id]["adapter_input_id"],
                "paper_adapter_input_ref": paper_by_packet[packet_id]["adapter_input_id"],
                "orphan_flag": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""
