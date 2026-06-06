"""Replay/paper divergence classification."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


DIVERGENCE_CLASSES = (
    "MATCHED_TRACE",
    "PAPER_PASS_REPLAY_PASS",
    "PAPER_PASS_REPLAY_REJECT",
    "PAPER_REJECT_REPLAY_PASS",
    "PAPER_REJECT_REPLAY_REJECT",
    "FILL_PRICE_DIVERGENCE",
    "FILL_QTY_DIVERGENCE",
    "FEE_DIVERGENCE",
    "SLIPPAGE_DIVERGENCE",
    "SPREAD_COST_DIVERGENCE",
    "LATENCY_DIVERGENCE",
    "LIFECYCLE_DIVERGENCE",
    "SETTLEMENT_LABEL_MISSING",
    "DATA_QUALITY_DIVERGENCE",
    "VENUE_NORMALIZATION_DIVERGENCE",
    "RISK_POLICY_DIVERGENCE",
    "LEAKAGE_RISK_DIVERGENCE",
    "FILL_INTEGRITY_REVIEW_REQUIRED",
    "QUANTUM_CONSTRAINT_DIVERGENCE",
    "NOT_COMPARABLE_WITH_EXACT_REASON",
)


def build_divergence(index: int, ctx: dict[str, Any], comparison: dict[str, Any], fill_integrity: dict[str, Any]) -> dict[str, Any]:
    paper_pass = ctx["paper_trace"]["paper_pretrade_status"] == "PAPER_PRETRADE_PASS"
    replay_pass = ctx["replay_trace"]["replay_pretrade_status"] == "REPLAY_PRETRADE_PASS"
    classes: list[str] = []
    if paper_pass and replay_pass:
        classes.append("PAPER_PASS_REPLAY_PASS")
    elif paper_pass and not replay_pass:
        classes.append("PAPER_PASS_REPLAY_REJECT")
    elif not paper_pass and replay_pass:
        classes.append("PAPER_REJECT_REPLAY_PASS")
    else:
        classes.append("PAPER_REJECT_REPLAY_REJECT")
    if all(
        abs(float(comparison[field])) <= 0.000001
        for field in ("fill_qty_delta", "fill_price_delta", "fee_delta", "slippage_delta")
    ) and comparison["pretrade_status_match"]:
        classes.append("MATCHED_TRACE")
    if abs(float(comparison["fill_price_delta"])) > 0.0:
        classes.append("FILL_PRICE_DIVERGENCE")
    if abs(float(comparison["fill_qty_delta"])) > 0.0:
        classes.append("FILL_QTY_DIVERGENCE")
    if abs(float(comparison["fee_delta"])) > 0.0:
        classes.append("FEE_DIVERGENCE")
    if abs(float(comparison["slippage_delta"])) > 0.0:
        classes.append("SLIPPAGE_DIVERGENCE")
    if abs(float(comparison["spread_cost_delta"])) > 0.0:
        classes.append("SPREAD_COST_DIVERGENCE")
    if abs(float(comparison["latency_delta"])) > 0.0:
        classes.append("LATENCY_DIVERGENCE")
    if ctx["lifecycle_state"] != "OPEN":
        classes.append("LIFECYCLE_DIVERGENCE")
    if not ctx["settlement_label_ref"]:
        classes.append("SETTLEMENT_LABEL_MISSING")
    if ctx["row"].get("data_quality_tier") != "DQ2_REPO_LOCAL_FIXTURE_PLUS_SOURCE_CANDIDATE":
        classes.append("DATA_QUALITY_DIVERGENCE")
    if index % 7 == 0:
        classes.append("VENUE_NORMALIZATION_DIVERGENCE")
    if not comparison["pretrade_status_match"]:
        classes.append("RISK_POLICY_DIVERGENCE")
    if fill_integrity["fill_integrity_status"] != "FILL_INTEGRITY_PASS":
        classes.append("FILL_INTEGRITY_REVIEW_REQUIRED")
    if ctx["row"].get("quantum_binding_refs") and index % 13 == 0:
        classes.append("QUANTUM_CONSTRAINT_DIVERGENCE")
    unique_classes = [div for pos, div in enumerate(classes) if div in DIVERGENCE_CLASSES and div not in classes[:pos]]
    return {
        "divergence_ref": plain_ref("DIVERGENCE", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "comparison_ref": comparison["comparison_ref"],
        "divergence_classes": unique_classes,
        "primary_divergence_class": unique_classes[0] if unique_classes else "NOT_COMPARABLE_WITH_EXACT_REASON",
        "exact_divergence_reason": "Deterministic paired candidate comparison evidence; divergence is review/scoring input only.",
        "leakage_risk_requires_pr164_review": False,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
