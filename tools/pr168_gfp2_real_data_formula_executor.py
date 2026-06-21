#!/usr/bin/env python3
"""Deterministic real-data execution ledger for PR168-GFP2."""

from __future__ import annotations

from typing import Any


def real_data_formula_execution_rows(eligibility_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in eligibility_rows:
        eligible = bool(row.get("proof_eligible_flag"))
        rows.append(
            {
                "canonical_row_key": row.get("canonical_row_key"),
                "qku_id": row.get("qku_id"),
                "formula_id": row.get("formula_id"),
                "formula_executed_flag": False,
                "formula_execution_context": "ACCEPTED_REAL_DATA_PROOF_LANE",
                "formula_execution_receipt_ref": None,
                "execution_status": "NOT_EXECUTED_ACCEPTED_REAL_DATA_MISSING"
                if not eligible
                else "READY_FOR_DETERMINISTIC_REAL_DATA_EXECUTION",
                "numeric_evidence_values": {},
                "numeric_evidence_refs": [],
                "data_provenance_receipt_ref": None,
                "proof_eligible_flag": eligible,
                "real_positive_claim_allowed_flag": False,
                "real_negative_claim_allowed_flag": False,
                "downstream_repair_route": "PR168-RP2",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows
