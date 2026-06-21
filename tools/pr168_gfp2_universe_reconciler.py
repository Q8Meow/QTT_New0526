#!/usr/bin/env python3
"""Universe reconciliation rows for PR168-GFP2."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2_constants import BASELINE_COUNTS
from tools.pr168_gfp2_input_loader import GFP2Inputs


def reconciliation_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    actuals = {
        "historical_master_qku_count": len(inputs.qku_coverage),
        "candidate_packet_v1_count": len(inputs.candidate_coverage),
        "atomic_rows_bridge_count": len(inputs.atomicrows_coverage) or len(inputs.atomicrows_records),
        "formula_assignment_count": len(inputs.assignments),
        "selected_formula_count": len(inputs.formulas),
    }
    rows = []
    for name, expected in BASELINE_COUNTS.items():
        actual = actuals[name]
        rows.append(
            {
                "count_name": name,
                "expected_count": expected,
                "actual_count": actual,
                "reconciliation_status": "MATCH" if actual == expected else "MISSING_OR_SUPERSEDED_WITH_EXACT_REASON",
                "missing_or_superseded_count": max(expected - actual, 0),
                "missing_reason": None if actual == expected else "UPSTREAM_COUNT_MISMATCH_REQUIRES_REPAIR",
                "source_refs": _source_refs(name),
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                "agent_owner": "Governance Agent",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def qku_reconciliation_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    return _surface_rows(inputs.qku_coverage, "historical_master_qku_count", "QKU")


def candidate_packet_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    return _surface_rows(inputs.candidate_coverage, "candidate_packet_v1_count", "CandidatePacketV1")


def atomicrows_bridge_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    return _surface_rows(inputs.atomicrows_coverage, "atomic_rows_bridge_count", "AtomicRows")


def _surface_rows(source_rows: list[dict[str, Any]], count_name: str, surface: str) -> list[dict[str, Any]]:
    rows = []
    for row in source_rows:
        rows.append(
            {
                "canonical_row_key": row.get("canonical_row_key"),
                "qku_id": _qku_id(row),
                "surface": surface,
                "count_name": count_name,
                "formula_id": row.get("formula_id"),
                "formula_status": row.get("formula_status"),
                "real_computation_evidence_status": row.get("real_computation_evidence_status"),
                "reconciliation_status": "REOPENED_PENDING_ACCEPTED_REAL_DATA_PROOF",
                "accepted_real_data_proof_flag": False,
                "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
                "agent_owner": row.get("owning_agent") or "Formula Materialization Agent",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def _qku_id(row: dict[str, Any]) -> str:
    key = str(row.get("canonical_row_key") or "")
    return key.removeprefix("QKU::") if key.startswith("QKU::") else key


def _source_refs(name: str) -> list[str]:
    return {
        "historical_master_qku_count": ["PR168_GFP_QKUComputationCoverage.report.json"],
        "candidate_packet_v1_count": ["PR168_GFP_CandidatePacketV1ComputationCoverage.report.json"],
        "atomic_rows_bridge_count": ["PR168_GFP_AtomicRowsComputationCoverage.report.json"],
        "formula_assignment_count": ["PR168_GFP_FormulaAssignmentMatrix.report.json"],
        "selected_formula_count": ["PR168_GFP_SelectedFormulaExpressionRegistry.report.json"],
    }[name]
