"""Deterministic paper order state machine."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref
from .paper_scenario_grid import Scenario


VALID_STATE_TRANSITIONS = {
    "DECISION_INTENT_CREATED": {"INTENT_CREATED"},
    "INTENT_CREATED": {"PRETRADE_CHECKED"},
    "PRETRADE_CHECKED": {"PRETRADE_REJECTED", "ACCEPTED_TO_PAPER_OMS"},
    "PRETRADE_REJECTED": {
        "STALE_QUOTE_REJECTED",
        "INSUFFICIENT_CASH_REJECTED",
        "INVALID_TICK_REJECTED",
        "INVALID_LIFECYCLE_REJECTED",
        "REJECTED",
    },
    "ACCEPTED_TO_PAPER_OMS": {"DELAYED_PENDING", "RESTING", "PARTIALLY_FILLED", "FILLED", "REJECTED", "EXPIRED"},
    "DELAYED_PENDING": {"RESTING", "PARTIALLY_FILLED", "FILLED", "REJECTED", "EXPIRED"},
    "RESTING": {"CANCEL_REQUESTED", "EXPIRED"},
    "PARTIALLY_FILLED": {"RESTING", "CANCELLED", "FILLED"},
    "FILLED": {"SYNTHETIC_SETTLEMENT_PENDING"},
    "CANCEL_REQUESTED": {"CANCELLED"},
    "SYNTHETIC_SETTLEMENT_PENDING": {"SYNTHETIC_SETTLED_FOR_FIXTURE_ACCOUNTING_ONLY"},
}


def _reject_state(reason: str) -> str:
    if "STALE_QUOTE" in reason or "FRESHNESS" in reason:
        return "STALE_QUOTE_REJECTED"
    if "CASH" in reason:
        return "INSUFFICIENT_CASH_REJECTED"
    if "TICK" in reason or "PRICE_DOMAIN" in reason:
        return "INVALID_TICK_REJECTED"
    if "LIFECYCLE" in reason:
        return "INVALID_LIFECYCLE_REJECTED"
    return "REJECTED"


def build_state_transitions(
    *,
    index: int,
    candidate_packet_id: str,
    decision_ref: str,
    order_ref: str,
    pretrade_ref: str,
    pretrade_status: str,
    pretrade_reasons: list[str],
    fill: Any,
    scenario: Scenario,
) -> list[dict[str, Any]]:
    sequence: list[tuple[str, str, str]] = [
        ("NONE", "DECISION_INTENT_CREATED", "PAPER_DECISION_INTENT_CREATED"),
        ("DECISION_INTENT_CREATED", "INTENT_CREATED", "PAPER_ORDER_INTENT_CREATED"),
        ("INTENT_CREATED", "PRETRADE_CHECKED", pretrade_status),
    ]
    if pretrade_status != "PAPER_PRETRADE_PASS":
        reason = pretrade_reasons[0] if pretrade_reasons else "PAPER_PRETRADE_REJECT_WITH_EXACT_REASON"
        sequence.append(("PRETRADE_CHECKED", "PRETRADE_REJECTED", reason))
        sequence.append(("PRETRADE_REJECTED", _reject_state(reason), reason))
    else:
        sequence.append(("PRETRADE_CHECKED", "ACCEPTED_TO_PAPER_OMS", "PAPER_OMS_ACCEPTED"))
        prior = "ACCEPTED_TO_PAPER_OMS"
        if scenario.name in {"MARKETABLE_BUY_FULL_FILL", "MARKETABLE_SELL_FULL_FILL", "FOK_FULL_FILL", "FAK_PARTIAL_FILL_CANCEL_RESIDUAL"}:
            sequence.append((prior, "DELAYED_PENDING", "PAPER_LATENCY_BUCKET_APPLIED"))
            prior = "DELAYED_PENDING"
        if fill.terminal_state == "FILLED":
            sequence.append((prior, "FILLED", fill.reason_code))
            sequence.append(("FILLED", "SYNTHETIC_SETTLEMENT_PENDING", "PAPER_FIXTURE_ACCOUNTING_SETTLEMENT_PENDING"))
            sequence.append(
                (
                    "SYNTHETIC_SETTLEMENT_PENDING",
                    "SYNTHETIC_SETTLED_FOR_FIXTURE_ACCOUNTING_ONLY",
                    "FIXTURE_LEDGER_ACCOUNTING_CHECK_ONLY",
                )
            )
        elif fill.terminal_state == "RESTING":
            if fill.filled_qty > 0:
                sequence.append((prior, "PARTIALLY_FILLED", fill.reason_code))
                sequence.append(("PARTIALLY_FILLED", "RESTING", "PAPER_RESIDUAL_RESTING"))
            else:
                sequence.append((prior, "RESTING", fill.reason_code))
        elif fill.terminal_state == "CANCELLED":
            if fill.filled_qty > 0:
                sequence.append((prior, "PARTIALLY_FILLED", fill.reason_code))
                sequence.append(("PARTIALLY_FILLED", "CANCELLED", "PAPER_RESIDUAL_CANCELLED"))
            else:
                sequence.append((prior, "RESTING", "PAPER_GTC_RESTING_BEFORE_CANCEL"))
                sequence.append(("RESTING", "CANCEL_REQUESTED", "PAPER_CANCEL_REQUESTED"))
                sequence.append(("CANCEL_REQUESTED", "CANCELLED", fill.reason_code))
        elif fill.terminal_state == "EXPIRED":
            sequence.append((prior, "RESTING", "PAPER_GTD_RESTING_UNTIL_EXPIRY"))
            sequence.append(("RESTING", "EXPIRED", fill.reason_code))
        else:
            sequence.append((prior, "REJECTED", fill.reason_code))
    rows = []
    for seq, (prior_state, next_state, reason) in enumerate(sequence, 1):
        rows.append(
            {
                "state_transition_ref": plain_ref("STATE_TRANSITION", (index * 100) + seq, width=8),
                "candidate_packet_id": candidate_packet_id,
                "paper_decision_intent_ref": decision_ref,
                "paper_order_intent_ref": order_ref,
                "pretrade_receipt_ref": pretrade_ref,
                "prior_state": prior_state,
                "next_state": next_state,
                "reason_code": reason,
                "consumed_input_refs": [decision_ref, order_ref, pretrade_ref],
                "sequence_number": seq,
                "scenario_id": scenario.name,
                "terminal_transition": seq == len(sequence),
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows
