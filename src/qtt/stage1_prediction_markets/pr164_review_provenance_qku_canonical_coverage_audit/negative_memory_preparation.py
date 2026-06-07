"""PR165-B negative-memory condition preparation."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import candidate_index, plain_ref


def build_negative_memory_rows(
    evidence_rows: list[dict[str, Any]],
    tca_by_candidate: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(evidence_rows, 1):
        cid = row["candidate_id"]
        idx = candidate_index(cid)
        tca = tca_by_candidate.get(cid, {})
        rows.append(
            {
                "negative_memory_preparation_ref": plain_ref("NEG_MEM", index),
                "candidate_id": cid,
                "qku_ids": row["qku_ids"],
                "condition_fingerprint": f"PR164_CONDITION_FINGERPRINT::{idx:06d}::market={tca.get('market_scope', 'UNKNOWN')}::venue={tca.get('venue_scope', 'SYNTHETIC')}",
                "qku_formula_algorithm_stack_id": f"PR164_STACK::{idx:06d}",
                "market_condition_bucket": tca.get("market_scope", "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW"),
                "venue_condition_bucket": tca.get("venue_scope", "SYNTHETIC_REPLAY_PAPER"),
                "liquidity_bucket": _bucket(float(tca.get("paper_liquidity_impact_candidate", 0.0))),
                "latency_bucket": _bucket(float(tca.get("paper_latency_cost_candidate", 0.0))),
                "fee_slippage_bucket": _bucket(float(tca.get("paper_fees", 0.0)) + float(tca.get("paper_slippage", 0.0))),
                "replay_paper_outcome_bucket": row["review_status"],
                "negative_memory_candidate_flag": row["review_status"] != "REVIEW_READY_FOR_PR165",
                "retest_eligibility_condition": "RETEST_AFTER_PR163_C_OR_PR162D_R3_REPAIR_IF_BLOCKED",
                "no_live_authority_flag": True,
                "validation_status": "PASS",
            }
        )
    return rows


def _bucket(value: float) -> str:
    if value <= 0.01:
        return "LOW"
    if value <= 0.1:
        return "MEDIUM"
    return "HIGH"
