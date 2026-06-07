"""Stage-1 activation and dormancy classifier."""

from __future__ import annotations

from typing import Any

from .central_reason_codes import ACTIVATION_STATES, require_enum
from .deterministic_ids import plain_ref


def classify_activation(market_scope: str) -> tuple[str, str]:
    if market_scope.startswith("PREDICTION_MARKET_"):
        return "STAGE1_ACTIVE_PREDICTION_MARKET", "Prediction-market scope is Stage-1 active."
    if market_scope.startswith("MARKET_AGNOSTIC_"):
        return "STAGE1_ACTIVE_MARKET_AGNOSTIC", "Market-agnostic math/risk/optimizer/governance scope supports Stage-1 control-plane use."
    if market_scope == "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW":
        return "REPAIR_REQUIRED_BEFORE_ACTIVATION", "Unknown market scope requires exact repair before activation."
    return "DORMANT_NON_STAGE1_MARKET", "Non-Stage-1 market scope is dormant with exact route."


def build_stage1_records(identity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(identity_rows, 1):
        activation_state = require_enum(row["activation_state"], ACTIVATION_STATES, "activation_state")
        dormant = activation_state.startswith("DORMANT")
        rows.append(
            {
                "stage1_activation_record_ref": plain_ref("STAGE1", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "market_scope": row["market_scope"],
                "activation_state": activation_state,
                "stage1_active_flag": activation_state.startswith("STAGE1_ACTIVE"),
                "dormant_flag": dormant,
                "dormant_reason": row["activation_reason"] if dormant else "",
                "activation_reason": row["activation_reason"],
                "downstream_pr_route": (
                    "ROUTE_TO_DORMANT_NON_STAGE1"
                    if dormant
                    else row["primary_downstream_pr_route"]
                ),
                "validation_status": "PASS",
            }
        )
    return rows
