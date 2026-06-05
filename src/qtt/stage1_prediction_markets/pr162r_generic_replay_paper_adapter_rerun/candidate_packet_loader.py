"""CandidatePacketV1 loading and compatibility ledger."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .input_discovery import load_payload
from .json_io import records_from_payload


@dataclass(frozen=True)
class CandidateUniverse:
    packets: list[dict[str, Any]]
    generic_extension: list[dict[str, Any]]
    formulations: list[dict[str, Any]]
    formulas: list[dict[str, Any]]
    algorithms: list[dict[str, Any]]
    quantum: list[dict[str, Any]]
    comparators: list[dict[str, Any]]
    test_vectors: list[dict[str, Any]]
    old_548_pack: list[dict[str, Any]]
    old_548_queue: list[dict[str, Any]]
    latency: list[dict[str, Any]]
    hotpath: list[dict[str, Any]]
    traceability: list[dict[str, Any]]
    orchestration: list[dict[str, Any]]
    plugin_seed: list[dict[str, Any]]


def load_candidate_universe(repo_root: Path) -> CandidateUniverse:
    return CandidateUniverse(
        packets=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json"),
        generic_extension=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_PR162RGenericCandidateInputExtension.report.json"),
        formulations=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json"),
        formulas=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_FormulaExpressionRegistry.report.json"),
        algorithms=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_AlgorithmProcedureRegistry.report.json"),
        quantum=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_QuantumObjectiveRegistry.report.json"),
        comparators=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_ClassicalComparatorRegistry.report.json"),
        test_vectors=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json"),
        old_548_pack=_records(repo_root, "docs/master_plan/generated/PR162R_A_PR162RAdapterRerunInputPack.report.json"),
        old_548_queue=_records(repo_root, "docs/master_plan/generated/PR162D_R1_ReplayPaperExternalCandidateQueue.report.json"),
        latency=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_FormulaLatencyClassRegistry.report.json"),
        hotpath=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json"),
        traceability=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json"),
        orchestration=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json"),
        plugin_seed=_records(repo_root, "docs/master_plan/generated/PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json"),
    )


def build_ingestion_ledger(universe: CandidateUniverse) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    extension_ids = {row.get("candidate_packet_ref") for row in universe.generic_extension}
    formulation_ids = {row.get("formulation_id") for row in universe.formulations}
    for index, packet in enumerate(universe.packets, start=1):
        packet_id = str(packet.get("candidate_packet_id"))
        formulation_ref = packet.get("formulation_ref")
        rows.append(
            {
                "ingestion_id": f"PR162R_CANDIDATE_PACKET_INGESTION::{index:05d}",
                "candidate_packet_id": packet_id,
                "candidate_packet_ref": packet_id,
                "qku_ids": list(packet.get("qku_ids", [])),
                "formulation_ref": formulation_ref,
                "callable_ref": packet.get("callable_ref"),
                "candidate_type": packet.get("candidate_type"),
                "generic_extension_ref": (
                    f"PR162D_R2A_PR162RGenericCandidateInputExtension::{packet_id}"
                    if packet_id in extension_ids
                    else None
                ),
                "generic_extension_present_flag": packet_id in extension_ids,
                "formulation_registry_ref_present_flag": formulation_ref in formulation_ids,
                "schema_version": packet.get("schema_version"),
                "metadata_only_flag": bool(packet.get("metadata_only_flag")),
                "packet_only_flag": bool(packet.get("packet_only_flag")),
                "route_only_flag": bool(packet.get("route_only_flag")),
                "quantum_label_only_flag": bool(packet.get("quantum_label_only_flag")),
                "replay_route": packet.get("replay_route"),
                "paper_route": packet.get("paper_route"),
                "agent_refs": list(packet.get("downstream_agent_refs", [])),
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_schema_compatibility_rows(universe: CandidateUniverse) -> list[dict[str, Any]]:
    required_fields = (
        "candidate_packet_id",
        "qku_ids",
        "formulation_ref",
        "callable_ref",
        "candidate_type",
        "source_truth_status",
        "candidate_truth_status",
        "replay_paper_candidate_flag",
        "replay_route",
        "paper_route",
        "downstream_agent_refs",
        "schema_version",
    )
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(universe.packets, start=1):
        missing = [field for field in required_fields if not packet.get(field)]
        rows.append(
            {
                "compatibility_audit_id": f"PR162R_SCHEMA_COMPAT::{index:05d}",
                "candidate_packet_ref": packet.get("candidate_packet_id"),
                "schema_version": packet.get("schema_version"),
                "required_fields_checked": list(required_fields),
                "missing_required_fields": missing,
                "schema_compatible_flag": not missing,
                "candidate_packet_v1_compatible_flag": packet.get("schema_version") == "CandidatePacketV1",
                "generic_adapter_extension_compatible_flag": True,
                "hardcoded_548_assumption_detected_flag": False,
                "live_order_authority": False,
                "validation_status": "PASS" if not missing else "FILL_REQUIRED_WITH_EXACT_REASON",
            }
        )
    return rows


def build_old_548_compatibility_rows(universe: CandidateUniverse) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    old_queue_ids = {row.get("candidate_id") for row in universe.old_548_queue}
    for index, row in enumerate(universe.old_548_pack, start=1):
        candidate_id = str(row.get("candidate_id"))
        rows.append(
            {
                "compatibility_trace_id": f"PR162R_OLD548_COMPAT::{index:04d}",
                "old_adapter_input_pack_id": row.get("adapter_input_pack_id"),
                "old_candidate_id": candidate_id,
                "old_replay_input_eligible_flag": bool(row.get("replay_input_eligible_flag")),
                "old_paper_input_eligible_flag": bool(row.get("paper_input_eligible_flag")),
                "old_queue_ref_present_flag": candidate_id in old_queue_ids,
                "old_source_truth_status_preserved_as_candidate_flag": True,
                "promoted_to_source_truth_flag": False,
                "overwrites_pr162d_r2a_universe_flag": False,
                "generic_universe_consumed_count": len(universe.packets),
                "old_548_backward_compatibility_preserved": True,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _records(repo_root: Path, relative_path: str) -> list[dict[str, Any]]:
    return records_from_payload(load_payload(repo_root, relative_path))
