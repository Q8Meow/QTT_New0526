"""Online-source enrichment registry projection."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


def build_online_enrichment_registry(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "online_enrichment_record_ref": plain_ref("ONLINE_SOURCE", index),
            "network_execution_required_for_pr164_build": False,
            "external_code_executed": False,
            "online_value_treated_as_truth": False,
            "replay_paper_candidate_lane_only": True,
        }
        for index, row in enumerate(source_rows, 1)
    ]


def build_point_in_time_ledger(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "point_in_time_source_ref": plain_ref("SOURCE_PIT", index),
            "source_record_ref": row["candidate_source_record_ref"],
            "source_class": row["source_class"],
            "source_locator": row["source_locator"],
            "observed_at_utc": row["observed_at_utc"],
            "extraction_method": row["extraction_method"],
            "candidate_value_not_source_truth": True,
            "validation_status": "PASS",
        }
        for index, row in enumerate(source_rows, 1)
    ]


def build_online_source_enrichment_plan(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted = [row for row in source_rows if not row["source_policy_disposition"].startswith("REJECT_")]
    return [
        {
            "online_source_enrichment_plan_ref": plain_ref("ONLINE_PLAN", index),
            "source_record_ref": row["candidate_source_record_ref"],
            "source_class": row["source_class"],
            "source_locator": row["source_locator"],
            "planned_consumer": "PR162D_R3_ACQUISITION_REPAIR_OR_PR165_SCORING_FEATURE_SOURCE_SCOUT",
            "no_live_connector_semantics": True,
            "validation_status": "PASS",
        }
        for index, row in enumerate(accepted, 1)
    ]
