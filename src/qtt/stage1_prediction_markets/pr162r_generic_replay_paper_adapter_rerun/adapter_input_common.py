"""Common ReplayPaperAdapterInputV1 row construction."""

from __future__ import annotations

from typing import Any

from .authority_policy import candidate_truth_status_for_adapter, map_source_truth_status


def build_adapter_input_rows(
    *,
    lane: str,
    packets: list[dict[str, Any]],
    computability_by_packet: dict[str, dict[str, Any]],
    binding_by_packet: dict[str, dict[str, Any]],
    smoke_by_formulation: dict[str, dict[str, Any]],
    latency_by_packet: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        packet_id = str(packet.get("candidate_packet_id"))
        comp = computability_by_packet.get(packet_id, {})
        binding = binding_by_packet.get(packet_id, {})
        smoke = smoke_by_formulation.get(str(packet.get("formulation_ref")), {})
        latency = latency_by_packet.get(packet_id, {})
        smoke_passed = smoke.get("smoke_execution_status") == "SMOKE_EXECUTION_PASSED"
        replay_status = "REPLAY_INPUT_FILL_REQUIRED"
        paper_status = "PAPER_INPUT_FILL_REQUIRED"
        paired_status = "PAIRED_FILL_REQUIRED"
        rows.append(
            {
                "adapter_input_id": f"PR162R_{lane}_ADAPTER_INPUT::{index:05d}",
                "adapter_lane": lane,
                "candidate_packet_ref": packet_id,
                "formulation_ref": packet.get("formulation_ref"),
                "callable_ref": packet.get("callable_ref"),
                "qku_ids": list(packet.get("qku_ids", [])),
                "agent_refs": list(packet.get("downstream_agent_refs", [])),
                "source_truth_status": map_source_truth_status(packet.get("source_truth_status")),
                "candidate_truth_status": candidate_truth_status_for_adapter(smoke_passed=smoke_passed, fill_required=True),
                "source_candidate_refs": list(packet.get("source_locator_refs", [])),
                "replay_paper_candidate_flag": bool(packet.get("replay_paper_candidate_flag")),
                "live_order_authority": False,
                "formula_or_algorithm_or_quantum_type": packet.get("candidate_type"),
                "computability_route": comp.get("computability_route"),
                "required_inputs": list(binding.get("required_inputs", [])),
                "available_inputs": list(binding.get("available_inputs", [])),
                "missing_inputs": list(binding.get("missing_replay_inputs", [])) + list(binding.get("missing_paper_inputs", [])),
                "data_binding_status": binding.get("data_binding_status", "DATA_BINDING_FILL_REQUIRED"),
                "data_binding_refs": list(binding.get("data_binding_refs", [])),
                "fill_action_refs": list(binding.get("fill_action_refs", [])),
                "test_vector_refs": list(packet.get("test_vectors", [])),
                "smoke_execution_status": smoke.get("smoke_execution_status", "SMOKE_EXECUTION_SKIPPED_WITH_EXACT_REASON"),
                "replay_adapter_status": replay_status,
                "paper_adapter_status": paper_status,
                "paired_status": paired_status,
                "latency_class": packet.get("latency_class"),
                "compute_tier": packet.get("compute_tier"),
                "precompute_required": bool(latency.get("precompute_required_flag")),
                "cacheable": bool(packet.get("cacheable")),
                "incremental_update_suitable": bool(packet.get("incremental_update_supported")),
                "quantum_batch_required": bool(latency.get("quantum_batch_only_flag")),
                "classical_comparator_refs": list(packet.get("classical_comparator_refs", [])),
                "route_triage_refs": ["docs/master_plan/generated/PR136RouteTriage.report.json"],
                "market_specific_index_refs": ["docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"],
                "command_action_refs": ["docs/master_plan/generated/PR136CommandActionMatrix.report.json"],
                "upstream_lineage_refs": [
                    "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json",
                    "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json",
                    "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json",
                ],
                "downstream_handoff_refs": ["PR163", "PR164", "PR165", "PR162E"],
                "no_result_packet_created": True,
                "no_live_order_authority": True,
                "validation_status": "PASS",
            }
        )
    return rows
