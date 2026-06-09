"""Outcome attribution rows for PR165-B."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref
from .negative_memory_reason_codes import COUNTERFACTUAL_ATTRIBUTION_FAMILIES


def _normalised_weights(raw: dict[str, float]) -> dict[str, float]:
    values = {key: max(0.0, float(raw.get(key, 0.0))) for key in COUNTERFACTUAL_ATTRIBUTION_FAMILIES}
    total = sum(values.values())
    if total <= 0.0:
        values["sparse_regime_uncertainty"] = 1.0
        total = 1.0
    rounded: dict[str, float] = {}
    running = 0.0
    keys = list(COUNTERFACTUAL_ATTRIBUTION_FAMILIES)
    for key in keys[:-1]:
        value = round(values[key] / total, 6)
        rounded[key] = value
        running += value
    rounded[keys[-1]] = round(1.0 - running, 6)
    return rounded


def build_outcome_attribution_record(
    index: int,
    ctx: dict[str, Any],
    condition_id: str,
    combination_id: str,
    classification: dict[str, Any],
) -> dict[str, Any]:
    tca = ctx["tca"]
    decomp = ctx["components"].get("score_decomposition", {})
    quantum = ctx["quantum"]
    raw = {
        "fees": tca.get("fee_cost", 0.0),
        "spread": tca.get("spread_cost", 0.0),
        "slippage": tca.get("slippage_cost", 0.0),
        "latency_adverse_selection": tca.get("latency_adverse_selection_cost", 0.0),
        "queue_nonfill": tca.get("queue_nonfill_opportunity_cost", 0.0),
        "maker_taker_route_error": max(0.0, 100.0 - float(decomp.get("maker_taker_route_score", 80.0))) / 100.0,
        "liquidity_depth": max(0.0, 100.0 - float(ctx["liquidity"].get("liquidity_fill_probability_score", 80.0))) / 100.0,
        "time_to_resolution": 0.03,
        "settlement_delay": tca.get("settlement_delay_penalty", 0.0),
        "stale_data": tca.get("stale_data_penalty", 0.0),
        "probability_calibration": max(0.0, 100.0 - float(decomp.get("probability_calibration_score", 80.0))) / 100.0,
        "replay_paper_divergence": float(ctx["divergence"].get("divergence_penalty", 0.0)) / 100.0,
        "stress_failure": max(0.0, 100.0 - float(ctx["stress"].get("scenario_stress_robustness_score", 85.0))) / 100.0,
        "model_risk": float(ctx["model_risk"].get("model_risk_penalty", 0.0)) / 100.0,
        "source_provenance": float(ctx["provenance"].get("source_candidate_penalty", 0.0)) / 10.0,
        "repair_confidence": max(0.0, 1.0 - float(ctx["repair_confidence"].get("repair_confidence_score", 0.8))),
        "formula_complexity": float(decomp.get("complexity_penalty", 0.0)) / 100.0,
        "portfolio_crowding": float(decomp.get("concentration_crowding_penalty", 0.0)),
        "duplicate_edge": float(decomp.get("portfolio_duplicate_edge_penalty", 0.0)),
        "yes_no_complement_inconsistency": 0.20 if classification["memory_classification"] == "YES_NO_COMPLEMENT_INCONSISTENT" else 0.0,
        "capital_lock": tca.get("capital_lock_penalty", 0.0),
        "false_discovery_adjustment": 0.18 if classification["memory_classification"] == "FALSE_DISCOVERY_RISK_WATCH" else 0.0,
        "sparse_regime_uncertainty": 0.18 if classification["memory_classification"] in {"SPARSE_REGIME_WATCH", "NEUTRAL_INSUFFICIENT_EVIDENCE"} else 0.0,
        "quantum_objective_gap": 0.12 if classification["memory_classification"] == "QUANTUM_FORMULATION_WEAK" else 0.0,
        "quantum_constraint_gap": 0.05 if quantum.get("constraint_set_materialized") is False else 0.0,
        "quantum_penalty_model_gap": 0.06 if quantum.get("penalty_model_materialized") is False else 0.0,
        "quantum_binary_expansion_gap": 0.06 if not quantum.get("binary_expansion_plan_ref") else 0.0,
        "quantum_classical_comparator_gap": 0.12 if classification["memory_classification"] == "QUANTUM_CLASSICAL_COMPARATOR_WEAK" else 0.0,
    }
    weights = _normalised_weights(raw)
    return {
        "outcome_attribution_ref": ordinal_ref("PR165_B_OUTCOME_ATTRIBUTION", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": condition_id,
        "combination_fingerprint_id": combination_id,
        "memory_classification": classification["memory_classification"],
        "attribution_weights": weights,
        "attribution_weight_sum": round(sum(weights.values()), 6),
        "dominant_attribution_family": max(weights, key=weights.get),
        "reason_codes": classification["reason_codes"],
        "validation_status": "PASS",
    }
