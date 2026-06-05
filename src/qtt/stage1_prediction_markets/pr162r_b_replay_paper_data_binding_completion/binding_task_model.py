"""BindingTaskV1 construction."""

from __future__ import annotations

from typing import Any

from .binding_family_classifier import (
    MARKET_FAMILY,
    data_granularity,
    quantum_or_classical_role,
    replay_or_paper_lane,
    target_field,
    unit_for_family,
)


def binding_task_id(index: int) -> str:
    return f"PR162R_B_BINDING_TASK::{index:04d}"


def dedup_group_label_for(
    *,
    binding_family: str,
    venue_scope: str,
    target: str,
    granularity: str,
    lane: str,
    role: str,
) -> str:
    return (
        f"{binding_family} | {venue_scope} | {MARKET_FAMILY} | {target} | "
        f"{granularity} | {lane} | {role}"
    )


def grouping_fields(binding_family: str, venue_scope: str) -> dict[str, str]:
    lane = replay_or_paper_lane(binding_family)
    role = quantum_or_classical_role(binding_family)
    target = target_field(binding_family)
    granularity = data_granularity(binding_family)
    return {
        "binding_family": binding_family,
        "venue_scope": venue_scope,
        "market_family": MARKET_FAMILY,
        "event_or_contract_scope_class": "BINARY_EVENT_OR_CONTRACT",
        "target_field": target,
        "data_granularity": granularity,
        "replay_or_paper_lane": lane,
        "quantum_or_classical_role": role,
        "unit": unit_for_family(binding_family),
        "scale": "binary_market_probability_0_to_1_or_usd_contract_units",
        "consumer_type": consumer_type_for_family(binding_family),
        "dedup_group_label": dedup_group_label_for(
            binding_family=binding_family,
            venue_scope=venue_scope,
            target=target,
            granularity=granularity,
            lane=lane,
            role=role,
        ),
    }


def consumer_type_for_family(binding_family: str) -> str:
    if binding_family.startswith("PAPER_"):
        return "PAPER_ADAPTER_AND_PAPER_CAPTURE"
    if binding_family.startswith("QUANTUM_"):
        return "QUANTUM_ADVISORY_BATCH_PRECOMPUTE"
    if binding_family == "CLASSICAL_COMPARATOR_INPUTS":
        return "CLASSICAL_COMPARATOR_AND_SCORING"
    if binding_family in {"FEE_MODEL", "SLIPPAGE_MODEL", "LATENCY_OBSERVATION_SERIES"}:
        return "REPLAY_PAPER_COST_LATENCY_MODEL"
    return "REPLAY_ADAPTER_AND_FEATURE_BUILDER"


def build_task_record(
    *,
    index: int,
    binding_family: str,
    venue_scope: str,
    actions: list[dict[str, Any]],
    packet_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    fields = grouping_fields(binding_family, venue_scope)
    packet_ids = sorted({str(action.get("candidate_packet_id")) for action in actions})
    qku_ids = sorted({str(action.get("qku_id")) for action in actions if action.get("qku_id")})
    agent_ids = sorted(
        {
            agent
            for packet_id in packet_ids
            for agent in packet_by_id.get(packet_id, {}).get("downstream_agent_refs", [])
        }
    )
    return {
        "binding_task_id": binding_task_id(index),
        **fields,
        "source_class_priority": source_class_priority(fields["binding_family"], fields["venue_scope"]),
        "impacted_missing_action_refs": sorted(str(action.get("action_id")) for action in actions),
        "impacted_candidate_packet_ids": packet_ids,
        "impacted_qku_ids": qku_ids,
        "impacted_agent_ids": agent_ids or ["QKU_COMPUTE_ENGINE", "REPLAY_PAPER_CANDIDATE_ROUTER"],
        "expected_rows_resolved": len(packet_ids),
        "dedup_group_reason": "Plain-text deterministic grouping by family, venue, market family, target, granularity, lane, and role.",
        "priority_score": round(max(float(action.get("priority_score", 0.0)) for action in actions), 4),
        "materialization_status": "BINDING_MATERIALIZED",
        "materialized_binding_refs": [],
        "exact_unavailable_reason": "",
        "downstream_refs": downstream_refs(fields["binding_family"]),
        "live_order_authority": False,
        "validation_status": "PASS",
    }


def source_class_priority(binding_family: str, venue_scope: str) -> list[str]:
    classes = ["REPO_LOCAL_ARTIFACT_CANDIDATE", "SYNTHETIC_TEST_FIXTURE"]
    if venue_scope != "VENUE_NEUTRAL_SYNTHETIC_FIXTURE":
        classes.insert(0, "OFFICIAL_SOURCE_CANDIDATE")
        classes.append("NON_OFFICIAL_WEB_CANDIDATE")
    if binding_family in {"HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES", "CROSS_VENUE_DISAGREEMENT_INPUTS"}:
        classes.append("RESEARCH_SOURCE_CANDIDATE")
    return classes


def downstream_refs(binding_family: str) -> list[str]:
    refs = [
        "QKU Compute Engine",
        "Formula/Algorithm Runtime candidate lane",
        "Feature Builder",
        "Replay/Paper Candidate Router",
        "PR163 Paper Adapter / Paper Capture Framework",
        "PR164 Review/Provenance",
        "PR165 Scoring/Ranking/Promotion",
        "PR162E Plugin Intake",
    ]
    if binding_family.startswith("QUANTUM_"):
        refs.append("Quantum Advisory / Quantum Mapping Agent")
        refs.append("PR162Q quantum expansion")
    if binding_family in {
        "COVARIANCE_CORRELATION_INPUTS",
        "PROBABILITY_MODEL_INPUTS",
        "PAPER_PORTFOLIO_STATE",
        "PAPER_EXECUTION_COST_MODEL",
        "QUANTUM_OBJECTIVE_INPUTS",
        "QUANTUM_CONSTRAINT_INPUTS",
    }:
        refs.extend(["Risk Manager", "Capital Allocation", "Parameter Stack Agent"])
    refs.append("future Execution Router boundary only after later owner approval")
    return refs
