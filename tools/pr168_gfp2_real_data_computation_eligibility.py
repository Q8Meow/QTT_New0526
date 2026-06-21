#!/usr/bin/env python3
"""Accepted-real-data proof eligibility for PR168-GFP2."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2_constants import REAL_PROOF_COMPONENTS
from tools.pr168_gfp2_input_loader import GFP2Inputs, rp_negative_by_key


def computation_eligibility_rows(inputs: GFP2Inputs) -> list[dict[str, Any]]:
    negatives = rp_negative_by_key(inputs)
    rows: list[dict[str, Any]] = []
    for assignment in inputs.assignments:
        key = str(assignment.get("canonical_row_key"))
        old_executed = key in negatives
        missing = list(REAL_PROOF_COMPONENTS)
        if assignment.get("formula_id"):
            missing = [item for item in missing if item != "formula_expression_ref"]
        rows.append(
            {
                "canonical_row_key": key,
                "qku_id": _qku_id(assignment),
                "formula_id": assignment.get("formula_id"),
                "accepted_real_data_available_flag": False,
                "accepted_real_data_refs": [],
                "accepted_source_evidence_refs": [],
                "market_data_asof": None,
                "replay_lock_ref": None,
                "formula_executed_flag": old_executed,
                "formula_execution_receipt_ref": negatives.get(key, {}).get("result_ref"),
                "all_required_inputs_available_flag": False,
                "all_required_cost_fill_latency_capacity_inputs_available_flag": False,
                "synthetic_proxy_candidate_component_present_flag": old_executed,
                "proof_eligible_flag": False,
                "proof_block_reason_codes": [
                    "ACCEPTED_REAL_MARKET_DATA_ABSENT",
                    "PRODUCTION_ACCEPTED_SOURCE_EVIDENCE_ABSENT",
                    "REAL_DATA_PROOF_COMPONENTS_INCOMPLETE",
                ],
                "missing_proof_components": missing,
                "real_positive_claim_allowed_flag": False,
                "real_negative_claim_allowed_flag": False,
                "zero_positive_final_truth_allowed_flag": False,
                "downstream_repair_route": "PR168-RP2",
                "agent_owner": assignment.get("owning_agent") or "Formula Materialization Agent",
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            }
        )
    return rows


def _qku_id(row: dict[str, Any]) -> str:
    key = str(row.get("canonical_row_key") or "")
    return key.removeprefix("QKU::") if key.startswith("QKU::") else key
