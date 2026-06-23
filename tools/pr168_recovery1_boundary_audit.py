#!/usr/bin/env python3
"""Computability, agent-consumability, and launch-readiness boundary audits."""

from __future__ import annotations

from typing import Any, Mapping


BOUNDARY_STATEMENT = (
    "Recovery1 produced 35 improved non-proof retest/stack rows, not 35 new formulas. "
    "Of those, 32 remain no-trade-dominated and 3 are recovered candidates for "
    "RP5/RANK4/QOPT1. These rows are replay/paper-agent-consumable only and are "
    "not live-trading-ready."
)


def build_boundary_audits(shards: Mapping[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    improved_rows = list(shards.get("improved_candidate", []))
    delta_rows = list(shards.get("before_after_delta", []))
    expression_rows = list(shards.get("expression_repair", []))
    source_rows = list(shards.get("source_provenance", []))
    handoff_rows = list(shards.get("downstream_handoff", []))

    improved_count = len(improved_rows)
    no_trade_dominated_count = sum(1 for row in delta_rows if row.get("still_no_trade_dominated_flag_non_proof"))
    recovered_count = sum(1 for row in delta_rows if row.get("candidate_recovered_flag_non_proof"))
    expression_count = len(expression_rows)
    source_candidate_count = sum(
        1
        for row in source_rows
        if row.get("candidate_only_flag") is True and row.get("accepted_truth_flag") is False
    )
    formula_ids = sorted({str(row.get("formula_id")) for row in expression_rows if row.get("formula_id")})
    recovered_candidate_refs = [
        row.get("after_row_ref")
        for row in improved_rows
        if row.get("downstream_route") == "PR168-RP5-RANK4-QOPT1"
    ]
    improved_evidence_refs = [row.get("after_row_ref") for row in improved_rows if row.get("after_row_ref")]
    authority_counts = _authority_counts(improved_rows + delta_rows + expression_rows + source_rows + handoff_rows)

    shared = {
        "boundary_statement": BOUNDARY_STATEMENT,
        "improved_non_proof_retest_stack_row_count": improved_count,
        "improved_rows_are_repaired_retested_stack_rows_flag": True,
        "improved_rows_are_new_formula_rows_flag": False,
        "new_formula_claim_proven_flag": False,
        "new_formula_count": 0,
        "new_canonical_formula_ids": [],
        "new_canonical_formula_id_count": 0,
        "expression_repair_count": expression_count,
        "expression_repairs_are_existing_formula_repairs_flag": True,
        "expression_repaired_existing_formula_ids": formula_ids,
        "source_provenance_candidate_usable_count": source_candidate_count,
        "source_provenance_rows_are_source_truth_flag": False,
        "still_no_trade_dominated_improved_row_count": no_trade_dominated_count,
        "recovered_candidate_count": recovered_count,
        "recovered_candidate_refs": recovered_candidate_refs,
        "replay_paper_agent_consumable_row_count": improved_count,
        "live_trading_ready_row_count": 0,
        "live_trading_ready_flag": False,
        "order_authority_created_count": authority_counts["order_authority_created_count"],
        "champion_allowed_count": authority_counts["champion_allowed_count"],
        "live_candidate_allowed_count": authority_counts["live_candidate_allowed_count"],
        "source_truth_acceptance_created_count": authority_counts["source_truth_acceptance_created_count"],
        "candidate_only_flag": True,
        "accepted_truth_flag": False,
        "not_real_profit_proof_flag": True,
        "manual_operator_review_before_live_required_flag": True,
        "RP5_RANK4_QOPT1_replay_paper_route_only_flag": True,
        "no_live_order_or_champion_authority_created_flag": True,
        "improved_evidence_refs": improved_evidence_refs,
    }
    return {
        "computability": {
            **shared,
            "computability_audit_state": "COMPUTABLE_REPAIRED_RETESTED_STACK_ROWS_NON_PROOF",
            "computable_repaired_retested_stack_row_count": improved_count,
            "computable_new_formula_row_count": 0,
            "computable_existing_formula_repair_count": expression_count,
            "computability_boundary_reason": (
                "Improved rows are stack/retest outputs derived from changed TCA/order-size inputs; "
                "the expression lane repaired existing formula records and did not mint canonical formula IDs."
            ),
        },
        "agent_consumable_formula": {
            **shared,
            "agent_consumability_state": "REPLAY_PAPER_AGENT_CONSUMABLE_NON_PROOF_ONLY",
            "agent_consumable_stack_evidence_count": improved_count,
            "agent_consumable_existing_formula_repair_count": expression_count,
            "agent_consumable_new_formula_count": 0,
            "agent_consumable_source_candidate_count": source_candidate_count,
            "formula_consumability_boundary_reason": (
                "Recovery1 exposes existing repaired formulas and candidate source mappings to downstream agents; "
                "it does not create source-truth or live formula authority."
            ),
        },
        "launch_readiness": {
            **shared,
            "launch_readiness_state": "NOT_LIVE_READY_REPLAY_PAPER_ONLY",
            "paper_or_replay_ready_non_proof_count": recovered_count,
            "live_ready_count": 0,
            "future_live_gate_required_flag": True,
            "launch_readiness_boundary_reason": (
                "Recovered candidates can seed RP5/RANK4/QOPT1 replay or paper workflows only. "
                "No Recovery1 artifact may bypass no-trade, proof, live, order, or source-truth gates."
            ),
        },
    }


def _authority_counts(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    fields = {
        "order_authority_created_count": (
            "order_authority_created_flag",
            "live_order_authority_flag",
            "live_order_receipt_created_flag",
        ),
        "champion_allowed_count": ("champion_allowed_flag",),
        "live_candidate_allowed_count": ("live_candidate_allowed_flag", "live_authority_created_flag"),
        "source_truth_acceptance_created_count": (
            "source_truth_acceptance_created_flag",
            "source_truth_accepted_flag",
            "accepted_truth_flag",
        ),
    }
    return {
        count_name: sum(1 for row in rows for flag in flags if row.get(flag) is True)
        for count_name, flags in fields.items()
    }
