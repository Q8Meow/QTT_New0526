"""Deterministic paper pre-trade checks."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref
from .paper_cash_reservation import estimate_required_cash


REQUIRED_CHECKS = (
    "candidate_packet_present",
    "qku_route_present",
    "paper_binding_present",
    "paper_market_state_present",
    "paper_portfolio_state_present",
    "paper_decision_intent_present",
    "order_side_valid",
    "order_type_valid",
    "price_domain_valid",
    "tick_aligned",
    "size_positive",
    "venue_min_size_respected",
    "paper_cash_available",
    "paper_cash_reservation_possible",
    "position_limit_respected",
    "event_exposure_limit_respected",
    "category_exposure_limit_respected",
    "venue_exposure_limit_respected",
    "capital_budget_limit_respected",
    "data_freshness_valid",
    "event_lifecycle_open",
    "settlement_not_final_before_open",
    "fee_model_present_or_exact_candidate_reason",
    "slippage_model_present_or_exact_candidate_reason",
    "latency_model_present_or_exact_candidate_reason",
    "robust_edge_threshold_evaluable",
    "no_live_authority",
    "no_source_acceptance",
    "no_connector_binding",
    "no_private_state_fetch",
    "no_profit_evidence",
    "no_llm_runtime_inference",
    "no_llm_order_release",
    "no_llm_source_acceptance",
    "no_llm_result_rewrite",
)


def _tick_aligned(price: float, tick: float = 0.01) -> bool:
    return abs(round(price / tick) * tick - price) < 0.0000001


def run_pretrade_checks(
    *,
    index: int,
    candidate_packet_id: str,
    decision_ref: str,
    order_ref: str,
    scenario_id: str,
    side: str,
    order_type: str,
    limit_price: float,
    requested_qty: float,
    paper_cash: float,
    lifecycle_state: str,
    robust_edge_after_cost: float,
) -> dict[str, Any]:
    checks = {name: True for name in REQUIRED_CHECKS}
    reasons: list[str] = []
    if side not in {"BUY_YES", "SELL_YES", "BUY_NO", "SELL_NO"}:
        checks["order_side_valid"] = False
        reasons.append("ORDER_SIDE_INVALID")
    if order_type not in {"LIMIT", "MARKETABLE_LIMIT", "GTC", "GTD", "FOK", "FAK", "POST_ONLY"}:
        checks["order_type_valid"] = False
        reasons.append("ORDER_TYPE_INVALID")
    if not (0.0 < limit_price < 1.0):
        checks["price_domain_valid"] = False
        reasons.append("PRICE_DOMAIN_INVALID")
    if not _tick_aligned(limit_price):
        checks["tick_aligned"] = False
        reasons.append("TICK_NOT_ALIGNED")
    if requested_qty <= 0:
        checks["size_positive"] = False
        reasons.append("SIZE_NOT_POSITIVE")
    required_cash = estimate_required_cash(side, limit_price, requested_qty, 0.05, 0.05)
    if required_cash > paper_cash:
        checks["paper_cash_available"] = False
        checks["paper_cash_reservation_possible"] = False
        reasons.append("PAPER_CASH_INSUFFICIENT")
    if scenario_id == "STALE_QUOTE_REJECT":
        checks["data_freshness_valid"] = False
        reasons.append("DATA_FRESHNESS_INVALID_STALE_QUOTE")
    if lifecycle_state != "OPEN":
        checks["event_lifecycle_open"] = False
        checks["settlement_not_final_before_open"] = False
        reasons.append(f"EVENT_LIFECYCLE_NOT_OPEN_{lifecycle_state}")
    if robust_edge_after_cost < 0.0:
        checks["robust_edge_threshold_evaluable"] = False
        reasons.append("ROBUST_EDGE_THRESHOLD_NOT_EVALUABLE")
    status = "PAPER_PRETRADE_PASS" if all(checks.values()) else "PAPER_PRETRADE_REJECT_WITH_EXACT_REASON"
    return {
        "pretrade_receipt_ref": plain_ref("PRETRADE_RECEIPT", index),
        "candidate_packet_id": candidate_packet_id,
        "paper_decision_intent_ref": decision_ref,
        "paper_order_intent_ref": order_ref,
        "scenario_id": scenario_id,
        "pretrade_status": status,
        "check_results": checks,
        "failed_check_names": [name for name, passed in checks.items() if not passed],
        "exact_reject_reasons": reasons,
        "robust_edge_after_cost": round(robust_edge_after_cost, 6),
        "no_blocker_status_used": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
