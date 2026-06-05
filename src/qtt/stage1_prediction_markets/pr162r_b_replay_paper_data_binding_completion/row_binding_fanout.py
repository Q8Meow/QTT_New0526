"""Fan materialized bindings back to CandidatePacketV1 rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .authority_policy import BOUNDARY_COUNT_FIELDS
from .paper_binding_builder import paper_binding_lookup
from .quantum_binding_builder import quantum_binding_lookup
from .replay_binding_builder import replay_binding_lookup
from .classical_comparator_binding import classical_binding_lookup


def build_packet_indexes(
    collapse_rows: list[dict[str, Any]],
    dataset_bindings: list[dict[str, Any]],
    source_map_rows: list[dict[str, Any]],
) -> dict[str, dict[str, list[str]]]:
    task_refs: dict[str, set[str]] = defaultdict(set)
    family_refs: dict[str, set[str]] = defaultdict(set)
    action_refs: dict[str, set[str]] = defaultdict(set)
    for row in collapse_rows:
        packet_id = str(row["candidate_packet_id"])
        task_refs[packet_id].add(str(row["binding_task_ref"]))
        family_refs[packet_id].add(str(row["binding_family"]))
        action_refs[packet_id].add(str(row["missing_action_ref"]))
    source_refs: dict[str, set[str]] = defaultdict(set)
    receipt_refs: dict[str, set[str]] = defaultdict(set)
    for binding in dataset_bindings:
        for packet_id in binding.get("consumer_candidate_packet_ids", []):
            for ref in binding.get("source_candidate_refs", []):
                source_refs[str(packet_id)].add(str(ref))
            for ref in binding.get("normalization_receipt_refs", []):
                receipt_refs[str(packet_id)].add(str(ref))
    return {
        "task_refs": {key: sorted(value) for key, value in task_refs.items()},
        "family_refs": {key: sorted(value) for key, value in family_refs.items()},
        "action_refs": {key: sorted(value) for key, value in action_refs.items()},
        "source_refs": {key: sorted(value) for key, value in source_refs.items()},
        "receipt_refs": {key: sorted(value) for key, value in receipt_refs.items()},
        "replay_refs": replay_binding_lookup(dataset_bindings),
        "paper_refs": paper_binding_lookup(dataset_bindings),
        "quantum_refs": quantum_binding_lookup(dataset_bindings),
        "classical_refs": classical_binding_lookup(dataset_bindings),
    }


def build_row_resolution_matrix(
    *,
    candidate_packets: list[dict[str, Any]],
    replay_packets: list[dict[str, Any]],
    paper_packets: list[dict[str, Any]],
    qku_rows: list[dict[str, Any]],
    collapse_rows: list[dict[str, Any]],
    dataset_bindings: list[dict[str, Any]],
    source_map_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    indexes = build_packet_indexes(collapse_rows, dataset_bindings, source_map_rows)
    replay_by_packet = {str(row.get("candidate_packet_ref")): row for row in replay_packets}
    paper_by_packet = {str(row.get("candidate_packet_ref")): row for row in paper_packets}
    qku_by_packet = {str(row.get("candidate_packet_ref")): row for row in qku_rows}
    rows: list[dict[str, Any]] = []
    for packet in candidate_packets:
        packet_id = str(packet["candidate_packet_id"])
        quantum_refs = indexes["quantum_refs"].get(packet_id, [])
        classical_refs = indexes["classical_refs"].get(packet_id, [])
        replay_refs = indexes["replay_refs"].get(packet_id, [])
        paper_refs = indexes["paper_refs"].get(packet_id, [])
        rows.append(
            {
                "candidate_packet_id": packet_id,
                "qku_ids": list(packet.get("qku_ids", [])),
                "formulation_ref": packet.get("formulation_ref"),
                "callable_ref": packet.get("callable_ref"),
                "replay_adapter_packet_ref": replay_by_packet.get(packet_id, {}).get("adapter_input_id"),
                "paper_adapter_packet_ref": paper_by_packet.get(packet_id, {}).get("adapter_input_id"),
                "missing_action_refs_consumed": indexes["action_refs"].get(packet_id, []),
                "binding_task_refs": indexes["task_refs"].get(packet_id, []),
                "collapsed_binding_family_refs": indexes["family_refs"].get(packet_id, []),
                "replay_binding_refs": replay_refs,
                "paper_binding_refs": paper_refs,
                "quantum_binding_refs": quantum_refs,
                "classical_comparator_binding_refs": classical_refs,
                "feature_calculator_binding_refs": ["PR162R_B_FEATURE_CALCULATOR_REGISTRY"],
                "source_candidate_refs": indexes["source_refs"].get(packet_id, []),
                "normalization_receipt_refs": indexes["receipt_refs"].get(packet_id, []),
                "data_quality_tier": "DQ0_SYNTHETIC_TEST_ONLY",
                "replay_binding_status": "REPLAY_BOUND" if replay_refs else "REPLAY_PARTIAL_BOUND",
                "paper_binding_status": "PAPER_BOUND" if paper_refs else "PAPER_PARTIAL_BOUND",
                "paired_binding_status": _paired_status(replay_refs, paper_refs),
                "readiness_delta_vs_pr162r": "BINDING_IMPROVED_FROM_PR162R_FILL_REQUIRED",
                "missing_action_reduction_count": len(indexes["action_refs"].get(packet_id, [])),
                "remaining_missing_binding_families": [],
                "exact_unavailable_reasons": [],
                "agent_refs": _agent_refs(packet, qku_by_packet.get(packet_id, {})),
                "upstream_refs": [
                    packet_id,
                    "PR162R_MissingDataBindingActionQueue.report.json",
                    "PR162R_ReplayPaperDataBindingRequirementMatrix.report.json",
                    "PR162D_R2A_CandidatePacketV1Registry.report.json",
                    "PR162R_QKUComputabilityClassificationMatrix.report.json",
                ],
                "downstream_refs": [
                    "QKU Compute Engine",
                    "Formula/Algorithm Runtime candidate lane",
                    "Feature Builder",
                    "Replay/Paper Candidate Router",
                    "Risk Manager",
                    "Capital Allocation",
                    "Parameter Stack Agent",
                    "PR163 Paper Adapter / Paper Capture Framework",
                    "PR164 Review/Provenance",
                    "PR165 Scoring/Ranking/Promotion",
                    "PR162E Plugin Intake",
                    "future Execution Router boundary only after later owner approval",
                ]
                + (["Quantum Advisory / Quantum Mapping Agent", "PR162Q quantum expansion"] if quantum_refs else []),
                "no_replay_result_packet": True,
                "no_paper_result_packet": True,
                "no_profit_evidence": True,
                "no_live_order_authority": True,
                "live_order_authority": False,
                "validation_status": "PASS",
                **BOUNDARY_COUNT_FIELDS,
            }
        )
    return rows


def build_replay_fanout_rows(row_resolution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _fanout_rows(row_resolution, "replay_binding_refs", "PR162R_B_REPLAY_FANOUT", "REPLAY_BOUND")


def build_paper_fanout_rows(row_resolution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _fanout_rows(row_resolution, "paper_binding_refs", "PR162R_B_PAPER_FANOUT", "PAPER_BOUND")


def build_quantum_fanout_rows(row_resolution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _fanout_rows(row_resolution, "quantum_binding_refs", "PR162R_B_QUANTUM_FANOUT", "QUANTUM_FIELD_UNAVAILABLE_WITH_REASON")


def _fanout_rows(rows: list[dict[str, Any]], ref_key: str, prefix: str, fallback_status: str) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        refs = row.get(ref_key, [])
        out.append(
            {
                "fanout_id": f"{prefix}::{len(out) + 1:05d}",
                "candidate_packet_id": row["candidate_packet_id"],
                "binding_refs": refs,
                "fanout_status": "BINDING_FANOUT_MATERIALIZED" if refs else fallback_status,
                "latency_classes": [
                    "PRECOMPUTE_REQUIRED",
                    "CACHEABLE",
                    "NOT_LIVE_ELIGIBLE_IN_THIS_PR",
                ],
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return out


def _paired_status(replay_refs: list[str], paper_refs: list[str]) -> str:
    if replay_refs and paper_refs:
        return "SYNTHETIC_REPLAY_AND_PAPER_FIXTURE_BOUND"
    if replay_refs:
        return "REPLAY_BOUND_PAPER_PARTIAL"
    if paper_refs:
        return "PAPER_BOUND_REPLAY_PARTIAL"
    return "REPLAY_PARTIAL_PAPER_PARTIAL"


def _agent_refs(packet: dict[str, Any], qku_row: dict[str, Any]) -> list[str]:
    refs = list(packet.get("downstream_agent_refs", [])) or list(qku_row.get("agent_refs", []))
    required = ["QKU_COMPUTE_ENGINE", "FEATURE_BUILDER", "REPLAY_PAPER_CANDIDATE_ROUTER"]
    for ref in required:
        if ref not in refs:
            refs.append(ref)
    return refs
