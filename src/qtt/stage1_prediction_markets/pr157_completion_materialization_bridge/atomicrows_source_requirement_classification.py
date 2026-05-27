"""Deterministic AtomicRows 4183 source-requirement classification."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


FAMILY_PRIMARY_CLASS = {
    "001_signal_features": c.AtomicRowsSourceRequirementClass.FORMULA_ONLY_NO_EXTERNAL_VALUE_REQUIRED,
    "002_scoring_ranking": c.AtomicRowsSourceRequirementClass.OWNER_POLICY_DEFAULT,
    "003_normalization_calibration": (
        c.AtomicRowsSourceRequirementClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS
    ),
    "004_risk_control": c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_OWNER_POLICY,
    "005_execution_connector_boundary": (
        c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_SOURCE_REQUIRED
    ),
    "006_capital_sizing_cash": c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_OWNER_POLICY,
    "007_latency_routing": c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_SOURCE_REQUIRED,
    "008_error_guard_fail_closed": c.AtomicRowsSourceRequirementClass.INTERNAL_CONTROL_PLANE,
    "009_lifecycle_agent_binding": c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED,
    "010_source_evidence_connector_semantic": (
        c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED
    ),
    "011_replay_paper_validation": c.AtomicRowsSourceRequirementClass.OWNER_POLICY_DEFAULT,
    "012_quantum_advisory_optimization": (
        c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY
    ),
    "013_quantum_qubo_ising_metadata": (
        c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY
    ),
    "014_quantum_qaoa_vqe_annealing_metadata": (
        c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY
    ),
    "015_quantum_portfolio_hybrid_comparator": (
        c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY
    ),
}


def classify_primary(row: Mapping[str, Any]) -> str:
    family_id = str(row.get("family_id") or row.get("source_file_family_id") or "")
    return FAMILY_PRIMARY_CLASS.get(
        family_id,
        c.AtomicRowsSourceRequirementClass.UNKNOWN_REQUIRES_TRIAGE,
    ).value


def secondary_tags(row: Mapping[str, Any], primary_class: str) -> list[str]:
    family_id = str(row.get("family_id") or "")
    tags: list[c.AtomicRowsSecondaryTag] = [
        c.AtomicRowsSecondaryTag.prediction_market_specific,
        c.AtomicRowsSecondaryTag.live_gate_future_dependent,
    ]
    if family_id == "001_signal_features":
        tags.extend(
            [
                c.AtomicRowsSecondaryTag.classical_formula,
                c.AtomicRowsSecondaryTag.statistical_edge,
                c.AtomicRowsSecondaryTag.microstructure_alpha,
            ]
        )
    if "scoring" in family_id:
        tags.extend(
            [
                c.AtomicRowsSecondaryTag.classical_algorithm,
                c.AtomicRowsSecondaryTag.optimizer_parameter,
                c.AtomicRowsSecondaryTag.owner_approval_dependent,
            ]
        )
    if "risk" in family_id:
        tags.append(c.AtomicRowsSecondaryTag.risk_parameter)
    if "capital" in family_id:
        tags.append(c.AtomicRowsSecondaryTag.capital_parameter)
    if "execution" in family_id:
        tags.append(c.AtomicRowsSecondaryTag.execution_parameter)
    if "latency" in family_id:
        tags.append(c.AtomicRowsSecondaryTag.latency_parameter)
    if "error_guard" in family_id:
        tags.append(c.AtomicRowsSecondaryTag.error_guard_parameter)
    if primary_class in {
        c.AtomicRowsSourceRequirementClass.PUBLIC_EXTERNAL_SOURCE_REQUIRED.value,
        c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_SOURCE_REQUIRED.value,
    }:
        tags.append(c.AtomicRowsSecondaryTag.source_evidence_dependent)
    if primary_class in {
        c.AtomicRowsSourceRequirementClass.OWNER_POLICY_DEFAULT.value,
        c.AtomicRowsSourceRequirementClass.PARAMETER_RANGE_OWNER_POLICY.value,
        c.AtomicRowsSourceRequirementClass.AGENT_BINDING_REQUIRED.value,
    }:
        tags.append(c.AtomicRowsSecondaryTag.owner_approval_dependent)
    if "replay_paper" in family_id:
        tags.append(c.AtomicRowsSecondaryTag.replay_paper_future_dependent)
    if "normalization" in family_id:
        tags.append(c.AtomicRowsSecondaryTag.cross_venue_normalization_dependent)
    if "quantum" in family_id:
        tags.extend(
            [
                c.AtomicRowsSecondaryTag.quantum_inspired_candidate,
                c.AtomicRowsSecondaryTag.true_quantum_candidate,
            ]
        )
    if "qubo_ising" in family_id:
        tags.extend([c.AtomicRowsSecondaryTag.qubo_compatible, c.AtomicRowsSecondaryTag.ising_compatible])
    if "qaoa_vqe_annealing" in family_id:
        tags.extend(
            [
                c.AtomicRowsSecondaryTag.qaoa_compatible,
                c.AtomicRowsSecondaryTag.vqe_compatible,
                c.AtomicRowsSecondaryTag.annealing_compatible,
            ]
        )
    if "portfolio_hybrid" in family_id:
        tags.extend(
            [
                c.AtomicRowsSecondaryTag.hybrid_classical_quantum_candidate,
                c.AtomicRowsSecondaryTag.quantum_portfolio_optimization_compatible,
            ]
        )
    return sorted({tag.value for tag in tags})


def compatibility_for_row(row: Mapping[str, Any], primary_class: str) -> list[str]:
    family_id = str(row.get("family_id") or "")
    if "qubo_ising" in family_id:
        return [
            c.QuantumClassicalCompatibility.QUBO_COMPATIBLE_METADATA_ONLY.value,
            c.QuantumClassicalCompatibility.ISING_COMPATIBLE_METADATA_ONLY.value,
            c.QuantumClassicalCompatibility.TRUE_QUANTUM_CANDIDATE.value,
        ]
    if "qaoa_vqe_annealing" in family_id:
        return [
            c.QuantumClassicalCompatibility.QAOA_COMPATIBLE_METADATA_ONLY.value,
            c.QuantumClassicalCompatibility.VQE_COMPATIBLE_METADATA_ONLY.value,
            c.QuantumClassicalCompatibility.ANNEALING_COMPATIBLE_METADATA_ONLY.value,
            c.QuantumClassicalCompatibility.TRUE_QUANTUM_CANDIDATE.value,
        ]
    if "portfolio_hybrid" in family_id:
        return [
            c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value,
            c.QuantumClassicalCompatibility.QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_METADATA_ONLY.value,
        ]
    if "quantum" in family_id:
        return [
            c.QuantumClassicalCompatibility.QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE.value,
            c.QuantumClassicalCompatibility.TRUE_QUANTUM_CANDIDATE.value,
        ]
    if primary_class == c.AtomicRowsSourceRequirementClass.FORMULA_ONLY_NO_EXTERNAL_VALUE_REQUIRED.value:
        return [
            c.QuantumClassicalCompatibility.CLASSICAL_FORMULA_COMPATIBLE.value,
            c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value,
        ]
    if any(token in family_id for token in ("risk", "capital", "execution", "latency")):
        return [c.QuantumClassicalCompatibility.RISK_CAPITAL_EXECUTION_FORMULA_COMPATIBLE.value]
    if "scoring" in family_id:
        return [c.QuantumClassicalCompatibility.CLASSICAL_TRADING_ALGORITHM_COMPATIBLE.value]
    if "signal" in family_id:
        return [
            c.QuantumClassicalCompatibility.STATISTICAL_EDGE_COMPATIBLE.value,
            c.QuantumClassicalCompatibility.MICROSTRUCTURE_ALPHA_COMPATIBLE.value,
        ]
    return [c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value]
