#!/usr/bin/env python3
"""Formula provenance rows for PR168-GFP2."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2_input_loader import GFP2Inputs


def selected_formula_provenance(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for formula in sorted(inputs.formulas, key=lambda row: str(row.get("formula_id"))):
        rows.append(
            {
                "formula_id": formula.get("formula_id"),
                "formula_family": formula.get("formula_family"),
                "formula_expression_ref": "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
                "formula_expression_present_flag": bool(formula.get("formula_expression")),
                "formula_source_ref": formula.get("formula_source_ref"),
                "formula_source_class": formula.get("formula_source_class"),
                "source_truth_accepted_flag": bool(formula.get("source_truth_accepted")),
                "source_candidate_flag": not bool(formula.get("source_truth_accepted")),
                "computation_function_path": formula.get("computation_function_path"),
                "computation_function_name": formula.get("computation_function_name"),
                "variable_map_present_flag": bool(formula.get("variable_map")),
                "selected_35_member_flag": True,
                "real_data_proof_created_flag": False,
                "champion_eligible": False,
                "live_candidate_worthy": False,
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                "agent_owner": formula.get("owning_agent") or "Formula Materialization Agent",
                "agent_consumers": ["Replay Paper Recompute Agent", "Ranking Agent"],
                "validator_refs": ["tools/pr168_gfp2_validator.py"],
                "test_refs": ["tests/pr168_gfp2"],
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
                "authority_class": "FORMULA_PROVENANCE_NOT_REAL_DATA_PROOF",
            }
        )
    return rows


def formula_assignment_audit(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in inputs.assignments:
        rows.append(
            {
                "canonical_row_key": row.get("canonical_row_key"),
                "qku_id": _qku_id(row),
                "row_family": row.get("row_family"),
                "formula_id": row.get("formula_id"),
                "required_formula_set_id": row.get("required_formula_set_id"),
                "formula_ids": row.get("formula_ids", []),
                "formula_expression_ref_count": row.get("formula_expression_ref_count"),
                "formula_source_ref_count": row.get("formula_source_ref_count"),
                "variable_map_ref_count": row.get("variable_map_ref_count"),
                "computation_function_path_ref_count": row.get("computation_function_path_ref_count"),
                "formula_join_state": "FORMULA_ASSIGNED_FROM_PR168_GFP",
                "source_report_path": row.get("source_report_path"),
                "source_row_pointer": row.get("source_row_pointer"),
                "selection_state_before_gfp2": "SELECTED_35_FORMULA_LAYER_ONLY",
                "selection_state_after_gfp2": "FULL_UNIVERSE_REOPENED_PENDING_REAL_DATA_PROOF",
                "authority_class": "FORMULA_ASSIGNMENT_AUDIT_NOT_PROOF",
                "owning_agent": row.get("owning_agent") or "Formula Materialization Agent",
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                "validator_refs": ["tools/pr168_gfp2_validator.py"],
                "test_refs": ["tests/pr168_gfp2"],
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def _qku_id(row: dict[str, Any]) -> str:
    key = str(row.get("canonical_row_key") or "")
    if key.startswith("QKU::"):
        return key.removeprefix("QKU::")
    return str(row.get("canonical_row_key") or "UNKNOWN_QKU_ID")
