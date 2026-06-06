"""Paired replay/paper run input contracts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_run_input(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    row = ctx["row"]
    candidate = ctx["candidate"]
    paper = ctx["paper"]
    qku_ids = list(row.get("qku_ids") or candidate.get("qku_ids") or [])
    return {
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_ids": qku_ids,
        "formulation_refs": [row.get("formulation_ref")] if row.get("formulation_ref") else [],
        "formula_refs": [row.get("callable_ref")] if row.get("callable_ref") else [],
        "algorithm_refs": [candidate.get("algorithm_family", "PR163B_NONLIVE_REPLAY_PAPER_EXECUTION_MODEL")],
        "parameter_stack_refs_if_present": list(candidate.get("parameter_stack_refs", [])),
        "replay_binding_refs": list(row.get("replay_binding_refs") or []),
        "paper_binding_refs": list(row.get("paper_binding_refs") or []),
        "pr163_paper_capture_refs": [paper["capture_bundle_ref"], paper["capture_event_ref"]],
        "paper_decision_intent_ref": paper["decision_ref"],
        "paper_order_intent_ref": paper["order_ref"],
        "paper_pretrade_receipt_ref": paper["pretrade_ref"],
        "replay_market_state_ref": ctx["replay_market_state_ref"],
        "paper_market_state_ref": paper["market_state_ref"],
        "event_lifecycle_ref": ctx["event_lifecycle_ref"],
        "settlement_label_ref": ctx["settlement_label_ref"],
        "source_candidate_refs": list(row.get("source_candidate_refs") or []),
        "source_as_of_time": ctx["clock"]["source_as_of_time"],
        "feature_as_of_time": ctx["clock"]["feature_as_of_time"],
        "clock_ref": ctx["clock"]["clock_ref"],
        "input_lock_ref": ctx["input_lock"]["input_lock_ref"],
        "leakage_guard_ref": ctx["leakage_guard"]["leakage_guard_ref"],
        "data_quality_tier": row.get("data_quality_tier", "DQ0_SYNTHETIC_TEST_ONLY"),
        "replay_lane_enabled": True,
        "paper_lane_enabled": True,
        "paired_comparison_enabled": True,
        "exact_disabled_reason": "",
        "downstream_pr164_ref": plain_ref("PR164_HANDOFF", index),
        "downstream_pr165_ref": plain_ref("PR165_HANDOFF", index),
        "downstream_pr166_ref": plain_ref("PR166_HANDOFF", index),
        "no_live_authority": True,
        "no_profit_evidence": True,
        "no_source_acceptance": True,
        "no_connector_binding": True,
        "no_private_state_fetch": True,
        "no_llm_runtime": True,
        "no_quantum_backend": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
