"""Real computation evidence contract helpers for PR168-GFP."""

from __future__ import annotations

from typing import Any


REQUIRED_COMPUTED_EVIDENCE_FIELDS = [
    "canonical_row_key",
    "formula_id",
    "formula_expression",
    "formula_source_ref",
    "computation_function_path",
    "variable_map",
    "input_values",
    "output_values",
    "execution_adjusted_edge",
    "net_expected_pnl_candidate",
    "lower_confidence_bound_edge",
    "positive_negative_decision",
    "validation_receipt_ref",
]


def classify_computation_evidence(row: dict[str, Any]) -> str:
    status = str(row.get("new_truth_status") or row.get("truth_status") or "")
    computed_status = status in {"COMPUTED_POSITIVE_EDGE", "COMPUTED_NEGATIVE_EDGE", "COMPUTED_NEUTRAL_OR_ZERO_EDGE"}
    missing = missing_computed_evidence_fields(row)
    if computed_status and missing:
        return "INVALID_COMPUTED_STATUS_MISSING_NUMERIC_EVIDENCE"
    if computed_status:
        return status
    if row.get("formula_id") or row.get("required_formula_set_id"):
        return "REAL_FORMULA_ASSIGNED_REPLAY_PAPER_PENDING"
    return "ACTIONABLE_COMPUTATION_GAP"


def missing_computed_evidence_fields(row: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_COMPUTED_EVIDENCE_FIELDS if not _field_present(row, field)]


def build_computation_gap(
    canonical_row_key: str,
    formula_id: str,
    missing_fields: list[str],
    owning_agent: str,
    downstream_route: str,
) -> dict[str, Any]:
    return {
        "canonical_row_key": canonical_row_key,
        "formula_id": formula_id,
        "truth_status": "ACTIONABLE_COMPUTATION_GAP",
        "missing_fields": list(missing_fields),
        "owning_agent": owning_agent,
        "candidate_fill_source_route": "PR168_GFP_FormulaInputRequirementLedger.report.json",
        "input_materialization_route": "PR168-FM",
        "replay_paper_recompute_route": downstream_route,
        "downstream_pr": downstream_route,
        "no_orphan_ref": f"PR168_GFP_NO_ORPHAN::{canonical_row_key}::COMPUTATION_GAP",
    }


def _field_present(row: dict[str, Any], field: str) -> bool:
    value = row.get(field)
    if value is None:
        return False
    if value == "":
        return False
    if isinstance(value, (list, dict)) and not value:
        return False
    return True
