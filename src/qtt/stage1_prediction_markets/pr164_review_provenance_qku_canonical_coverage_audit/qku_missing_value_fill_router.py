"""Missing-value fill task router."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


def build_missing_value_fill_tasks(computability_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(
        [item for item in computability_rows if item["missing_field_fill_task_ref"]],
        1,
    ):
        route = (
            "ROUTE_TO_PR162B_R_MARKET_SCOPE_REPAIR"
            if row["computability_disposition"] == "COMPUTABLE_AFTER_MARKET_SCOPE_REPAIR"
            else "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR"
        )
        rows.append(
            {
                "missing_value_fill_task_ref": row["missing_field_fill_task_ref"],
                "missing_value_fill_router_ref": plain_ref("MISSING_FILL", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "exact_missing_field": "candidate_packet_v1_record",
                "expected_type": "object",
                "valid_range_or_domain": "CandidatePacketV1 object with qku_ids, formulation_ref, inputs, outputs, replay_route, paper_route, and source candidate refs.",
                "candidate_source_targets": [
                    "OWNER_PROVIDED",
                    "LOCAL_REPO_DERIVED",
                    "OFFICIAL_API_DOC",
                    "ACADEMIC_RESEARCH",
                    "INSTITUTIONAL_RESEARCH",
                    "OPEN_SOURCE_REPO_RESEARCH_ONLY",
                    "SOCIAL_SIGNAL_RESEARCH_ONLY",
                    "NEWS_RESEARCH_ONLY",
                ],
                "candidate_estimation_policy_for_replay_paper": "Candidate values may be estimated for replay/paper only and must not be treated as source truth or live connector semantics.",
                "confidence_hint": "MEDIUM_FOR_LOCAL_REPO_DERIVED_LOW_FOR_NONOFFICIAL_EXTERNAL_UNTIL_VERIFIED",
                "no_live_use_until_downstream_verified_flag": True,
                "route_to_pr162d_r3_or_pr162b_r_or_pr163c": route,
                "validation_status": "PASS",
            }
        )
    return rows
