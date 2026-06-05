"""Paper capture events and capture bundles."""

from __future__ import annotations

from typing import Any

from .authority_policy import llm_exclusion_fields, no_authority_fields, plain_ref


def build_capture_event(
    *,
    index: int,
    candidate_packet_id: str,
    qku_ids: list[str],
    agent_refs: list[str],
    formulation_refs: list[str],
    adapter_input_ref: str,
    decision_ref: str,
    order_ref: str,
    pretrade_ref: str,
    risk_ref: str,
    state_refs: list[str],
    fill_refs: list[str],
    ledger_ref: str,
    cash_ref: str,
    cost_ref: str,
    latency_ref: str,
    source_candidate_refs: list[str],
    binding_refs: list[str],
    quantum_refs: list[str],
    qku_handoff_ref: str,
    llm_ref: str,
) -> dict[str, Any]:
    return {
        "capture_event_ref": plain_ref("CAPTURE_EVENT", index),
        "candidate_packet_id": candidate_packet_id,
        "qku_ids": qku_ids,
        "agent_refs": agent_refs,
        "formulation_refs": formulation_refs,
        "paper_adapter_input_ref": adapter_input_ref,
        "paper_decision_intent_ref": decision_ref,
        "paper_order_intent_ref": order_ref,
        "pretrade_receipt_ref": pretrade_ref,
        "risk_policy_receipt_ref": risk_ref,
        "order_state_transition_refs": state_refs,
        "synthetic_fill_event_refs": fill_refs,
        "portfolio_ledger_snapshot_refs": [ledger_ref],
        "cash_reservation_refs": [cash_ref],
        "execution_cost_receipt_refs": [cost_ref],
        "latency_slippage_receipt_refs": [latency_ref],
        "source_candidate_refs": source_candidate_refs,
        "pr162r_b_binding_refs": binding_refs,
        "quantum_advisory_refs": quantum_refs,
        "qku_prioritization_feature_handoff_ref": qku_handoff_ref,
        "llm_future_handoff_exclusion_receipt_ref": llm_ref,
        "downstream_pr163_b_refs": [plain_ref("PR163B_HANDOFF", index)],
        "downstream_pr164_refs": [plain_ref("PR164_HANDOFF", index)],
        "downstream_pr165_refs": [plain_ref("PR165_HANDOFF", index)],
        "downstream_pr166_refs": [plain_ref("PR166_HANDOFF", index)],
        "truth_status": "SYNTHETIC_OR_CANDIDATE_PAPER_CAPTURE",
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }


def build_capture_bundle(index: int, capture_event: dict[str, Any], terminal_state: str, scenario_id: str) -> dict[str, Any]:
    return {
        "capture_bundle_ref": plain_ref("CAPTURE_BUNDLE", index),
        "candidate_packet_id": capture_event["candidate_packet_id"],
        "paper_capture_event_ref": capture_event["capture_event_ref"],
        "scenario_id": scenario_id,
        "terminal_state": terminal_state,
        "bundle_truth_status": "SYNTHETIC_OR_CANDIDATE_PAPER_CAPTURE",
        "paper_result_packet_created": False,
        "replay_result_packet_created": False,
        "profit_evidence_created": False,
        "downstream_pr163_b_paired_replay_paper_executor_ref": plain_ref("PR163B_HANDOFF", index),
        "downstream_pr164_review_provenance_ref": plain_ref("PR164_HANDOFF", index),
        "downstream_pr165_scoring_ranking_ref": plain_ref("PR165_HANDOFF", index),
        "downstream_pr166_llm_review_lane_ref": plain_ref("PR166_HANDOFF", index),
        "validation_status": "PASS",
        **llm_exclusion_fields(),
        **no_authority_fields(),
    }
