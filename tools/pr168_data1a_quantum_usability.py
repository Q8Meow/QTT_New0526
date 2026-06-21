#!/usr/bin/env python3
"""Quantum-forward usability audit for PR168-DATA1A."""

from __future__ import annotations

from typing import Any

from tools.pr168_data1a_config import generated_ref, report_path, route_defaults


def build_quantum_usability(context: dict[str, Any], created_at_utc: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_rows = context["reports"].get("PR168_DATA1_QuantumForwardCoefficientFeatureSurface", {}).get("records", [])
    if not isinstance(source_rows, list):
        source_rows = []
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(source_rows, start=1):
        penalty_gap = bool(source.get("penalty_scaling_gap_flag"))
        interpret_gap = not bool(source.get("interpret_back_map_source_ref"))
        comparator_gap = not bool(source.get("classical_comparator_required_flag"))
        if penalty_gap:
            classification = "QUANTUM_FORWARD_PARTIAL_MISSING_COEFFICIENTS"
        elif interpret_gap:
            classification = "QUANTUM_FORWARD_PARTIAL_MISSING_INTERPRET_BACK"
        elif comparator_gap:
            classification = "QUANTUM_FORWARD_BLOCKED_NO_CLASSICAL_COMPARATOR"
        else:
            classification = "QUANTUM_FORWARD_DATA_READY_CANDIDATE"
        rows.append(
            {
                "quantum_usability_row_id": f"quantum_usability_{index:05d}",
                "quantum_feature_vector_id": source.get("quantum_feature_vector_id"),
                "candidate_stack_binary_variable_universe": source.get("candidate_stack_binary_variable_universe", []),
                "binary_decision_variable_identity": source.get("candidate_stack_binary_variable_universe", []),
                "alpha_expected_value_proxy_source_ref": source.get("alpha_coefficient_data_source", []),
                "cost_TCA_coefficient_source_ref": source.get("cost_coefficient_data_source", []),
                "capacity_depth_constraint_source_ref": source.get("capacity_constraint_data_source", []),
                "liquidity_spread_constraint_source_ref": source.get("liquidity_constraint_data_source", []),
                "event_family_concentration_penalty_source_ref": source.get("concentration_penalty_data_source", []),
                "latency_staleness_penalty_source_ref": source.get("latency_penalty_data_source", []),
                "FDR_trial_family_penalty_source_ref": source.get("fdr_penalty_data_source", []),
                "no_trade_comparator_source_ref": source.get("no_trade_constraint_data_source", []),
                "interpret_back_map_source_ref": source.get("interpret_back_map_source_ref"),
                "classical_fallback_source_ref": source.get("classical_fallback_required_flag"),
                "penalty_scaling_source_or_gap": "MISSING_PENALTY_SCALING_SOURCE" if penalty_gap else "DATA1_SOURCE_PRESENT",
                "quantum_readiness_classification": classification,
                "mapping_readiness": source.get("mapping_readiness"),
                "downstream_mapping_route": [
                    "PR162E-Q quantum automapper",
                    "PR166-Q quantum/classical comparator",
                    "PR166-QB bounded optimizer benchmark",
                    "PR166-QC quantum-selected replay/paper retest",
                    "PR168-GFP2R",
                    "PR168-RP2",
                    "PR168-RANK2",
                ],
                "quantum_backend_execution_flag": False,
                "quantum_advantage_claim_flag": False,
                "created_at_utc": created_at_utc,
                **route_defaults("quantum", data1_refs=[generated_ref(report_path("PR168_DATA1_QuantumForwardCoefficientFeatureSurface"))]),
            }
        )
    summary = {
        "quantum_feature_vector_count": len(rows),
        "candidate_stack_binary_variable_count": sum(len(row["candidate_stack_binary_variable_universe"]) for row in rows),
        "alpha_coefficient_data_source_count": sum(bool(row["alpha_expected_value_proxy_source_ref"]) for row in rows),
        "cost_coefficient_data_source_count": sum(bool(row["cost_TCA_coefficient_source_ref"]) for row in rows),
        "capacity_constraint_data_source_count": sum(bool(row["capacity_depth_constraint_source_ref"]) for row in rows),
        "liquidity_constraint_data_source_count": sum(bool(row["liquidity_spread_constraint_source_ref"]) for row in rows),
        "correlation_penalty_data_source_count": sum(bool(source.get("correlation_penalty_data_source")) for source in source_rows),
        "concentration_penalty_data_source_count": sum(bool(row["event_family_concentration_penalty_source_ref"]) for row in rows),
        "latency_penalty_data_source_count": sum(bool(row["latency_staleness_penalty_source_ref"]) for row in rows),
        "fdr_penalty_data_source_count": sum(bool(row["FDR_trial_family_penalty_source_ref"]) for row in rows),
        "no_trade_constraint_data_source_count": sum(bool(row["no_trade_comparator_source_ref"]) for row in rows),
        "penalty_scaling_gap_count": sum(row["penalty_scaling_source_or_gap"] == "MISSING_PENALTY_SCALING_SOURCE" for row in rows),
        "interpret_back_gap_count": sum(not row["interpret_back_map_source_ref"] for row in rows),
        "classical_fallback_available_flag": all(bool(row["classical_fallback_source_ref"]) for row in rows) if rows else False,
        "classical_comparator_available_flag": all(bool(source.get("classical_comparator_required_flag")) for source in source_rows) if source_rows else False,
        "quantum_forward_data_ready_candidate_count": sum(row["quantum_readiness_classification"] == "QUANTUM_FORWARD_DATA_READY_CANDIDATE" for row in rows),
        "quantum_forward_partial_count": sum("PARTIAL" in row["quantum_readiness_classification"] for row in rows),
        "quantum_backend_execution_flag": False,
        "quantum_advantage_claim_flag": False,
        **route_defaults("quantum", data1_refs=[generated_ref(report_path("PR168_DATA1_QuantumForwardCoefficientFeatureSurface"))]),
    }
    return summary, rows
