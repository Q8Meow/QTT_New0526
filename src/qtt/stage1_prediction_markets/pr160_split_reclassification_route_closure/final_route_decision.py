"""Final PR160 route-decision construction."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .route_arbitration import selected_route


def _compatibility(record: Mapping[str, Any], route_class: str) -> list[str]:
    domain = str(record.get("pr150_target_domain_or_null") or "")
    if route_class == c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value:
        return [c.QuantumClassicalCompatibility.CLASSICAL_TRADING_ALGORITHM_COMPATIBLE.value]
    if domain == "INTEGER_LINEAR_QUADRATIC_PROGRAM_METADATA_SLOTS":
        return [
            c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value,
            c.QuantumClassicalCompatibility.QUBO_COMPATIBLE_METADATA_ONLY.value,
            c.QuantumClassicalCompatibility.QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE.value,
        ]
    if domain == "QUANTUM_PORTFOLIO_SELECTION_METADATA_SLOTS":
        return [
            c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value,
            c.QuantumClassicalCompatibility.QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_METADATA_ONLY.value,
        ]
    if domain == "QUANTUM_SEARCH_SPACE_METADATA_SLOTS":
        return [
            c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value,
            c.QuantumClassicalCompatibility.QUBO_COMPATIBLE_METADATA_ONLY.value,
            c.QuantumClassicalCompatibility.ISING_COMPATIBLE_METADATA_ONLY.value,
        ]
    if domain in {"VQE_ANSATZ_CLASS_METADATA_SLOTS", "VQE_EXPECTATION_TOLERANCE_TARGET_SLOTS"}:
        return [
            c.QuantumClassicalCompatibility.TRUE_QUANTUM_CANDIDATE.value,
            c.QuantumClassicalCompatibility.VQE_COMPATIBLE_METADATA_ONLY.value,
        ]
    if domain == "QUANTUM_APPLICABILITY_METADATA":
        return [
            c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value,
            c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value,
        ]
    if domain == "QUANTUM_APPLICABILITY_SCORE_INPUTS":
        return [
            c.QuantumClassicalCompatibility.CLASSICAL_FORMULA_COMPATIBLE.value,
            c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value,
        ]
    return [c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value]


def _downstream(route_class: str) -> dict[str, Any]:
    if route_class == c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value:
        return {
            "blocker_class": c.BlockerClass.SOURCE_LOCATOR_VALUE_UNIT_REQUIRED.value,
            "record_final_state": c.RecordFinalState.RECLASSIFIED_ROUTE_CLOSED_WITH_DOWNSTREAM_BLOCKER.value,
            "exact_next_action": "Add the target to PR159R for exact official locator, value, unit, scale, and field-scope capture; route accepted output to PR161/PR162 only after PR159R passes.",
            "required_actor": "PR159R_OFFICIAL_SOURCE_CAPTURE_AGENT",
            "required_input_artifact": c.PR159R_SOURCE_REQUEUE_PATH.as_posix(),
            "validator_that_will_unblock": c.PR159_VALIDATOR,
            "future_pr_route": c.FutureRoute.PR159R_EXACT_SOURCE_LOCATOR_VALUE_UNIT_CAPTURE.value,
            "risk_if_unresolved": "Venue normalization dependency remains unusable for scoring, replay, paper, and live gates.",
            "selection_readiness_impact": "BLOCKED_UNTIL_SOURCE_ACCEPTED_THEN_PR161_PR162_AUDITED",
            "trade_context_readiness_impact": "BLOCKED_FOR_VENUE_NORMALIZATION_METADATA",
            "low_latency_index_impact": "NOT_LOW_LATENCY_ELIGIBLE_UNTIL_SOURCE_ACCEPTED",
            "can_qtt_use_in_scoring_metadata_flag": False,
        }
    if route_class == c.ReclassificationFinalRouteClass.RUNTIME_RECEIPT_FUTURE_ROUTE.value:
        return {
            "blocker_class": c.BlockerClass.RUNTIME_RECEIPT_REQUIRED_FUTURE.value,
            "record_final_state": c.RecordFinalState.RECLASSIFIED_ROUTE_CLOSED_WITH_DOWNSTREAM_BLOCKER.value,
            "exact_next_action": "Defer VQE tolerance evidence to PR169 quantum backend gated sandbox; PR160 records only the route and forbids backend execution.",
            "required_actor": "PR169_QUANTUM_BACKEND_SANDBOX_AGENT",
            "required_input_artifact": "future_pr169_quantum_backend_gated_sandbox_receipt",
            "validator_that_will_unblock": "tools/validate_pr169_quantum_backend_gated_sandbox.py",
            "future_pr_route": c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
            "risk_if_unresolved": "Quantum tolerance target remains metadata-only and cannot influence replay, paper, optimizer, or live gates.",
            "selection_readiness_impact": "METADATA_ONLY_BLOCKED_UNTIL_QUANTUM_EVIDENCE_GATE",
            "trade_context_readiness_impact": "NO_TRADE_CONTEXT_USE_UNTIL_FUTURE_GATE",
            "low_latency_index_impact": "EXCLUDED_FROM_LOW_LATENCY_PATH",
            "can_qtt_use_in_scoring_metadata_flag": False,
        }
    if route_class == c.ReclassificationFinalRouteClass.SCORING_RANKING_METADATA_ROUTE.value:
        return {
            "blocker_class": c.BlockerClass.ACCEPTED_INPUTS_REQUIRED.value,
            "record_final_state": c.RecordFinalState.RECLASSIFIED_ROUTE_CLOSED_WITH_DOWNSTREAM_BLOCKER.value,
            "exact_next_action": "Carry as scoring/ranking metadata to PR164, then require replay/paper calibration and owner review before any live use.",
            "required_actor": "PR164_SCORING_RANKING_BRIDGE_AGENT",
            "required_input_artifact": "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json",
            "validator_that_will_unblock": "tools/validate_parameter_stack_scoring_and_ranking_gate.py",
            "future_pr_route": c.FutureRoute.PR164_SCORING_RANKING_BRIDGE.value,
            "risk_if_unresolved": "Quantum applicability score input cannot be consumed by scoring/ranking or selection gates.",
            "selection_readiness_impact": "READY_AS_METADATA_ONLY_AFTER_PR164_VALIDATION",
            "trade_context_readiness_impact": "TRADE_CONTEXT_METADATA_PENDING_SCORING_BRIDGE",
            "low_latency_index_impact": "LOW_LATENCY_METADATA_ONLY_AFTER_PRECOMPUTED_INDEX",
            "can_qtt_use_in_scoring_metadata_flag": True,
        }
    if route_class == c.ReclassificationFinalRouteClass.REPLAY_PAPER_EVALUATION_FUTURE_ROUTE.value:
        return {
            "blocker_class": c.BlockerClass.ACCEPTED_INPUTS_REQUIRED.value,
            "record_final_state": c.RecordFinalState.RECLASSIFIED_ROUTE_CLOSED_WITH_DOWNSTREAM_BLOCKER.value,
            "exact_next_action": "Route optimizer metadata to PR167/PR168 and require replay/paper evaluation before promotion; PR160 creates no optimizer output.",
            "required_actor": "PR167_OPTIMIZER_INTERFACE_AGENT",
            "required_input_artifact": "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json",
            "validator_that_will_unblock": "tools/validate_quantum_classical_optimizer_arbitration_gate.py",
            "future_pr_route": c.FutureRoute.PR167_OPTIMIZER_INTERFACE.value,
            "risk_if_unresolved": "Optimizer metadata remains non-consumable for optimizer arbitration, replay, paper, and live gates.",
            "selection_readiness_impact": "OPTIMIZER_METADATA_PENDING_REPLAY_PAPER",
            "trade_context_readiness_impact": "TRADE_CONTEXT_SELECTION_PENDING_OPTIMIZER_EVALUATION",
            "low_latency_index_impact": "EXCLUDED_FROM_LOW_LATENCY_PATH_UNTIL_CALIBRATED",
            "can_qtt_use_in_scoring_metadata_flag": True,
        }
    if route_class == c.ReclassificationFinalRouteClass.QUANTUM_CLASSICAL_METADATA_ONLY_ROUTE.value:
        return {
            "blocker_class": c.BlockerClass.NONE.value,
            "record_final_state": c.RecordFinalState.RECLASSIFIED_ROUTE_CLOSED.value,
            "exact_next_action": "Record quantum/classical compatibility metadata only and defer any backend execution or advantage claim to future gates.",
            "required_actor": "PR160_STATIC_ROUTE_CLOSURE_AGENT",
            "required_input_artifact": c.QUANTUM_COMPAT_UPDATE_PATH.as_posix(),
            "validator_that_will_unblock": c.PR160_VALIDATOR,
            "future_pr_route": c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
            "risk_if_unresolved": "No immediate blocker; metadata remains non-execution authority.",
            "selection_readiness_impact": "READY_AS_METADATA_ONLY_NO_SELECTION_EXECUTION",
            "trade_context_readiness_impact": "TRADE_CONTEXT_METADATA_ONLY",
            "low_latency_index_impact": "LOW_LATENCY_METADATA_ONLY_IF_PRECOMPUTED_ELIGIBLE",
            "can_qtt_use_in_scoring_metadata_flag": True,
        }
    return {
        "blocker_class": c.BlockerClass.INVALID_UNSUPPORTED_RECORD.value,
        "record_final_state": c.RecordFinalState.INVALID_OR_UNSUPPORTED_FAIL_CLOSED.value,
        "exact_next_action": "Fail closed and create a supported PR160 route classification before downstream use.",
        "required_actor": "OWNER_OR_ROUTE_TRIAGE_AGENT",
        "required_input_artifact": c.OWNER_DECISION_PACKET_PATH.as_posix(),
        "validator_that_will_unblock": c.PR160_VALIDATOR,
        "future_pr_route": c.FutureRoute.OWNER_REVIEW_AFTER_FUTURE_GATES.value,
        "risk_if_unresolved": "Record remains unusable in all future gates.",
        "selection_readiness_impact": "BLOCKED_INVALID_ROUTE",
        "trade_context_readiness_impact": "BLOCKED_INVALID_ROUTE",
        "low_latency_index_impact": "BLOCKED_INVALID_ROUTE",
        "can_qtt_use_in_scoring_metadata_flag": False,
    }


def final_decision(
    source_record: Mapping[str, Any],
    candidate_matrix_record: Mapping[str, Any],
) -> dict[str, Any]:
    selected = selected_route(candidate_matrix_record)
    route_class = str(selected.get("candidate_route_class"))
    downstream = _downstream(route_class)
    target_id = str(source_record.get("PR154_target_id"))
    compatibility = _compatibility(source_record, route_class)
    return {
        **dict(source_record),
        "final_route_class": route_class,
        "one_final_route_flag": True,
        "record_final_state": downstream["record_final_state"],
        "basis_artifact_refs": list(selected.get("basis_artifact_refs") or []),
        "basis_class": selected.get("basis_class"),
        "route_confidence_class": selected.get("route_confidence_class"),
        "authority_class": selected.get("authority_class"),
        "blocker_class": downstream["blocker_class"],
        "generic_split_reclassification_state_remaining_flag": False,
        "exact_next_action": downstream["exact_next_action"],
        "required_actor": downstream["required_actor"],
        "required_input_artifact": downstream["required_input_artifact"],
        "validator_that_will_unblock": downstream["validator_that_will_unblock"],
        "future_pr_route": downstream["future_pr_route"],
        "risk_if_unresolved": downstream["risk_if_unresolved"],
        "replay_paper_live_implications": "Replay, paper, owner review, connector/runtime gates, and live gates remain future-only.",
        "selection_readiness_impact": downstream["selection_readiness_impact"],
        "trade_context_readiness_impact": downstream["trade_context_readiness_impact"],
        "low_latency_index_impact": downstream["low_latency_index_impact"],
        "quantum_classical_compatibility": compatibility,
        "can_qtt_use_in_scoring_metadata_flag": downstream["can_qtt_use_in_scoring_metadata_flag"],
        "can_qtt_use_in_replay_flag": False,
        "can_qtt_use_in_paper_flag": False,
        "can_qtt_use_in_live_flag": False,
        "source_acceptance_executed_flag": False,
        "source_value_materialized_flag": False,
        "owner_approval_created_flag": False,
        "private_doc_attestation_created_flag": False,
        "exact_agent_id_created_flag": False,
        "connector_semantic_binding_created_flag": False,
        "runtime_receipt_created_flag": False,
        "scoring_ranking_selection_execution_created_flag": False,
        "optimizer_execution_created_flag": False,
        "quantum_backend_execution_created_flag": False,
        "order_fill_profit_authority_created_flag": False,
        "downstream_dependency_ids": list(selected.get("downstream_dependency_ids") or []),
        "route_decision_id": f"PR160_ROUTE_DECISION__{target_id}",
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }


def build_final_decisions(
    source_records: list[Mapping[str, Any]],
    candidate_matrix: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    matrix_by_target = {
        str(item.get("PR154_target_id")): item for item in candidate_matrix
    }
    return [
        final_decision(record, matrix_by_target.get(str(record.get("PR154_target_id")), {}))
        for record in source_records
    ]
