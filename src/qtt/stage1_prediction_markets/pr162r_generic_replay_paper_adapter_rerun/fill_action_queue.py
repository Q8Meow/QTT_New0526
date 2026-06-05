"""Missing data-binding and fill-action queue for PR162R."""

from __future__ import annotations

from typing import Any

from .adapter_contracts import PAPER_REQUIRED_BINDINGS, REPLAY_REQUIRED_BINDINGS


def build_missing_binding_actions(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        rows.append(_action(index, packet, "REPLAY", _replay_family(packet), REPLAY_REQUIRED_BINDINGS[0]))
        rows.append(_action(index + len(packets), packet, "PAPER", "MISSING_PAPER_MARKET_STATE_BINDING", PAPER_REQUIRED_BINDINGS[0]))
        rows.append(_action(index + (2 * len(packets)), packet, "LATENCY", "MISSING_LATENCY_MEASUREMENT", "benchmark_latency_measurement"))
    return rows


def _action(index: int, packet: dict[str, Any], lane: str, family: str, required_input: str) -> dict[str, Any]:
    qku_id = _first_qku(packet)
    query = _query(packet, lane, family)
    return {
        "action_id": f"PR162R_MISSING_BINDING_ACTION::{index:05d}",
        "candidate_packet_id": packet.get("candidate_packet_id"),
        "qku_id": qku_id,
        "formulation_ref": packet.get("formulation_ref"),
        "callable_ref": packet.get("callable_ref"),
        "missing_field": required_input,
        "required_input": required_input,
        "fill_action_family": family,
        "responsible_agent": _responsible_agent(packet, lane),
        "suggested_source_classes": _source_classes(lane, packet),
        "source_scout_query_if_useful": query,
        "downstream_consumer": _downstream_consumer(lane),
        "replay_impact": "required before replay run-request can become executable" if lane == "REPLAY" else "non-blocking for replay except paired readiness" if lane == "PAPER" else "benchmark required before any future live hot path",
        "paper_impact": "required before paper run-request can become executable" if lane == "PAPER" else "non-blocking for paper except paired readiness" if lane == "REPLAY" else "benchmark required before any future live hot path",
        "quantum_impact": "required for quantum coefficient/material input binding" if packet.get("candidate_type") == "QUANTUM_FORMULATION" else "not quantum-specific",
        "latency_impact": "latency benchmark missing; PR162R remains replay/paper-only" if lane == "LATENCY" else "data binding impacts replay/paper readiness, not live latency authority",
        "priority_score": _priority(packet, lane),
        "owner_override_allowed_for_internal_priority": True,
        "owner_override_cannot_fabricate_external_fact": True,
        "live_order_authority": False,
        "validation_status": "PASS",
    }


def _replay_family(packet: dict[str, Any]) -> str:
    fields = set(str(field) for field in packet.get("inputs", []))
    candidate_type = packet.get("candidate_type")
    if candidate_type == "QUANTUM_FORMULATION":
        return "MISSING_QUANTUM_OBJECTIVE_PARAMETER"
    if {"best_bid", "best_ask", "bid_size", "ask_size"} & fields:
        return "MISSING_ORDERBOOK_SNAPSHOT_SERIES"
    if {"volume", "depth", "available_depth"} & fields:
        return "MISSING_VOLUME_OR_DEPTH_SERIES"
    if {"actual_outcomes", "outcome"} & fields:
        return "MISSING_OUTCOME_LABEL"
    if {"p_model", "predicted_probabilities", "probability"} & fields:
        return "MISSING_PROBABILITY_MODEL_INPUT"
    if {"fee_estimate"} & fields:
        return "MISSING_FEE_MODEL_INPUT"
    if {"slippage_estimate", "slippage_component"} & fields:
        return "MISSING_SLIPPAGE_MODEL_INPUT"
    if {"covariance", "covariance_ij"} & fields:
        return "MISSING_COVARIANCE_INPUT"
    return "MISSING_HISTORICAL_PRICE_SERIES"


def _responsible_agent(packet: dict[str, Any], lane: str) -> str:
    if packet.get("candidate_type") == "QUANTUM_FORMULATION":
        return "QUANTUM_ADVISORY_MAPPING_AGENT" if lane != "PAPER" else "REPLAY_PAPER_CANDIDATE_ROUTER"
    if lane == "LATENCY":
        return "LATENCY_PRECOMPUTE_ROUTER"
    if lane == "PAPER":
        return "REPLAY_PAPER_CANDIDATE_ROUTER"
    return "DATA_ACQUISITION_AGENT"


def _source_classes(lane: str, packet: dict[str, Any]) -> list[str]:
    if lane == "LATENCY":
        return ["REPO_LOCAL_ARTIFACT_CANDIDATE", "OWNER_PROVIDED_CANDIDATE"]
    if packet.get("candidate_type") == "QUANTUM_FORMULATION":
        return ["QUANTUM_PROVIDER_DOC_CANDIDATE", "RESEARCH_PAPER_CANDIDATE", "REPO_LOCAL_ARTIFACT_CANDIDATE"]
    return ["OFFICIAL_DOC_CANDIDATE", "NON_OFFICIAL_WEB_CANDIDATE", "REPO_LOCAL_ARTIFACT_CANDIDATE"]


def _downstream_consumer(lane: str) -> str:
    if lane == "PAPER":
        return "PR163 generic paper adapter / paper capture framework"
    if lane == "LATENCY":
        return "PR162R-B replay/paper data binding completion and later hot-path benchmark gate"
    return "PR162R-B replay/paper data binding completion"


def _priority(packet: dict[str, Any], lane: str) -> float:
    base = 0.75 if lane in {"REPLAY", "PAPER"} else 0.45
    if packet.get("candidate_type") == "QUANTUM_FORMULATION":
        base += 0.05
    if packet.get("compute_tier") in {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA"}:
        base += 0.03
    return round(min(base, 0.99), 3)


def _query(packet: dict[str, Any], lane: str, family: str) -> str:
    domain = packet.get("domain_family_key") or packet.get("candidate_type")
    return f"{lane.lower()} {family.lower()} prediction market {domain} data binding source"


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""
