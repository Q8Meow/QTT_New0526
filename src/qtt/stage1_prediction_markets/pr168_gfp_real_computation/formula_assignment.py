"""Formula-family derivation and row assignment for PR168-GFP."""

from __future__ import annotations

from typing import Any

from .formula_discovery import REQUIRED_FORMULA_SETS, formula_by_id, required_formula_set_records


PREDICTION_MARKET_SET = "PR168_GFP_RFS_TRADABLE_BINARY_CONTRACT_MINIMUM"
EXECUTION_SET = "PR168_GFP_RFS_EXECUTION_TCA"
PORTFOLIO_SET = "PR168_GFP_RFS_PORTFOLIO_RISK"
VALIDATION_SET = "PR168_GFP_RFS_VALIDATION_MEMORY"
QUANTUM_SET = "PR168_GFP_RFS_QUANTUM_OBJECTIVE_WITH_CLASSICAL_FALLBACK"


def derive_required_formula_set_ids(row: dict[str, Any]) -> list[str]:
    row_family = str(row.get("qku_family") or row.get("row_family") or row.get("source_row_class") or "")
    market = str(row.get("qku_market_primary") or row.get("market_type") or row.get("market_type_applicability_metadata_only") or "")
    quantum = str(row.get("qku_quantum_applicability") or row.get("quantum_applicability_metadata_class") or row.get("source_quantum_metadata_class") or "")
    algorithm = str(row.get("qku_algorithm_family") or row.get("optimizer_family_if_available") or "")
    normalized = " ".join([row_family, market, quantum, algorithm]).upper()

    set_ids: list[str] = []
    if "PREDICTION_MARKET" in normalized:
        set_ids.append(PREDICTION_MARKET_SET)
    if any(token in normalized for token in ["LATENCY", "EXECUTION", "FILL", "QUEUE", "TCA"]):
        set_ids.append(EXECUTION_SET)
    if any(token in normalized for token in ["RISK", "CAPITAL", "PORTFOLIO", "CROWDING", "CAPACITY"]):
        set_ids.append(PORTFOLIO_SET)
    if any(token in normalized for token in ["QUANTUM", "QAOA", "VQE", "ANNEALING", "QUBO", "ISING", "BQM", "CQM", "DQM"]):
        set_ids.append(QUANTUM_SET)
    if any(token in normalized for token in ["FORMULA", "ALGORITHM", "STRATEGY", "CONSTRAINT", "PARAMETER", "AGENT_CONSUMPTION"]):
        set_ids.append(VALIDATION_SET)
    if not set_ids:
        set_ids.append(VALIDATION_SET)
    return _dedupe(set_ids)


def formula_ids_for_sets(required_formula_set_ids: list[str]) -> list[str]:
    formula_ids: list[str] = []
    for set_id in required_formula_set_ids:
        formula_ids.extend(REQUIRED_FORMULA_SETS[set_id]["formula_ids"])
    return _dedupe(formula_ids)


def formula_families_for_ids(formula_ids: list[str]) -> list[str]:
    formulas = formula_by_id()
    return [str(formulas[formula_id]["formula_family"]) for formula_id in formula_ids]


def assignment_for_row(canonical_row_key: str, row: dict[str, Any], source_row_pointer: str, row_family: str) -> dict[str, Any]:
    set_ids = derive_required_formula_set_ids(row)
    formula_ids = formula_ids_for_sets(set_ids)
    formulas = formula_by_id()
    primary_set_id = set_ids[0]
    return {
        "canonical_row_key": canonical_row_key,
        "row_family": row_family,
        "source_report_path": source_row_pointer.split("#", 1)[0],
        "source_row_pointer": source_row_pointer,
        "formula_id": formula_ids[0],
        "required_formula_set_id": primary_set_id,
        "required_formula_set_ids": set_ids,
        "formula_ids": formula_ids,
        "formula_families_required": formula_families_for_ids(formula_ids),
        "formula_proof_ref": "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
        "required_formula_set_proof_ref": "docs/master_plan/generated/PR168_GFP_RequiredFormulaSetMap.report.json",
        "formula_expression_ref_count": len([formula_id for formula_id in formula_ids if formulas[formula_id].get("formula_expression")]),
        "formula_source_ref_count": len([formula_id for formula_id in formula_ids if formulas[formula_id].get("formula_source_ref")]),
        "variable_map_ref_count": len([formula_id for formula_id in formula_ids if formulas[formula_id].get("variable_map")]),
        "computation_function_path_ref_count": len([formula_id for formula_id in formula_ids if formulas[formula_id].get("computation_function_path")]),
        "formula_status": "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING",
        "real_computation_evidence_status": "NOT_COMPUTED_NUMERIC_INPUTS_MISSING_OR_REPLAY_PAPER_PENDING",
        "new_truth_status": "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING",
        "owning_agent": _owning_agent(row, set_ids),
        "downstream_route": _downstream_route(set_ids),
        "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::{canonical_row_key}",
    }


def required_formula_set_map_with_family_refs() -> list[dict[str, Any]]:
    return required_formula_set_records()


def _owning_agent(row: dict[str, Any], set_ids: list[str]) -> str:
    if QUANTUM_SET in set_ids:
        return "Quantum AutoMapper Agent"
    if EXECUTION_SET in set_ids:
        return "Execution/TCA Agent"
    if PORTFOLIO_SET in set_ids:
        return "Portfolio/Risk Agent"
    if PREDICTION_MARKET_SET in set_ids:
        return "Formula Materialization Agent"
    return "Algorithm Materialization Agent"


def _downstream_route(set_ids: list[str]) -> str:
    if QUANTUM_SET in set_ids:
        return "PR166-QC-R2"
    if PREDICTION_MARKET_SET in set_ids:
        return "PR168-RP"
    if PORTFOLIO_SET in set_ids or VALIDATION_SET in set_ids:
        return "PR168-RANK"
    return "PR168-RP"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
