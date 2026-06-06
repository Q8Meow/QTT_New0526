"""Replay/paper rejection remediation classification."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def _family_from_reasons(reasons: list[str]) -> tuple[str, str, str]:
    text = " ".join(reasons)
    if "PAPER_CASH_INSUFFICIENT" in text:
        return ("VALID_CAPITAL_REJECTION", "VALID_REJECTION_KEEP_REJECTED", "Keep rejected until later capital policy review.")
    if "DATA_FRESHNESS" in text:
        return ("MARKET_STATE_REPAIR", "REPAIRABLE_PRE_LAUNCH", "Repair stale quote fixture freshness before launch review.")
    if "TICK_NOT_ALIGNED" in text:
        return ("TICK_SIZE_REPAIR", "REPAIRABLE_PRE_LAUNCH", "Repair tick-size quantization model before launch review.")
    if "PRICE_DOMAIN_INVALID" in text:
        return ("VENUE_NORMALIZATION_REPAIR", "REPAIRABLE_PRE_LAUNCH", "Repair venue price-domain normalization.")
    if "EVENT_LIFECYCLE_NOT_OPEN" in text:
        return ("VALID_LIFECYCLE_REJECTION", "VALID_REJECTION_KEEP_REJECTED", "Keep rejected while lifecycle is non-open.")
    if "ROBUST_EDGE_THRESHOLD" in text:
        return ("VALID_EDGE_REJECTION", "VALID_REJECTION_KEEP_REJECTED", "Keep rejected because robust edge is not evaluable after cost.")
    if "NO_LIQUIDITY" in text:
        return ("VALID_LIQUIDITY_REJECTION", "VALID_REJECTION_KEEP_REJECTED", "Keep rejected until liquidity exists.")
    return ("OWNER_REVIEW_REQUIRED_WITH_REASON", "OWNER_REVIEW_REQUIRED", "Review exact rejection reason in PR164.")


def build_remediation(index: int, ctx: dict[str, Any], divergence: dict[str, Any]) -> dict[str, Any]:
    paper_status = ctx["paper_trace"]["paper_pretrade_status"]
    replay_status = ctx["replay_trace"]["replay_pretrade_status"]
    paper_reasons = list(ctx["paper"]["pretrade"].get("exact_reject_reasons") or [])
    replay_reasons = [] if replay_status == "REPLAY_PRETRADE_PASS" else ["REPLAY_SYNTHETIC_MODEL_REJECTED_WITH_EXACT_REASON"]
    if paper_status != "PAPER_PRETRADE_PASS":
        family, repairability, action = _family_from_reasons(paper_reasons)
    elif replay_status != "REPLAY_PRETRADE_PASS":
        family, repairability, action = (
            "REPLAY_ADAPTER_REPAIR",
            "REPAIRABLE_PRE_LAUNCH",
            "Inspect replay-only rejection divergence before PR165 scoring use.",
        )
    else:
        family, repairability, action = (
            "OWNER_REVIEW_REQUIRED_WITH_REASON",
            "OWNER_REVIEW_REQUIRED",
            "No rejection; retain paired evidence for review and scoring input.",
        )
    return {
        "remediation_ref": plain_ref("REMEDIATION", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "paper_pretrade_status": paper_status,
        "replay_pretrade_status": replay_status,
        "paper_rejection_reasons": paper_reasons,
        "replay_rejection_reasons": replay_reasons,
        "divergence_class_refs": [divergence["divergence_ref"]],
        "remediation_family": family,
        "repairability": repairability,
        "exact_repair_action": action,
        "downstream_pr164_ref": plain_ref("PR164_HANDOFF", index),
        "downstream_pr165_ref": plain_ref("PR165_HANDOFF", index),
        "downstream_future_repair_pr_ref": "PR163-C_PRETRADE_REJECTION_REMEDIATION_CANDIDATE",
        "no_forced_pass": True,
        "no_live_authority": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
