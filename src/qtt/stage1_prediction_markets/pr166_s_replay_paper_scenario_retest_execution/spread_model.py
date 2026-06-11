"""Deterministic spread model for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


def build_spread_model_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bucket_bps = {"TIGHT": 15.0, "MEDIUM": 35.0, "WIDE": 75.0}
    for index, context in enumerate(ready_contexts(contexts), start=1):
        bucket = str(context.condition.get("spread_bucket", "MEDIUM"))
        row_id = ordinal_ref("PR166_S_SPREAD_MODEL", index)
        rows.append(
            {
                "spread_model_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "order_intent_ref": stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id),
                "spread_bucket": bucket,
                "spread_bps_candidate": bucket_bps.get(bucket, 35.0),
                "upstream_spread_cost_candidate": round(numeric(context.tca.get("spread_cost"), 0.04), 6),
                "model_assumption_ref": stable_ref("PR166_S_SPREAD_ASSUMPTION", bucket),
                "confidence_score": 0.72 if context.tca else 0.45,
                "repair_route": "NO_REPAIR_REQUIRED" if context.tca else "DATA_DEPTH_INSUFFICIENT_WITH_FIXTURE_REPLAY_ROUTE",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_C_ConditionRegimeFeatureMatrix.report.json",
                    source_row_ref=context.candidate_packet_id,
                    computed_by_module="spread_model",
                    owning_agent="tca_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="spread model input",
                    downstream_artifact_route="PR166_S_ExecutionCostLedger.report.json",
                ),
            }
        )
    return rows
