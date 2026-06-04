"""CandidatePacketV1 derivation for PR162D-R2A."""

from __future__ import annotations

from typing import Any


def build_candidate_packets(
    mapping_attempts: list[dict[str, Any]],
    formulation_by_id: dict[str, dict[str, Any]],
    exact_fill_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fill_by_qku = {row["qku_id"]: row for row in exact_fill_actions}
    packets: list[dict[str, Any]] = []
    for index, attempt in enumerate(mapping_attempts, start=1):
        formulation = formulation_by_id.get(str(attempt.get("formulation_ref")), {})
        fill = fill_by_qku.get(attempt["qku_id"])
        formulation_ref = formulation.get("formulation_id")
        exact_fill_ref = fill.get("fill_action_id") if fill else None
        if not formulation_ref and not exact_fill_ref:
            continue
        packets.append(
            {
                "candidate_packet_id": f"PR162D_R2A_CANDIDATE_PACKET::{index:05d}",
                "formulation_ref": formulation_ref,
                "exact_fill_action_ref": exact_fill_ref,
                "source_universe": attempt["source_universe"],
                "source_record_ids": attempt["source_record_ids"],
                "domain_family_key": attempt["domain_family_key"],
                "subfamily_key": attempt["subfamily_key"],
                "variant_key": attempt["variant_key"],
                "qku_ids": [attempt["qku_id"]],
                "formula_family": formulation.get("domain_family_key") if formulation.get("formulation_type") in {"FORMULA", "FEATURE"} else None,
                "algorithm_family": formulation.get("domain_family_key") if formulation.get("formulation_type") == "ALGORITHM" else None,
                "parameter_pack_family": formulation.get("domain_family_key") if formulation.get("formulation_type") == "PARAMETER_PACK" else None,
                "quantum_family": formulation.get("domain_family_key") if formulation.get("formulation_type") == "QUANTUM_FORMULATION" else None,
                "candidate_type": formulation.get("formulation_type", "FIELD_FILL_ACTION"),
                "expression": formulation.get("expression"),
                "algorithm_pseudocode": formulation.get("algorithm_procedure"),
                "callable_ref": formulation.get("callable_ref"),
                "inputs": formulation.get("inputs", []),
                "outputs": formulation.get("outputs", []),
                "units": formulation.get("units_or_type_hints", {}),
                "unit_unknown_but_type_known": formulation.get("unit_unknown_but_type_known_flag", False),
                "candidate_default_ranges": formulation.get("candidate_default_ranges", {}),
                "required_data_bindings": ["replay_or_paper_candidate_data_binding"],
                "test_vectors": formulation.get("test_vector_refs", []),
                "formulation_materialization_state": formulation.get("validator_materiality_status", "EXACT_FIELD_FILL_ACTION_CREATED"),
                "replay_paper_route_state": "REPLAY_PAPER_ROUTE_READY" if formulation_ref else "FIELD_FILL_REQUIRED",
                "live_materialization_state": "LIVE_MATERIALIZATION_NOT_IN_SCOPE",
                "source_truth_status": attempt["source_truth_status"],
                "candidate_truth_status": attempt["candidate_truth_status"],
                "source_locator_refs": formulation.get("source_locator_refs", ["OWNER_TEMPLATE_PR162D_R2A"]),
                "official_truth_flag": False,
                "candidate_or_provisional_flag": True,
                "replay_paper_candidate_flag": attempt["replay_paper_candidate_flag"],
                "live_order_authority": False,
                "latency_class": formulation.get("latency_class", "REPLAY_PAPER_ONLY"),
                "compute_tier": formulation.get("compute_tier", "TIER_5_REPLAY_PAPER_RESEARCH_ONLY"),
                "precompute_allowed": formulation.get("compute_tier") not in {"TIER_4_QUANTUM_OR_HYBRID_BATCH_OPTIMIZER"},
                "cacheable": formulation.get("compute_tier") in {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA"},
                "vectorized_supported": formulation.get("compute_tier") == "TIER_2_VECTORIZED_FEATURE_FORMULA",
                "incremental_update_supported": formulation.get("latency_class") == "INCREMENTAL_UPDATE_ELIGIBLE",
                "quantum_applicability": {
                    "quantum_candidate_flag": formulation.get("formulation_type") == "QUANTUM_FORMULATION",
                    "quantum_backend_execution_flag": False,
                    "quantum_advantage_claim_flag": False,
                },
                "quantum_mapping_refs": [formulation_ref] if formulation.get("formulation_type") == "QUANTUM_FORMULATION" else [],
                "classical_comparator_refs": [formulation.get("classical_comparator_ref")] if formulation.get("classical_comparator_ref") else [],
                "upstream_pr_refs": ["PR162D", "PR162D_R1", "PR162R_A"],
                "downstream_pr_refs": ["PR162R", "PR163", "PR164", "PR165", "PR162D_R2", "PR162E"],
                "upstream_agent_refs": ["QKU_FORMULATION_FIRST_MATERIALIZER"],
                "downstream_agent_refs": [
                    "QKU_COMPUTE_ENGINE",
                    "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_LANE",
                    "FEATURE_BUILDER",
                    "PARAMETER_STACK_AGENT",
                    "QUANTUM_ADVISORY_MAPPING_AGENT",
                    "REPLAY_PAPER_CANDIDATE_ROUTER",
                ],
                "replay_route": "PR162R_GENERIC_CANDIDATE_INPUT_EXTENSION",
                "paper_route": "PR163_GENERIC_PAPER_CANDIDATE_INPUT",
                "promotion_state_seed": "NEEDS_REPLAY_PAPER_EVIDENCE",
                "owner_review_state": "OWNER_REVIEW_NOT_REQUIRED_FOR_CANDIDATE_COMPUTABILITY",
                "fill_actions": [exact_fill_ref] if exact_fill_ref else [],
                "validation_status": "PASS",
                "schema_version": "CandidatePacketV1",
                "packet_only_flag": False,
                "route_only_flag": False,
                "metadata_only_flag": False,
                "quantum_label_only_flag": False,
            }
        )
    return packets


def build_candidate_intake_lanes(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet in packets:
        if packet.get("formulation_ref") and packet.get("replay_paper_route_state") == "REPLAY_PAPER_ROUTE_READY":
            lane = "FAST_REPLAY_PAPER_CANDIDATE"
        elif packet.get("formulation_ref"):
            lane = "FORMULATION_ONLY_ROUTE_FILL_REQUIRED"
        elif packet.get("exact_fill_action_ref"):
            lane = "FIELD_FILL_REQUIRED"
        else:
            lane = "EXECUTABLE_WITH_ENHANCEMENT_BACKLOG"
        rows.append(
            {
                "candidate_packet_id": packet["candidate_packet_id"],
                "qku_ids": packet["qku_ids"],
                "primary_intake_lane": lane,
                "formulation_ref": packet.get("formulation_ref"),
                "exact_fill_action_ref": packet.get("exact_fill_action_ref"),
                "mapping_attempted_flag": True,
                "live_order_authority": False,
            }
        )
    return rows
