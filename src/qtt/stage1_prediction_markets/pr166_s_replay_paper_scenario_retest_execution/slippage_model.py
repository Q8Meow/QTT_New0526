"""Deterministic slippage model for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


def build_slippage_model_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        latency_bucket = str(context.condition.get("latency_bucket", "MEDIUM"))
        liquidity_bucket = str(context.condition.get("liquidity_bucket", "MEDIUM"))
        mode = "SPREAD_BASED_SLIPPAGE"
        if latency_bucket == "HIGH":
            mode = "LATENCY_ADJUSTED_SLIPPAGE"
        if liquidity_bucket == "LOW":
            mode = "LIQUIDITY_BUCKET_SLIPPAGE"
        upstream = numeric(context.tca.get("slippage_cost"), 0.03)
        bps = round(max(1.0, upstream * 10000.0), 6)
        row_id = ordinal_ref("PR166_S_SLIPPAGE_MODEL", index)
        rows.append(
            {
                "slippage_model_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "order_intent_ref": stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id),
                "slippage_mode": mode,
                "slippage_bps_candidate": bps,
                "slippage_cost_candidate": round(upstream, 6),
                "model_assumption_ref": stable_ref("PR166_S_SLIPPAGE_ASSUMPTION", mode, liquidity_bucket, latency_bucket),
                "confidence_score": 0.70 if context.tca else 0.42,
                "repair_route": "NO_REPAIR_REQUIRED" if context.tca else "EXECUTION_MODEL_WEAK",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_TCAAdjustedScoreRegistry.report.json",
                    source_row_ref=context.candidate_packet_id,
                    computed_by_module="slippage_model",
                    owning_agent="tca_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="slippage model input",
                    downstream_artifact_route="PR166_S_ExecutionCostLedger.report.json",
                ),
            }
        )
    return rows
