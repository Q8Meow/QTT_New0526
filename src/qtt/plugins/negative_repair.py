"""Negative candidate repair helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NegativeRepairClassification:
    row_ref: str
    root_cause_code: str
    repair_action: str
    materialization_status: str
    retest_route: str
    terminal_reason: str = ""


def classify_negative_row(row: dict[str, object]) -> NegativeRepairClassification:
    row_ref = str(row.get("row_id") or row.get("plugin_need_id") or "UNKNOWN_ROW")
    if row.get("stale_book_flag"):
        return NegativeRepairClassification(
            row_ref=row_ref,
            root_cause_code="STALE_BOOK_FAILURE",
            repair_action="stale-book repair",
            materialization_status="POST_REPAIR_RETEST_READY",
            retest_route=str(row.get("downstream_pr166_qc_retest_route_ref") or "PR162E_PostRepairRetestQueue.report.json"),
        )
    if row.get("simulator_repair_flag") or row.get("still_negative_after_costs_flag"):
        return NegativeRepairClassification(
            row_ref=row_ref,
            root_cause_code="MODEL_EXECUTION_GAP_FAILURE",
            repair_action="implementation-shortfall adjustment",
            materialization_status="POST_REPAIR_RETEST_READY",
            retest_route=str(row.get("downstream_pr166_qc_retest_route_ref") or "PR162E_PostRepairRetestQueue.report.json"),
        )
    return NegativeRepairClassification(
        row_ref=row_ref,
        root_cause_code="UNKNOWN_REQUIRES_AGENT_REVIEW",
        repair_action="agent diagnostic review",
        materialization_status="COMPUTABLE_REPAIR_READY",
        retest_route="PR162E_PostRepairRetestQueue.report.json",
    )
