"""Deterministic market-impact proxy for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


def build_market_impact_model_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        liquidity_bucket = str(context.condition.get("liquidity_bucket", "MEDIUM"))
        size_bucket = str(context.condition.get("size_bucket", "THIN"))
        base = {"HIGH": 0.004, "MEDIUM": 0.012, "LOW": 0.032}.get(liquidity_bucket, 0.012)
        size_mult = {"THIN": 0.75, "NORMAL": 1.0, "LARGE": 1.7}.get(size_bucket, 0.85)
        impact = round(base * size_mult, 6)
        row_id = ordinal_ref("PR166_S_MARKET_IMPACT_MODEL", index)
        rows.append(
            {
                "market_impact_model_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "order_intent_ref": stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id),
                "impact_mode": "IMPACT_BUCKET_PROXY",
                "impact_bps_candidate": round(impact * 10000.0, 6),
                "impact_bps_cost": impact,
                "model_assumption_ref": stable_ref("PR166_S_MARKET_IMPACT_ASSUMPTION", liquidity_bucket, size_bucket),
                "confidence_score": 0.64 if context.condition else 0.40,
                "repair_route": "LIQUIDITY_INSUFFICIENT" if liquidity_bucket == "LOW" else "NO_REPAIR_REQUIRED",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_C_ConditionRegimeFeatureMatrix.report.json",
                    source_row_ref=context.candidate_packet_id,
                    computed_by_module="market_impact_model",
                    owning_agent="tca_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="market-impact model input",
                    downstream_artifact_route="PR166_S_ExecutionCostLedger.report.json",
                ),
            }
        )
    return rows
