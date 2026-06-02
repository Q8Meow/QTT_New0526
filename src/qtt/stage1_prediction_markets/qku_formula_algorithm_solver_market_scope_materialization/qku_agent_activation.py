"""QTT agent activation and dormant-QKU allowlist helpers."""

from __future__ import annotations

from typing import Any

from . import constants as c


def trade_role_for_qku(qku: dict[str, Any], execution_class: str) -> str:
    qku_type = str(qku.get("qku_type") or "")
    name = str(qku.get("qku_name") or "").upper()
    if execution_class == "FORMULA_EXECUTABLE":
        if "PROB" in name:
            return "PROBABILITY_ESTIMATION"
        if "PRICE" in name:
            return "PRICE_NORMALIZATION"
        return "EXPECTED_VALUE"
    if execution_class == "ALGORITHM_EXECUTABLE":
        return "SIGNAL_GENERATION"
    if execution_class in {"SOLVER_INPUT_ASSEMBLABLE", "SOLVER_MAPPING_ONLY", "SOLVER_SMOKE_EXECUTABLE"}:
        return "QUANTUM_SOLVER_MAPPING"
    if qku_type in {"RISK_QKU"}:
        return "RISK_CONTROL"
    if qku_type in {"CAPITAL_QKU"}:
        return "CAPITAL_ALLOCATION"
    if qku_type in {"LATENCY_QKU"}:
        return "LATENCY_CONTROL"
    if qku_type in {"AGENT_BINDING_QKU"}:
        return "OWNER_REVIEW_GOVERNANCE"
    if qku_type in {"ATOMICROW_QKU"}:
        return "DATA_QUALITY_CONTROL"
    if qku_type in {"PARAMETER_QKU", "RANGE_QKU", "DEFAULT_VALUE_QKU"}:
        return "NON_TRADING_SUPPORT"
    return "UNKNOWN_ROLE"


def activation_status(
    primary_market_scope: str,
    execution_class: str,
    *,
    has_binding: bool,
    has_input_binding: bool,
    market_scope_confidence: str,
) -> tuple[str, str, str]:
    if primary_market_scope in c.DORMANT_DEFAULT_MARKET_SCOPES:
        return (
            "DORMANT_NON_STAGE1_MARKET_SPECIFIC",
            "DORMANT_NON_STAGE1_MARKET_SPECIFIC",
            "LIVE_BLOCKED_NON_STAGE1_MARKET_SCOPE",
        )
    if primary_market_scope == "UNKNOWN_MARKET_SCOPE":
        return (
            "DORMANT_UNKNOWN_MARKET_SCOPE",
            "DORMANT_UNKNOWN_MARKET_SCOPE",
            "LIVE_BLOCKED_OWNER_REVIEW_REQUIRED",
        )
    if market_scope_confidence in {"LOW_NAME_HEURISTIC_ONLY", "UNKNOWN_REQUIRES_OWNER_REVIEW"}:
        return (
            "DORMANT_OWNER_REVIEW_REQUIRED",
            "DORMANT_OWNER_REVIEW_REQUIRED",
            "LIVE_BLOCKED_OWNER_REVIEW_REQUIRED",
        )
    if execution_class == "METADATA_ONLY_BLOCKED":
        return ("DORMANT_METADATA_ONLY", "DORMANT_METADATA_ONLY", "LIVE_BLOCKED_METADATA_ONLY")
    if not has_input_binding:
        return (
            "DORMANT_MISSING_INPUT_BINDING",
            "DORMANT_MISSING_INPUT_BINDING",
            "LIVE_BLOCKED_NO_INPUT_BINDING",
        )
    if execution_class == "FORMULA_EXECUTABLE" and not has_binding:
        return ("DORMANT_MISSING_FORMULA", "DORMANT_MISSING_FORMULA", "LIVE_BLOCKED_NO_FORMULA")
    if execution_class == "ALGORITHM_EXECUTABLE" and not has_binding:
        return ("DORMANT_MISSING_ALGORITHM", "DORMANT_MISSING_ALGORITHM", "LIVE_BLOCKED_NO_ALGORITHM")
    if execution_class in {"FORMULA_EXECUTABLE", "ALGORITHM_EXECUTABLE", "OBJECTIVE_EXECUTABLE", "CONSTRAINT_EXECUTABLE", "SOLVER_SMOKE_EXECUTABLE"}:
        return (
            "ACTIVE_STAGE1_REPLAY_PAPER_ONLY",
            "NOT_DORMANT_STAGE1_ACTIVE",
            "LIVE_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
        )
    if primary_market_scope == "PREDICTION_MARKET_BINARY_EVENT_CONTRACT":
        return (
            "ACTIVE_STAGE1_PREDICTION_MARKET_SUPPORT",
            "NOT_DORMANT_STAGE1_ACTIVE",
            "LIVE_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
        )
    return (
        "ACTIVE_STAGE1_MARKET_AGNOSTIC_SUPPORT",
        "NOT_DORMANT_STAGE1_ACTIVE",
        "LIVE_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
    )


def agent_allowlist_records(classification_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_qkus = [
        record["qku_id"]
        for record in classification_records
        if not str(record["stage1_prediction_market_activation_status"]).startswith("DORMANT_")
    ]
    dormant_qkus = [
        record["qku_id"]
        for record in classification_records
        if str(record["stage1_prediction_market_activation_status"]).startswith("DORMANT_")
    ]
    records = []
    for agent in c.AGENT_ROLES:
        if agent in {"QTT_RESEARCH_AGENT", "QTT_SOURCE_EVIDENCE_AGENT", "QTT_OWNER_REVIEW_AGENT", "QTT_GOVERNANCE_AGENT"}:
            readable = active_qkus + dormant_qkus
            execution_allowed = []
        elif agent in {"QTT_EXECUTION_ROUTER_AGENT"}:
            readable = active_qkus
            execution_allowed = []
        elif agent in {"QTT_RANKING_AGENT", "QTT_SCORING_AGENT"}:
            readable = active_qkus
            execution_allowed = []
        else:
            readable = active_qkus
            execution_allowed = active_qkus
        records.append(
            {
                "record_id": f"PR162B-AGENT-ALLOWLIST-{agent}",
                "agent_id": agent,
                "readable_qku_count": len(readable),
                "readable_qku_refs": readable[:200],
                "readable_qku_refs_truncated_flag": len(readable) > 200,
                "execution_allowed_qku_count": len(execution_allowed),
                "execution_allowed_qku_refs": execution_allowed[:200],
                "dormant_qku_exclusion_status": "PASS",
                "order_routing_allowed_flag": False,
                "live_use_allowed_flag": False,
                "created_by_pr": c.PR_ID,
            }
        )
    return records
