"""QKU upstream/downstream orchestration records for PR162D-R2A."""

from __future__ import annotations

from typing import Any


DOWNSTREAM_AGENTS = (
    "QKU Compute Engine",
    "Formula/Algorithm Runtime candidate lane",
    "Feature Builder",
    "Parameter Stack Agent",
    "Quantum Advisory / Quantum Mapping Agent",
    "Replay/Paper Candidate Router",
    "PR162R generic replay adapter candidate input",
    "PR163 generic paper adapter candidate input",
    "PR164 review/provenance framework",
    "PR165 scoring/ranking/promotion framework",
    "PR162D-R2 materialization expansion queue",
    "PR162E formula/algorithm/quantum plugin intake seed",
    "Risk Manager candidate review",
    "Capital Allocation candidate review",
    "Execution Router future final authority only after later gates/owner approval",
)


def build_upstream_downstream_matrix(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "orchestration_id": f"PR162D_R2A_ORCHESTRATION::{index:05d}",
            "candidate_packet_id": packet["candidate_packet_id"],
            "qku_ids": packet["qku_ids"],
            "formulation_ref": packet.get("formulation_ref"),
            "upstream_links": {
                "master_plan_section_locator": "docs/master_plan/QTT_MasterPlan_Current.md",
                "pr162d_record_refs": packet["source_record_ids"],
                "pr162d_r1_candidate_refs": ["PR162D_R1_ComputableCandidateRegistry.report.json"],
                "pr162r_a_candidate_refs": ["PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json"],
                "source_locator_refs": packet.get("source_locator_refs", []),
            },
            "downstream_links": list(DOWNSTREAM_AGENTS),
            "orphan_flag": False,
            "live_order_authority": False,
        }
        for index, packet in enumerate(packets, start=1)
    ]


def build_qku_agent_workflow_traceability(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "traceability_id": f"PR162D_R2A_QKU_AGENT_TRACE::{index:05d}",
            "qku_id": packet["qku_ids"][0],
            "candidate_packet_ref": packet["candidate_packet_id"],
            "formulation_ref": packet.get("formulation_ref"),
            "agent_workflow": [
                "QKU_FORMULATION_FIRST_MATERIALIZER",
                "QKU_COMPUTE_ENGINE",
                "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_LANE",
                "REPLAY_PAPER_CANDIDATE_ROUTER",
            ],
            "route_state": packet["replay_paper_route_state"],
            "orphan_flag": False,
            "live_order_authority": False,
        }
        for index, packet in enumerate(packets, start=1)
    ]


def build_pr162r_extension(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "pr162r_input_id": f"PR162D_R2A_PR162R_INPUT::{index:05d}",
            "candidate_packet_ref": packet["candidate_packet_id"],
            "formulation_ref": packet.get("formulation_ref"),
            "callable_ref": packet.get("callable_ref"),
            "qku_ids": packet["qku_ids"],
            "candidate_type": packet["candidate_type"],
            "replay_route": packet["replay_route"],
            "paper_route": packet["paper_route"],
            "schema_version": "CandidatePacketV1",
            "replay_execution_count": 0,
            "paper_execution_count": 0,
            "result_packet_created_count": 0,
            "live_order_authority": False,
        }
        for index, packet in enumerate(packets, start=1)
        if packet.get("formulation_ref")
    ]


def build_pr162e_plugin_seed_registry(formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, formulation in enumerate(formulations, start=1):
        rows.append(
            {
                "plugin_seed_id": f"PR162D_R2A_PLUGIN_SEED::{index:04d}",
                "formulation_ref": formulation["formulation_id"],
                "semantic_version": "0.1.0",
                "source_version": "owner_template_v1",
                "input_schema_version": "FormulationRecordV1",
                "output_schema_version": "CandidatePacketV1",
                "parameter_version": formulation.get("variant_key", "owner_template_v1"),
                "test_vector_version": "v1",
                "promotion_state_seed": "NEEDS_REPLAY_PAPER_EVIDENCE",
                "rollback_target": None,
                "equivalence_family": f"{formulation['domain_family_key']}::{formulation['subfamily_key']}",
                "duplicate_equivalence_refs": [],
                "candidate_registry_refs": ["PR162D_R2A_CandidatePacketV1Registry.report.json"],
                "qku_refs": [],
                "agent_routes": ["QKU_COMPUTE_ENGINE", "REPLAY_PAPER_CANDIDATE_ROUTER"],
                "replay_paper_routes": ["PR162R", "PR163"],
                "runtime_allowlist_candidate_stage": "REPLAY_PAPER_CANDIDATE_ONLY",
                "formulation_materialization_state": formulation["validator_materiality_status"],
                "replay_paper_route_state": formulation["replay_paper_route_state"],
                "callable_ref": formulation["callable_ref"],
                "live_order_authority": False,
            }
        )
    return rows
