"""Central market-scope classifier for QKU and candidate rows."""

from __future__ import annotations

from typing import Any

from .central_reason_codes import MARKET_SCOPES, require_enum
from .deterministic_ids import plain_ref


def classify_market_scope(master_row: dict[str, Any] | None, candidate: dict[str, Any] | None = None) -> str:
    market = str((master_row or {}).get("qku_market_primary") or "").upper()
    qku_type = str((master_row or {}).get("qku_type") or "").upper()
    domain = str((candidate or {}).get("domain_family_key") or "").lower()
    if market == "PREDICTION_MARKET":
        if "multi" in domain:
            return "PREDICTION_MARKET_MULTIOUTCOME_EVENT_CONTRACT"
        if "range" in domain or "scalar" in domain:
            return "PREDICTION_MARKET_SCALAR_RANGE_CONTRACT"
        return "PREDICTION_MARKET_BINARY_EVENT_CONTRACT"
    if market == "MARKET_AGNOSTIC":
        if "RISK" in qku_type or "risk" in domain:
            return "MARKET_AGNOSTIC_RISK"
        if "ALGORITHM" in qku_type or "OPTIMIZER" in qku_type or "optimizer" in domain:
            return "MARKET_AGNOSTIC_OPTIMIZER"
        if "AGENT" in qku_type:
            return "MARKET_AGNOSTIC_GOVERNANCE"
        return "MARKET_AGNOSTIC_MATH"
    if market == "FUTURES_MARKET":
        return "FUTURES"
    return "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW"


def build_market_scope_records(identity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(identity_rows, 1):
        scope = require_enum(row["market_scope"], MARKET_SCOPES, "market_scope")
        rows.append(
            {
                "market_scope_record_ref": plain_ref("MARKET_SCOPE", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "market_scope": scope,
                "market_scope_classifier_reason": row["market_scope_reason"],
                "owner_review_required": scope == "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW",
                "route_when_unknown": (
                    "ROUTE_TO_PR162B_R_MARKET_SCOPE_REPAIR"
                    if scope == "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW"
                    else "ROUTE_TO_PR165_SCORING"
                ),
                "validation_status": "PASS",
            }
        )
    return rows
