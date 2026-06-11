"""Deterministic latency lane model for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


LANE_MS = {
    "LOW": ("FAST_LANE", 15, 25, 55),
    "MEDIUM": ("STANDARD_LANE", 60, 90, 185),
    "HIGH": ("SLOW_LANE", 180, 260, 540),
}


def build_latency_model_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        bucket = str(context.condition.get("latency_bucket", "MEDIUM"))
        lane, decision_ms, submission_ms, round_trip_ms = LANE_MS.get(bucket, LANE_MS["MEDIUM"])
        latency_drag = min(1.0, numeric(context.candidate.get("latency_drag_penalty"), 0.35) + round_trip_ms / 5000.0)
        edge = numeric(context.expected.get("expected_value_candidate"), numeric(context.scenario.get("net_edge_candidate"), 0.0))
        latency_miss = lane == "SLOW_LANE" and edge < 0.08
        row_id = ordinal_ref("PR166_S_LATENCY_MODEL", index)
        rows.append(
            {
                "latency_model_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "order_intent_ref": stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id),
                "simulated_decision_latency_ms": decision_ms,
                "simulated_submission_latency_ms": submission_ms,
                "simulated_round_trip_latency_ms": round_trip_ms,
                "latency_lane_ref": lane,
                "latency_miss_flag": latency_miss,
                "latency_drag_score": round(latency_drag, 6),
                "future_latency_repair_route": "LATENCY_MISSED" if latency_miss else "NO_REPAIR_REQUIRED",
                "no_live_hot_path_authority": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_LatencyLaneAssignmentRegistry.report.json",
                    source_row_ref=context.candidate_packet_id,
                    computed_by_module="latency_model",
                    owning_agent="latency_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="latency model input",
                    downstream_artifact_route="PR166_S_ExecutionCostLedger.report.json",
                ),
            }
        )
    return rows
