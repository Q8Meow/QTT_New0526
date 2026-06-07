"""PR163-B evidence review registry."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields
from .deterministic_ids import candidate_index, plain_ref


def build_evidence_review_rows(
    handoff_rows: list[dict[str, Any]],
    divergence_by_candidate: dict[str, dict[str, Any]],
    tca_by_candidate: dict[str, dict[str, Any]],
    remediation_by_candidate: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for row in sorted(handoff_rows, key=lambda item: item["candidate_packet_id"]):
        cid = row["candidate_packet_id"]
        idx = candidate_index(cid)
        divergence = divergence_by_candidate.get(cid, {})
        tca = tca_by_candidate.get(cid, {})
        remediation = remediation_by_candidate.get(cid, {})
        rows.append(
            {
                "evidence_review_ref": plain_ref("EVIDENCE_REVIEW", idx),
                "candidate_id": cid,
                "qku_ids": list(row.get("qku_ids") or []),
                "evidence_id": f"PR163B_PR164_HANDOFF::{idx:06d}",
                "paired_run_ref": row.get("paired_run_ref", ""),
                "comparison_ref": row.get("comparison_ref", ""),
                "divergence_ref": row.get("divergence_ref", divergence.get("divergence_ref", "")),
                "tca_ref": tca.get("tca_ref", ""),
                "remediation_ref": remediation.get("remediation_ref", ""),
                "review_status": (
                    "REVIEW_REPAIR_REQUIRED_BEFORE_PR165"
                    if remediation.get("repairability") == "REPAIRABLE_PRE_LAUNCH"
                    else "REVIEW_READY_FOR_PR165"
                ),
                "evidence_tier": "EVIDENCE_TIER_0_REPO_LOCAL_DETERMINISTIC",
                "source_truth_created": False,
                "final_replay_or_paper_result_authority_created": False,
                "profit_evidence_created": False,
                "replay_paper_materialization_route": "PR163_B_PAIRED_EVIDENCE_REVIEWED_FOR_PR165_INPUT",
                "pr165_scoring_readiness_route": (
                    "ROUTE_TO_PR163_C_INFRA_REPAIR"
                    if remediation.get("repairability") == "REPAIRABLE_PRE_LAUNCH"
                    else "ROUTE_TO_PR165_SCORING"
                ),
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows
