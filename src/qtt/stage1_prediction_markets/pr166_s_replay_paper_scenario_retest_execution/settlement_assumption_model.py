"""Prediction-market payoff and settlement assumptions for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, clamp, numeric, ready_contexts


def build_settlement_assumption_rows(contexts: list[ExecutionContext]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        price = simulated_price(context)
        side = str(context.condition.get("side", "YES"))
        adjustment = round(numeric(context.tca.get("settlement_delay_penalty"), 0.0025), 6)
        row_id = ordinal_ref("PR166_S_SETTLEMENT_ASSUMPTION", index)
        rows.append(
            {
                "settlement_assumption_id": row_id,
                "candidate_packet_id": context.candidate_packet_id,
                "order_intent_ref": stable_ref("PR166_S_ORDER_INTENT", context.candidate_packet_id),
                "contract_payoff_style": "BINARY_YES_NO_REPLAY_PAPER_CANDIDATE",
                "side": side if side in {"YES", "NO", "BUY", "SELL"} else "SIMULATED_ONLY",
                "price_implied_probability": price,
                "payout_normalized_win_payoff": round(1.0 - price, 6),
                "payout_normalized_loss_payoff": round(-price, 6),
                "settlement_payoff_adjustment": adjustment,
                "settlement_source_status": "CANDIDATE_PROVISIONAL_REPLAY_ONLY",
                "source_truth_conversion_allowed_by_PR166_S": False,
                "no_source_truth_promotion": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_B_ScenarioOutcomeMatrix.report.json",
                    source_row_ref=context.candidate_packet_id,
                    computed_by_module="settlement_assumption_model",
                    owning_agent="settlement_assumption_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="settlement assumption input",
                    downstream_artifact_route="PR166_S_ExecutionCostLedger.report.json",
                ),
            }
        )
    return rows


def simulated_price(context: ExecutionContext) -> float:
    raw_edge = numeric(context.expected.get("raw_edge_side"), 0.10)
    entry_bucket = str(context.condition.get("entry_price_bucket", "MID_ENTRY"))
    bucket_shift = {"HIGH_EDGE_ENTRY": -0.04, "MID_ENTRY": 0.0, "EXPENSIVE_ENTRY": 0.04}.get(entry_bucket, 0.0)
    return round(clamp(0.50 - raw_edge / 4.0 + bucket_shift, 0.02, 0.98), 6)
