"""Event stream builder for deterministic PR166-S replay/paper execution."""

from __future__ import annotations

from typing import Any

from .execution_cost_engine import by_candidate
from .input_consumption import row_contract
from .selected_batch_loader import LoadedSelection, ready_contexts


def build_event_stream_rows(
    selection: LoadedSelection,
    order_rows: list[dict[str, Any]],
    fill_rows: list[dict[str, Any]],
    attribution_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    orders = by_candidate(order_rows)
    fills = by_candidate(fill_rows)
    attrs = by_candidate(attribution_rows)
    rows: list[dict[str, Any]] = []
    index = 0
    for batch in sorted(selection.batch_rows, key=lambda row: str(row["batch_id"])):
        index += 1
        rows.append(_event(index, batch["batch_id"], "SELECTED_BATCH_EVENT", batch["batch_id"], "PR165_D_BatchExposureCapacityLedger.report.json", "selection_agent"))
    for context in ready_contexts(selection.contexts):
        cid = context.candidate_packet_id
        for event_type, source_ref, artifact, owner in (
            ("MARKET_SNAPSHOT_EVENT", context.condition.get("condition_regime_feature_id", cid), "PR165_C_ConditionRegimeFeatureMatrix.report.json", "replay_agent"),
            ("SCENARIO_REGIME_EVENT", context.scenario.get("scenario_outcome_ref", cid), "PR165_B_ScenarioOutcomeMatrix.report.json", "replay_agent"),
            ("SIMULATED_ORDER_INTENT_EVENT", orders[cid]["order_intent_id"], "PR166_S_OrderIntentRegistry.report.json", "execution_simulation_agent"),
            ("SIMULATED_FILL_EVENT", fills[cid]["fill_record_id"], "PR166_S_SimulatedFillLedger.report.json", "fill_model_agent"),
            ("RESULT_ATTRIBUTION_EVENT", attrs[cid]["result_attribution_id"], "PR166_S_ResultAttributionLedger.report.json", "risk_agent"),
        ):
            index += 1
            rows.append(_event(index, context.batch_id, event_type, source_ref, artifact, owner, cid))
    for context in selection.contexts:
        if context.ready:
            continue
        index += 1
        rows.append(_event(index, context.batch_id, "REPAIR_PREPARATION_EVENT", context.retest["retest_batch_selection_id"], "PR165_D_RetestBatchSelectionQueue.report.json", "repair_agent", context.candidate_packet_id))
    return rows


def _event(
    index: int,
    batch_id: str,
    event_type: str,
    source_ref: str,
    source_artifact: str,
    owner: str,
    candidate_packet_id: str = "",
) -> dict[str, Any]:
    row_id = f"PR166_S_EVENT::{index:06d}"
    return {
        "event_stream_id": row_id,
        "event_type": event_type,
        "source_selected_batch_id": batch_id,
        "candidate_packet_id": candidate_packet_id,
        "event_time": f"PR166_S_EVENT_TIME::{index:06d}",
        "data_available_at_decision_time": True,
        "event_cursor": index,
        "source_event_ref": source_ref,
        "no_future_outcome_used": True,
        "no_settlement_leak_used": True,
        "no_private_state_used": True,
        "no_live_market_state_used": True,
        **row_contract(
            row_id=row_id,
            source_artifact_ref=source_artifact,
            source_row_ref=source_ref,
            computed_by_module="event_stream_builder",
            owning_agent=owner,
            consuming_agent="execution_simulation_agent",
            downstream_action_type="event-driven replay/paper execution input",
            downstream_artifact_route="PR166_S_OrderIntentRegistry.report.json",
        ),
    }
