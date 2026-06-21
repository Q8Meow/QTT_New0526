#!/usr/bin/env python3
"""Data-readiness classification for PR168-DATA1 artifacts."""

from __future__ import annotations

from collections import Counter

from tools.pr168_data1_config import authority_flags, route_defaults


def classify_readiness(snapshot_rows: list[dict[str, object]], l2_rows: list[dict[str, object]], audit_rows: list[dict[str, object]], now_utc: str) -> list[dict[str, object]]:
    counter = Counter(str(row.get("data_authority_class")) for row in snapshot_rows)
    counter["DATA_READY_PUBLIC_REAL_FORWARD_L2_CANDIDATE"] = len(l2_rows)
    for audit in audit_rows:
        counter[str(audit.get("availability_classification"))] += 1
    rows = []
    for state, count in sorted(counter.items()):
        rows.append(
            {
                "classification_row_id": f"readiness_{state.lower()}",
                "data_readiness_state": state,
                "artifact_count": count,
                "computability_route": _route_for_state(state),
                "accepted_truth_flag": False,
                "candidate_only_flag": True,
                "created_at_utc": now_utc,
                **route_defaults("governance"),
                **authority_flags(),
            }
        )
    return rows


def _route_for_state(state: str) -> str:
    if "FORWARD_L2" in state:
        return "COMPUTABLE_AFTER_HISTORICAL_FULL_BOOK_OR_FORWARD_L2_CAPTURE"
    if "SNAPSHOT" in state or "ORDERBOOK" in state or "PRICE_HISTORY" in state or "TRADE_HISTORY" in state:
        return "COMPUTABLE_AFTER_DATA1_WITH_PUBLIC_CANDIDATE_DATA"
    if "UNAVAILABLE" in state:
        return "NOT_COMPUTABLE_UNDER_CURRENT_DATA_MAP_WITH_EXACT_REASON"
    if "AUTH" in state or "SUBSCRIPTION" in state:
        return "COMPUTABLE_AFTER_FORECASTEX_IBKR_AUTH_SETUP"
    return "COMPUTABLE_AFTER_SOURCE_EVIDENCE_ACCEPTANCE"
