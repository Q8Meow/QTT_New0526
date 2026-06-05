"""Source/candidate materialization and online scout queue builders."""

from __future__ import annotations

from typing import Any

from .authority_policy import map_source_truth_status


def build_source_materialization_rows(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        packet_id = str(packet.get("candidate_packet_id"))
        rows.append(
            {
                "source_candidate_id": f"PR162R_SOURCE_CANDIDATE::{index:05d}",
                "target_qku_id": _first_qku(packet),
                "target_field": "formulation_ref",
                "value": packet.get("formulation_ref"),
                "unit": None,
                "scale": None,
                "formula_or_algorithm_context": packet.get("candidate_type"),
                "source_class": "REPO_LOCAL_ARTIFACT_CANDIDATE",
                "source_locator": f"docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json#{packet_id}",
                "observed_at_utc": None,
                "extraction_basis": "repo-local PR162D-R2A CandidatePacketV1 row; not accepted source truth",
                "source_truth_status": map_source_truth_status(packet.get("source_truth_status")),
                "candidate_truth_status": "FORMULATION_EXECUTABLE_CANDIDATE",
                "source_candidate_refs": list(packet.get("source_locator_refs", [])),
                "replay_paper_use_allowed": True,
                "promotion_requires_replay_paper_evidence": True,
                "promotion_requires_owner_or_later_gate": True,
                "no_accepted_source_truth_claim": True,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_online_scout_rows(missing_actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, action in enumerate(missing_actions, start=1):
        target_field = str(action.get("missing_field"))
        rows.append(
            {
                "source_scout_id": f"PR162R_ONLINE_SOURCE_SCOUT::{index:05d}",
                "target_qku_id": action.get("qku_id"),
                "candidate_packet_id": action.get("candidate_packet_id"),
                "target_field": target_field,
                "expected_unit": _expected_unit(action),
                "expected_scale": _expected_scale(action),
                "search_query": action.get("source_scout_query_if_useful"),
                "source_classes_to_scout": list(action.get("suggested_source_classes", [])),
                "responsible_agent": action.get("responsible_agent"),
                "downstream_impact": action.get("downstream_consumer"),
                "replay_impact": action.get("replay_impact"),
                "paper_impact": action.get("paper_impact"),
                "quantum_impact": action.get("quantum_impact"),
                "priority_score": action.get("priority_score"),
                "candidate_truth_status": "FILL_REQUIRED_WITH_EXACT_REASON",
                "no_accepted_source_truth_claim": True,
                "ci_network_required_flag": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""


def _expected_unit(action: dict[str, Any]) -> str:
    family = str(action.get("fill_action_family"))
    if "LATENCY" in family:
        return "seconds_or_milliseconds"
    if "PROBABILITY" in family:
        return "probability_0_to_1"
    if "PRICE" in family or "ORDERBOOK" in family:
        return "venue_native_price_or_probability"
    return "field_specific_unit_from_adapter_contract"


def _expected_scale(action: dict[str, Any]) -> str:
    family = str(action.get("fill_action_family"))
    if "PROBABILITY" in family:
        return "0_to_1"
    if "LATENCY" in family:
        return "positive_real"
    return "candidate_field_native_scale"
