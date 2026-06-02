"""Strict PR162B QKU market-scope classifier."""

from __future__ import annotations

from typing import Any

from . import constants as c


def classify_market_scope(qku: dict[str, Any]) -> dict[str, Any]:
    old_scope = str(qku.get("qku_market_primary") or "")
    qku_type = str(qku.get("qku_type") or "")
    name = str(qku.get("qku_name") or "").upper()
    if old_scope == "PREDICTION_MARKET":
        primary = "PREDICTION_MARKET_BINARY_EVENT_CONTRACT"
        confidence = "HIGH_EXPLICIT_QKU_FAMILY"
        method = "PR161C_EXPLICIT_PREDICTION_MARKET_SCOPE"
    elif old_scope == "FUTURES_MARKET" or "FUTURE_AGENT_FAMILY" in name:
        primary = "FUTURES"
        confidence = "HIGH_EXPLICIT_QKU_FAMILY"
        method = "PR161C_EXPLICIT_FUTURES_SCOPE"
    elif qku_type in {"FORMULA_QKU", "PARAMETER_QKU", "RANGE_QKU", "DEFAULT_VALUE_QKU"}:
        primary = "MARKET_AGNOSTIC_MATH"
        confidence = "MEDIUM_FORMULA_REQUIREMENT_INFERRED"
        method = "QKU_TYPE_MARKET_AGNOSTIC_MATH"
    elif qku_type in {"RISK_QKU", "CAPITAL_QKU"}:
        primary = "MARKET_AGNOSTIC_RISK"
        confidence = "MEDIUM_FORMULA_REQUIREMENT_INFERRED"
        method = "QKU_TYPE_MARKET_AGNOSTIC_RISK"
    elif qku_type == "OPTIMIZER_SETTING_QKU":
        primary = "MARKET_AGNOSTIC_OPTIMIZER"
        confidence = "MEDIUM_FORMULA_REQUIREMENT_INFERRED"
        method = "QKU_TYPE_MARKET_AGNOSTIC_OPTIMIZER"
    elif qku_type in {"AGENT_BINDING_QKU", "LATENCY_QKU"}:
        primary = "MARKET_AGNOSTIC_GOVERNANCE"
        confidence = "HIGH_EXPLICIT_AGENT_ROUTE"
        method = "QKU_TYPE_AGENT_OR_LATENCY_GOVERNANCE"
    elif qku_type == "ATOMICROW_QKU":
        primary = "MARKET_AGNOSTIC_FEATURE"
        confidence = "HIGH_EXPLICIT_INPUT_FIELD_BINDING"
        method = "ATOMICROW_STAGE1_FIELD_BINDING"
    else:
        primary = "UNKNOWN_MARKET_SCOPE"
        confidence = "UNKNOWN_REQUIRES_OWNER_REVIEW"
        method = "NO_RELIABLE_MARKET_SCOPE"
    compatible = _compatible_scopes(primary)
    excluded = [scope for scope in c.MARKET_SCOPES if scope not in compatible and scope != primary]
    stage1_allowed = primary in c.STAGE1_ALLOWED_MARKET_SCOPES
    return {
        "primary_market_scope": primary,
        "compatible_market_scopes": compatible,
        "excluded_market_scopes": excluded,
        "market_scope_confidence": confidence,
        "classification_method": method,
        "classification_evidence_refs": [
            qku.get("qku_source_artifact_path"),
            "docs/master_plan/generated/PR161C_QKUCanonicalRegistry.report.json",
            "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
        ],
        "owner_review_required_flag": confidence in {
            "LOW_NAME_HEURISTIC_ONLY",
            "UNKNOWN_REQUIRES_OWNER_REVIEW",
        },
        "stage1_market_scope_allowed_flag": stage1_allowed,
    }


def _compatible_scopes(primary: str) -> list[str]:
    if primary == "PREDICTION_MARKET_BINARY_EVENT_CONTRACT":
        return [
            "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
            "NON_MARKET_SPECIFIC",
            "MARKET_AGNOSTIC_MATH",
            "MARKET_AGNOSTIC_FEATURE",
            "MARKET_AGNOSTIC_RISK",
            "MARKET_AGNOSTIC_OPTIMIZER",
            "MARKET_AGNOSTIC_GOVERNANCE",
        ]
    if primary in c.STAGE1_ALLOWED_MARKET_SCOPES:
        return [primary, "PREDICTION_MARKET_BINARY_EVENT_CONTRACT"]
    return [primary]


def market_classification_records(qkus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for qku in qkus:
        classified = classify_market_scope(qku)
        records.append(
            {
                "record_id": f"PR162B-MARKET-{qku['qku_id']}",
                "qku_id": qku["qku_id"],
                "qku_family": qku.get("qku_type"),
                **classified,
                "stage1_prediction_market_activation_status": "PENDING_EXECUTION_CLASSIFICATION",
                "dormancy_status": "PENDING_EXECUTION_CLASSIFICATION",
                "created_by_pr": c.PR_ID,
            }
        )
    return records
