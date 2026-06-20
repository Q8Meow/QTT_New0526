#!/usr/bin/env python3
"""Connector candidate routing without connector binding for PR168-RP."""

from __future__ import annotations

from typing import Any


def connector_route_for(row: dict[str, Any]) -> dict[str, Any]:
    market_scope = str(row.get("market_scope") or row.get("row_family") or "")
    route = "FUTURE_CONNECTOR_CANDIDATE_ROUTE::PREDICTION_MARKET_STAGE1" if "PREDICTION" in market_scope or row.get("row_family") in {"QKU", "CandidatePacketV1"} else "FUTURE_CONNECTOR_CANDIDATE_ROUTE::MARKET_SCOPE_REVIEW"
    return {
        "connector_candidate_route": route,
        "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
        "connector_truth_authority": False,
        "live_authority": False,
        "downstream_connector_agent": "Connector Candidate Routing Agent",
        "downstream_connector_pr": "PR174-PR181",
        "source_truth_authority": False,
    }
