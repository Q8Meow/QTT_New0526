"""Downstream repair trigger matrix builders."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


def build_pr162b_repair_triggers(market_scope_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    triggers = [row for row in market_scope_rows if row["market_scope"] == "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW"]
    return [
        {
            "downstream_route_record_ref": plain_ref("PR162B_R", index),
            "qku_id": row["qku_id"],
            "candidate_id": row["candidate_id"],
            "downstream_pr_route": "ROUTE_TO_PR162B_R_MARKET_SCOPE_REPAIR",
            "repair_trigger_reason": "Unknown market scope owner review required.",
            "validation_status": "PASS",
        }
        for index, row in enumerate(triggers, 1)
    ]


def build_pr162d_r3_repair_triggers(missing_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "downstream_route_record_ref": plain_ref("PR162D_R3", index),
            "qku_id": row["qku_id"],
            "candidate_id": row["candidate_id"],
            "downstream_pr_route": "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR",
            "repair_trigger_reason": row["exact_missing_field"],
            "missing_value_fill_task_ref": row["missing_value_fill_task_ref"],
            "validation_status": "PASS",
        }
        for index, row in enumerate(missing_tasks, 1)
        if row["route_to_pr162d_r3_or_pr162b_r_or_pr163c"] == "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR"
    ]


def build_pr163c_repair_triggers(infra_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    triggers = [row for row in infra_rows if row["artificial_infrastructure_rejection_flag"]]
    return [
        {
            "downstream_route_record_ref": plain_ref("PR163C", index),
            "candidate_id": row["candidate_id"],
            "qku_ids": row["qku_ids"],
            "downstream_pr_route": "ROUTE_TO_PR163_C_INFRA_REPAIR",
            "repair_trigger_reason": row["exact_repair_action"],
            "remediation_ref": row["remediation_ref"],
            "validation_status": "PASS",
        }
        for index, row in enumerate(triggers, 1)
    ]
