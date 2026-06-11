"""Deterministic fee model for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


def build_fee_model_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        row_id = ordinal_ref("PR166_S_FEE_MODEL", index)
        order_type = str(context.condition.get("order_type", "LIMIT_MAKER"))
        maker_bps = 15.0 if "MAKER" in order_type else 20.0
        taker_bps = 35.0 if "MAKER" in order_type else 45.0
        upstream_fee = numeric(context.tca.get("fee_cost"), 0.02)
        rows.append(
            {
                "fee_model_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "qku_id": context.qku_id,
                "order_intent_ref": stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id),
                "maker_fee_candidate_bps": maker_bps,
                "taker_fee_candidate_bps": taker_bps,
                "upstream_fee_cost_candidate": round(upstream_fee, 6),
                "fee_source_status": "EXISTING_REPO",
                "source_ref": context.tca.get("tca_adjusted_score_ref", "PR165_TCAAdjustedScoreRegistry.report.json"),
                "replay_paper_only": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_TCAAdjustedScoreRegistry.report.json",
                    source_row_ref=context.candidate_packet_id,
                    computed_by_module="fee_model",
                    owning_agent="tca_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="fee model input",
                    downstream_artifact_route="PR166_S_ExecutionCostLedger.report.json",
                ),
            }
        )
    return rows
