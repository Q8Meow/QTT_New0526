"""Risk and capital sizing route helpers."""

from __future__ import annotations


def risk_capital_sizing_routes(routes):
    return [
        record for record in routes
        if "RISK_MANAGER_CANDIDATE_REVIEW" in record.get("agent_path_refs", [])
        or "CAPITAL_SIZING_CANDIDATE_REVIEW" in record.get("agent_path_refs", [])
    ]
