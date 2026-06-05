"""Downstream PR handoff seed builders for PR162R."""

from __future__ import annotations

from typing import Any


def build_pr163_handoff_seed(paired_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_seed("PR163", "paper_adapter_capture_framework", index, row) for index, row in enumerate(paired_plan, start=1)]


def build_pr164_handoff_seed(paired_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_seed("PR164", "review_provenance_framework", index, row) for index, row in enumerate(paired_plan, start=1)]


def build_pr165_handoff_seed(paired_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_seed("PR165", "scoring_ranking_framework", index, row) for index, row in enumerate(paired_plan, start=1)]


def build_pr162e_plugin_seed(
    plugin_seed: list[dict[str, Any]],
    packets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    packet_count_by_formulation: dict[str, int] = {}
    for packet in packets:
        key = str(packet.get("formulation_ref"))
        packet_count_by_formulation[key] = packet_count_by_formulation.get(key, 0) + 1
    rows: list[dict[str, Any]] = []
    for index, seed in enumerate(plugin_seed, start=1):
        formulation_ref = str(seed.get("formulation_ref"))
        rows.append(
            {
                "plugin_compatibility_seed_id": f"PR162R_PR162E_PLUGIN_COMPAT::{index:04d}",
                "upstream_plugin_seed_ref": seed.get("plugin_seed_id"),
                "formulation_ref": formulation_ref,
                "callable_ref": seed.get("callable_ref"),
                "candidate_packet_count": packet_count_by_formulation.get(formulation_ref, 0),
                "replay_paper_route_state": seed.get("replay_paper_route_state"),
                "plugin_intake_recommendation": "PR162E_FORMULA_ALGORITHM_QUANTUM_PLUGIN_INTAKE",
                "runtime_allowlist_candidate_stage": "REPLAY_PAPER_CANDIDATE_ONLY",
                "no_live_order_authority": True,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _seed(pr_id: str, family: str, index: int, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "handoff_seed_id": f"PR162R_{pr_id}_HANDOFF_SEED::{index:05d}",
        "target_pr": pr_id,
        "handoff_family": family,
        "candidate_packet_ref": row["candidate_packet_ref"],
        "paired_run_request_candidate_ref": row["paired_run_request_candidate_id"],
        "status": "HANDOFF_SEED_CREATED_FILL_REQUIRED_NOT_EXECUTED",
        "fill_action_refs": list(row.get("fill_action_refs", [])),
        "downstream_compatibility_refs": ["PR163", "PR164", "PR165", "PR162E"],
        "result_packet_created_count": 0,
        "profit_evidence_count": 0,
        "live_order_authority": False,
        "validation_status": "PASS",
    }
