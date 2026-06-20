#!/usr/bin/env python3
"""Centralized authority and PR168-RP reason-code registry."""

from __future__ import annotations

from pathlib import Path


AUTHORITY_BOUNDARY_CODES: dict[str, dict[str, object]] = {
    "NO_LIVE_ORDER_AUTHORITY": {
        "description": "No real order submission, cancellation, reduction, close, or release is created.",
        "live_authority": False,
        "order_authority": False,
    },
    "NO_SOURCE_TRUTH_AUTHORITY": {
        "description": "External and prior values remain candidate or replay-paper evidence, not accepted source truth.",
        "source_truth_authority": False,
    },
    "NO_CONNECTOR_TRUTH_OR_BINDING": {
        "description": "Connector route metadata may be created, but semantic binding and connector truth are not.",
        "connector_truth_authority": False,
        "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
    },
    "NO_PRIVATE_STATE_OR_CASH": {
        "description": "Private state, account state, and cash handling are outside this PR.",
        "private_state_authority": False,
        "cash_authority": False,
    },
    "NO_QUANTUM_BACKEND_EXECUTION": {
        "description": "Quantum rows may be structurally mapped and classically evaluated only.",
        "quantum_backend_execution": False,
        "quantum_advantage_claim": False,
    },
    "NO_LLM_HOT_PATH_AUTHORITY": {
        "description": "LLMs may not accept sources, rewrite results, or release orders on any hot path.",
        "llm_hot_path_authority": False,
    },
    "NO_QTT_DIGEST_AUTHORITY": {
        "description": "PR168-RP does not create QTT freeze, checksum, or global digest authority.",
        "generated_digest_authority": False,
    },
    "NO_ATOMICROWS_DIGEST_AUTHORITY": {
        "description": "PR168-RP does not create AtomicRows digest authority.",
        "generated_digest_authority": False,
    },
    "LIVE_CANDIDATE_HANDOFF_ONLY": {
        "description": "LIVE_CANDIDATE packets are future handoff records and require a later execution-router gate.",
        "live_authority": False,
        "execution_router_required_future_gate": True,
    },
}

GAP_REASON_CODES: dict[str, dict[str, object]] = {
    "MISSING_NUMERIC_INPUTS": {"critical": True, "downstream_route": "PR168_RP_ActionableInputGapQueue.report.json"},
    "MISSING_DEFAULT_THRESHOLD": {"critical": True, "downstream_route": "PR168_RP_MissingDefaultResolutionQueue.report.json"},
    "MISSING_MICROSTRUCTURE_INPUTS": {"critical": True, "downstream_route": "PR168_RP_MissingValueCandidateFillQueue.report.json"},
    "MISSING_QUANTUM_COEFFICIENT_MAP": {"critical": True, "downstream_route": "PR168_RP_QuantumCoefficientMapInputGaps.report.json"},
    "MISSING_AGENT_DUTY_SOURCE": {"critical": True, "downstream_route": "PR168_RP_AgentDutySourceGapQueue.report.json"},
    "MISSING_CONNECTOR_ROUTE_TARGET": {"critical": False, "downstream_route": "PR168_RP_ConnectorCandidateRouteMap.report.json"},
    "TERMINAL_NON_TRADING_FORMULA": {"critical": False, "downstream_route": "PR168_RP_To_OwnerDashboardComputedTruth.report.json"},
}

NEGATIVE_RECOVERY_REASON_CODES: dict[str, dict[str, object]] = {
    "prediction_wrong_or_uncalibrated": {"repair_stage": "probability_calibration_repair"},
    "market_implied_probability_too_high": {"repair_stage": "input_repair"},
    "spread_cost_exceeds_edge": {"repair_stage": "microstructure_repair"},
    "slippage_cost_exceeds_edge": {"repair_stage": "microstructure_repair"},
    "market_impact_exceeds_edge": {"repair_stage": "size_capacity_repair"},
    "adverse_selection_exceeds_edge": {"repair_stage": "microstructure_repair"},
    "implementation_shortfall_exceeds_edge": {"repair_stage": "microstructure_repair"},
    "fill_probability_too_low": {"repair_stage": "order_policy_repair"},
    "partial_fill_residual_risk_high": {"repair_stage": "order_policy_repair"},
    "stale_orderbook_risk_high": {"repair_stage": "timing_regime_repair"},
    "latency_decay_exceeds_edge": {"repair_stage": "timing_regime_repair"},
    "capacity_crowding_exceeds_edge": {"repair_stage": "size_capacity_repair"},
    "overfit_fdr_penalty_exceeds_edge": {"repair_stage": "overfit_retest_repair"},
    "portfolio_marginal_utility_negative": {"repair_stage": "portfolio_repair"},
    "no_trade_candidate_dominates": {"repair_stage": "order_policy_repair"},
    "scenario_ladder_failure": {"repair_stage": "scenario_repair"},
    "order_policy_failure": {"repair_stage": "order_policy_repair"},
    "regime_specific_failure": {"repair_stage": "timing_regime_repair"},
    "quantum_coefficient_map_missing": {"repair_stage": "quantum_structural_gap"},
    "formula_inputs_missing": {"repair_stage": "input_repair"},
    "data_default_missing": {"repair_stage": "default_resolution"},
    "source_candidate_needed": {"repair_stage": "external_candidate_research"},
    "terminal_non_trading_formula": {"repair_stage": "terminal_classification"},
}

PRETRADE_DECISION_REASON_CODES: dict[str, dict[str, object]] = {
    "NO_TRADE_BASELINE_REQUIRED": {"decision_status": "NO_TRADE_CANDIDATE_REQUIRED"},
    "NO_TRADE_DOMINATES": {"decision_status": "PRETRADE_NO_TRADE_DOMINATES"},
    "LATENCY_BUDGET_FAIL": {"decision_status": "PRETRADE_INPUT_GAP_OR_FAIL"},
    "SCENARIO_LADDER_FAIL": {"decision_status": "PRETRADE_INPUT_GAP_OR_FAIL"},
    "CAPACITY_FAIL": {"decision_status": "PRETRADE_INPUT_GAP_OR_FAIL"},
    "LCB_NOT_POSITIVE": {"decision_status": "PRETRADE_INPUT_GAP_OR_FAIL"},
    "AUTHORITY_BOUNDARY_FAIL": {"decision_status": "PRETRADE_BLOCKED_BY_AUTHORITY"},
    "FUTURE_LIVE_GATE_REQUIRED": {"decision_status": "LIVE_CANDIDATE_HANDOFF_ONLY_NOT_ORDER_AUTHORITY"},
}

_SCATTERED_AUTHORITY_TEXT = (
    "submit real orders",
    "source truth accepted",
    "connector truth accepted",
    "quantum advantage proven",
    "live promotion ready",
    "order ready",
)


def get_authority_boundary_code(code: str) -> dict[str, object]:
    return _lookup(AUTHORITY_BOUNDARY_CODES, code, "authority boundary")


def get_gap_reason_code(code: str) -> dict[str, object]:
    return _lookup(GAP_REASON_CODES, code, "gap reason")


def get_negative_recovery_reason_code(code: str) -> dict[str, object]:
    return _lookup(NEGATIVE_RECOVERY_REASON_CODES, code, "negative recovery reason")


def get_pretrade_decision_reason_code(code: str) -> dict[str, object]:
    return _lookup(PRETRADE_DECISION_REASON_CODES, code, "pretrade decision reason")


def validate_no_scattered_authority_wording(path: str) -> dict[str, object]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    findings = [
        {"term": term, "path": file_path.as_posix()}
        for term in _SCATTERED_AUTHORITY_TEXT
        if term.lower() in text.lower()
    ]
    return {
        "path": file_path.as_posix(),
        "scattered_authority_wording_count": len(findings),
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }


def all_reason_code_names() -> set[str]:
    return set().union(
        AUTHORITY_BOUNDARY_CODES,
        GAP_REASON_CODES,
        NEGATIVE_RECOVERY_REASON_CODES,
        PRETRADE_DECISION_REASON_CODES,
    )


def _lookup(registry: dict[str, dict[str, object]], code: str, label: str) -> dict[str, object]:
    try:
        return registry[code]
    except KeyError as exc:
        raise KeyError(f"unknown {label} code: {code}") from exc
