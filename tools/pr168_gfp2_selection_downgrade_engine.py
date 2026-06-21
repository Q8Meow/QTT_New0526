#!/usr/bin/env python3
"""Selection and computability downgrade ledgers for PR168-GFP2."""

from __future__ import annotations

from collections import Counter
from typing import Any


def selection_decision_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_row_key": row["canonical_row_key"],
            "qku_id": row["qku_id"],
            "formula_id": row["formula_id"],
            "selection_state_before_gfp2": row["selection_state_before_gfp2"],
            "selection_state_after_gfp2": row["selection_state_after_gfp2"],
            "selection_decision_reason_code": row["selection_decision_reason_code"],
            "selection_decision_data_provenance_tier": row["selection_decision_data_provenance_tier"],
            "prior_result_supersession_state": row["prior_result_supersession_state"],
            "classification_after_gfp2": row["classification_after_gfp2"],
            "real_positive_claim_allowed_flag": False,
            "real_negative_claim_allowed_flag": False,
            "champion_eligible": False,
            "live_candidate_worthy": False,
            "downstream_repair_route": row["downstream_repair_route"],
            "agent_owner": row["agent_owner"],
            "agent_consumers": row["agent_consumers"],
            "downstream_pr_refs": row["downstream_pr_refs"],
            "validator_refs": row["validator_refs"],
            "test_refs": row["test_refs"],
            "no_orphan_status": row["no_orphan_status"],
            "authority_class": row["authority_class"],
        }
        for row in universe_rows
    ]


def unselected_reopen_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_row_key": row["canonical_row_key"],
            "qku_id": row["qku_id"],
            "formula_id": row["formula_id"],
            "unselected_or_unproven_state": "UNPROVEN_UNSELECTED_PENDING_REAL_DATA_AUDIT",
            "reopen_reason_code": "NO_ACCEPTED_REAL_DATA_PROOF_FOR_SELECTION_OR_REJECTION",
            "requires_real_market_recompute_flag": True,
            "recovery_eligibility_state": row["recovery_eligibility_state"],
            "repair_queue_refs": row["repair_queue_refs"],
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "agent_owner": row["agent_owner"],
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            "authority_class": "UNSELECTED_REOPENED_NOT_REAL_NEGATIVE",
        }
        for row in universe_rows
    ]


def computability_downgrade_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in universe_rows:
        rows.append(
            {
                "canonical_row_key": row["canonical_row_key"],
                "qku_id": row["qku_id"],
                "old_classification": row["old_classification"],
                "new_classification": row["classification_after_gfp2"],
                "downgrade_reason": row["downgrade_reason"],
                "not_permanently_noncomputable_flag": row["classification_after_gfp2"]
                != "STRUCTURALLY_NOT_COMPUTABLE_WITH_PROOF",
                "structural_impossibility_proven_flag": False,
                "recovery_eligibility_state": row["recovery_eligibility_state"],
                "gap_reason_codes": row["gap_reason_codes"],
                "downstream_repair_route": row["downstream_repair_route"],
                "agent_owner": row["agent_owner"],
                "no_orphan_status": row["no_orphan_status"],
            }
        )
    return rows


def selection_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row["classification_after_gfp2"]) for row in rows)
    return {
        "full_universe_discovered_count": len(rows),
        "selected_formula_layer_count": 35,
        "unselected_qku_reopened_count": len(rows),
        "qkus_rejected_before_real_market_proof_count": len(rows),
        "qkus_rejected_because_accepted_real_market_negative_count": 0,
        "qkus_rejected_because_missing_binding_count": len(
            [row for row in rows if "FORMULA_INPUT_BINDING_REPAIR_REQUIRED" in row["gap_reason_codes"]]
        ),
        "qkus_rejected_because_proxy_internal_evidence_count": len(
            [row for row in rows if row["repo_local_generated_flag"]]
        ),
        "qkus_never_executed_count": len([row for row in rows if not row["formula_executed_flag"]]),
        "qkus_structurally_impossible_count": 0,
        "qkus_computable_after_binding_repair_count": counts.get("COMPUTABLE_AFTER_BINDING_REPAIR", 0),
        "qkus_recovery_eligible_count": len(rows),
        "qkus_real_negative_after_recovery_exhaustion_count": 0,
        "classification_counts": dict(counts),
    }
