"""Simulated order intent builder for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, ready_contexts
from .settlement_assumption_model import simulated_price


def build_order_intent_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        row_id = stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id)
        order_type = _order_type(context)
        decision = f"PR166_S_TIME::{index:06d}::DECISION"
        submission = f"PR166_S_TIME::{index:06d}::SUBMISSION"
        expiration = f"PR166_S_TIME::{index:06d}::EXPIRATION"
        rows.append(
            {
                "order_intent_id": row_id,
                "source_selected_batch_id": context.batch_id,
                "source_candidate_packet_id": context.candidate_packet_id,
                "candidate_packet_id": context.candidate_packet_id,
                "qku_id": context.qku_id,
                "condition_fingerprint_id": context.retest.get("condition_fingerprint_id")
                or context.candidate.get("condition_fingerprint_id", ""),
                "combination_fingerprint_id": context.retest.get("combination_fingerprint_id")
                or context.candidate.get("combination_fingerprint_id", ""),
                "run_mode": "REPLAY_AND_PAPER",
                "side": _side(context),
                "simulated_price": simulated_price(context),
                "simulated_size": _size(context),
                "simulated_notional_bucket": context.condition.get("size_bucket", "THIN"),
                "order_type": order_type,
                "time_in_force_candidate": "IOC" if order_type == "SIMULATED_IOC" else "GTT_REPLAY_PAPER",
                "decision_time": decision,
                "submission_time": submission,
                "expiration_time": expiration,
                "price_bounds": {
                    "min_price": 0.01,
                    "max_price": 0.99,
                    "bounded_fixture_price_source": "PR165_C_CONDITION_REGIME_FEATURE_AND_PR165_EXPECTED_VALUE",
                },
                "cost_model_ref": stable_ref("PR166_S_EXECUTION_COST", context.candidate_packet_id),
                "fill_model_ref": stable_ref("PR166_S_FILL_MODEL", context.candidate_packet_id),
                "no_live_authority": True,
                "no_live_order_routing": True,
                "replay_paper_only": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_RetestBatchSelectionQueue.report.json",
                    source_row_ref=context.retest["retest_batch_selection_id"],
                    computed_by_module="order_intent_builder",
                    owning_agent="execution_simulation_agent",
                    consuming_agent="fill_model_agent",
                    downstream_action_type="simulated order intent input",
                    downstream_artifact_route="PR166_S_OrderStateTransitionLedger.report.json",
                ),
            }
        )
    return rows


def _side(context: ExecutionContext) -> str:
    side = str(context.condition.get("side", "YES")).upper()
    return side if side in {"YES", "NO", "BUY", "SELL"} else "SIMULATED_ONLY"


def _order_type(context: ExecutionContext) -> str:
    order_type = str(context.condition.get("order_type", "LIMIT_MAKER")).upper()
    if "MARKET" in order_type:
        return "SIMULATED_MARKET"
    if "IOC" in order_type:
        return "SIMULATED_IOC"
    if "POST" in order_type or "MAKER" in order_type:
        return "SIMULATED_POST_ONLY"
    return "SIMULATED_LIMIT"


def _size(context: ExecutionContext) -> float:
    size_bucket = str(context.condition.get("size_bucket", "THIN"))
    return {"THIN": 1.0, "NORMAL": 2.0, "LARGE": 5.0}.get(size_bucket, 1.0)
