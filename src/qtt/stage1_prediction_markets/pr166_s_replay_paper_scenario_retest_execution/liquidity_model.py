"""Deterministic liquidity and capacity model for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


LIQUIDITY_PROXY = {
    "HIGH": (1.00, "SIZE_BUCKET_05", "MEDIUM_CAPACITY", 0.10, 0.03),
    "MEDIUM": (0.55, "SIZE_BUCKET_03", "SMALL_CAPACITY", 0.32, 0.12),
    "LOW": (0.22, "SIZE_BUCKET_01", "THIN_CAPACITY", 0.62, 0.35),
}


def build_liquidity_model_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        bucket = str(context.condition.get("liquidity_bucket", "MEDIUM"))
        visible, max_size, capacity, partial, no_fill = LIQUIDITY_PROXY.get(bucket, LIQUIDITY_PROXY["MEDIUM"])
        fragility = max(0.0, min(1.0, numeric(context.candidate.get("liquidity_fragility_penalty"), 1.0 - visible)))
        row_id = ordinal_ref("PR166_S_LIQUIDITY_MODEL", index)
        rows.append(
            {
                "liquidity_model_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "order_intent_ref": stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id),
                "liquidity_bucket": bucket,
                "visible_liquidity_proxy": visible,
                "volume_or_depth_proxy": round(visible * 1000.0, 6),
                "liquidity_fragility_score": round(fragility, 6),
                "max_simulated_size_bucket": max_size,
                "capacity_bucket": capacity,
                "partial_fill_probability_proxy": partial,
                "no_fill_probability_proxy": no_fill,
                "liquidity_repair_route": "LIQUIDITY_INSUFFICIENT" if bucket == "LOW" else "NO_REPAIR_REQUIRED",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_C_ConditionRegimeFeatureMatrix.report.json",
                    source_row_ref=context.candidate_packet_id,
                    computed_by_module="liquidity_model",
                    owning_agent="liquidity_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="liquidity model input",
                    downstream_artifact_route="PR166_S_ExecutionCostLedger.report.json",
                ),
            }
        )
    return rows
