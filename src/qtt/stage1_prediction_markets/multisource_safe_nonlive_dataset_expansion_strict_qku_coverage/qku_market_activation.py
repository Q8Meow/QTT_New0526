"""PR162C market, activation, and dormancy continuity records."""

from __future__ import annotations

from typing import Any

from . import constants as c


def market_continuity_records(qkus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-MARKET-CONTINUITY-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "primary_market_scope": record["primary_market_scope"],
            "compatible_market_scopes": record["compatible_market_scopes"],
            "excluded_market_scopes": record["excluded_market_scopes"],
            "continuity_status": "PASS",
            "created_by_pr": c.PR_ID,
        }
        for record in qkus
    ]


def activation_continuity_records(qkus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-ACTIVATION-CONTINUITY-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "stage1_prediction_market_activation_status": record[
                "stage1_prediction_market_activation_status"
            ],
            "execution_class": record["primary_execution_class"],
            "execution_router_allowed_flag": False,
            "continuity_status": "PASS",
            "created_by_pr": c.PR_ID,
        }
        for record in qkus
    ]


def dormancy_continuity_records(qkus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-DORMANCY-CONTINUITY-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "dormancy_status": record["dormancy_status"],
            "dormant_qku_execution_router_excluded_flag": True,
            "continuity_status": "PASS",
            "created_by_pr": c.PR_ID,
        }
        for record in qkus
    ]


def market_input_field_requirement_records(qkus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162C-MARKET-FIELD-REQ-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "primary_market_scope": record["primary_market_scope"],
            "required_input_fields": record["required_input_fields"],
            "market_scope_supported_flag": record["primary_market_scope"] in c.MARKET_SCOPES,
            "created_by_pr": c.PR_ID,
        }
        for record in qkus
    ]
