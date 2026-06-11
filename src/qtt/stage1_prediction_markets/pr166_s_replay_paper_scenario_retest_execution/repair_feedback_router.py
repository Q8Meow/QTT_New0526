"""Repair-feedback routing for failed or non-executable PR166-S rows."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, repair_contexts


def build_repair_feedback_rows(
    contexts: list[ExecutionContext],
    attribution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for context in repair_contexts(contexts):
        index += 1
        reason = _repair_reason_from_context(context)
        row_id = f"PR166_S_REPAIR_FEEDBACK::{index:06d}"
        rows.append(
            {
                "repair_feedback_route_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "source_selected_batch_ref": context.retest["retest_batch_selection_id"],
                "repair_reason_code": reason,
                "repair_route_type": "REPAIR_REQUIRED_BEFORE_EXECUTION",
                "repair_owner": context.repair.get("owning_repair_agent", "repair_agent") if context.repair else "repair_agent",
                "future_retest_route": "PR166-S_AFTER_REPAIR_QUEUE",
                "executed_as_ready_retest_in_pr166_s": False,
                "repair_payload": {
                    "selection_value_preserved": context.repair.get("selection_value_preserved") if context.repair else context.retest.get("marginal_candidate_utility"),
                    "evidence_requirement": context.repair.get("evidence_requirement") if context.repair else "REPAIR_RECEIPT_AND_MATCHING_CONDITION_RETEST_PACKET",
                },
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_RepairBeforeRetestSelectionQueue.report.json",
                    source_row_ref=context.retest["retest_batch_selection_id"],
                    computed_by_module="repair_feedback_router",
                    owning_agent="repair_agent",
                    consuming_agent="repair_agent",
                    downstream_action_type="repair-feedback input",
                    downstream_pr_route="PR167" if reason == "EXECUTION_MODEL_WEAK" else "score_memory_refresh_PR",
                    downstream_artifact_route="PR166_S_RepairFeedbackRouter.report.json",
                    no_orphan_status="CONNECTED_TO_REPAIR_ROUTE",
                ),
            }
        )
    for attr in attribution_rows:
        if not str(attr.get("recommended_next_state", "")).startswith("REPAIR_REQUIRED_BEFORE_EXECUTION"):
            continue
        index += 1
        reason = str(attr["recommended_next_state"]).split("::", 1)[-1]
        row_id = f"PR166_S_REPAIR_FEEDBACK::{index:06d}"
        rows.append(
            {
                "repair_feedback_route_id": row_id,
                "candidate_packet_id": attr["candidate_packet_id"],
                "source_result_attribution_ref": attr["result_attribution_id"],
                "repair_reason_code": normalize_repair_reason(reason),
                "repair_route_type": "FAILED_EXECUTION_REPAIR_ROUTE",
                "repair_owner": _repair_owner_for(reason),
                "future_retest_route": "PR166-S_AFTER_REPAIR_QUEUE",
                "executed_as_ready_retest_in_pr166_s": True,
                "repair_payload": {
                    "dominant_failure_driver": attr["dominant_failure_driver"],
                    "net_return_proxy": attr["net_return_proxy"],
                    "cost_drag_ratio": attr["cost_drag_ratio"],
                },
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="repair_feedback_router",
                    owning_agent="repair_agent",
                    consuming_agent="repair_agent",
                    downstream_action_type="repair-feedback input",
                    downstream_artifact_route="PR166_S_RepairFeedbackRouter.report.json",
                    no_orphan_status="CONNECTED_TO_REPAIR_ROUTE",
                ),
            }
        )
    return rows


def normalize_repair_reason(reason: str) -> str:
    allowed = {
        "COST_DOMINATED",
        "LATENCY_MISSED",
        "LATENCY_DOMINATED",
        "LIQUIDITY_INSUFFICIENT",
        "LIQUIDITY_DOMINATED",
        "SETTLEMENT_ASSUMPTION_WEAK",
        "SETTLEMENT_ASSUMPTION_SENSITIVE",
        "DATA_DEPTH_INSUFFICIENT",
        "EXECUTION_MODEL_WEAK",
        "ADVERSE_SELECTION_DOMINATED",
    }
    if reason in allowed:
        return "SETTLEMENT_ASSUMPTION_WEAK" if reason == "SETTLEMENT_ASSUMPTION_SENSITIVE" else reason
    return "EXECUTION_MODEL_WEAK"


def _repair_reason_from_context(context: ExecutionContext) -> str:
    if context.repair:
        raw = str(context.repair.get("repair_reason_code") or context.repair.get("required_materialization_action") or "")
        return normalize_repair_reason(raw)
    return "EXECUTION_MODEL_WEAK"


def _repair_owner_for(reason: str) -> str:
    if "LATENCY" in reason:
        return "latency_agent"
    if "LIQUIDITY" in reason:
        return "liquidity_agent"
    if "SETTLEMENT" in reason:
        return "settlement_assumption_agent"
    if "COST" in reason or "ADVERSE" in reason:
        return "tca_agent"
    return "repair_agent"
