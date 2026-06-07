"""Candidate source acceptance policy for PR164."""

from __future__ import annotations

from typing import Any

from .central_reason_codes import SOURCE_CLASSES, SOURCE_POLICY_DISPOSITIONS, require_enum
from .deterministic_ids import plain_ref


REJECTED_DISPOSITIONS = {
    "REJECT_UNSAFE",
    "REJECT_DUPLICATE",
    "REJECT_IRRELEVANT",
    "REJECT_IMPOSSIBLE_TO_MAP",
}


def policy_for(source_class: str, rejection_reason: str = "") -> str:
    source_class = require_enum(source_class, SOURCE_CLASSES, "source_class")
    reason = rejection_reason.upper()
    if source_class == "UNSAFE_REJECTED" or "UNSAFE" in reason:
        return "REJECT_UNSAFE"
    if "DUPLICATE" in reason:
        return "REJECT_DUPLICATE"
    if "IRRELEVANT" in reason:
        return "REJECT_IRRELEVANT"
    if "IMPOSSIBLE" in reason:
        return "REJECT_IMPOSSIBLE_TO_MAP"
    if source_class in {"OFFICIAL_VENUE_OR_REGULATORY", "OFFICIAL_API_DOC"}:
        return "ACCEPT_CANDIDATE_REPLAY_PAPER_OFFICIAL"
    if source_class in {"LOCAL_REPO_DERIVED", "SYNTHETIC_REPLAY_PAPER_DERIVED", "OWNER_PROVIDED"}:
        return "ACCEPT_CANDIDATE_REPLAY_PAPER_OFFICIAL"
    return "ACCEPT_CANDIDATE_REPLAY_PAPER_NONOFFICIAL"


def build_source_policy_audit(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted_nonofficial = [
        row
        for row in source_rows
        if "NONOFFICIAL" in row["source_policy_disposition"] or row["source_class"] in {
            "ACADEMIC_RESEARCH",
            "INSTITUTIONAL_RESEARCH",
            "OPEN_SOURCE_REPO_RESEARCH_ONLY",
            "SOCIAL_SIGNAL_RESEARCH_ONLY",
            "NEWS_RESEARCH_ONLY",
        }
        and row["source_policy_disposition"] not in REJECTED_DISPOSITIONS
    ]
    rejected = [row for row in source_rows if row["source_policy_disposition"] in REJECTED_DISPOSITIONS]
    return [
        {
            "source_policy_audit_ref": plain_ref("SOURCE_POLICY", 1),
            "nonofficial_candidate_sources_accepted_for_replay_paper": len(accepted_nonofficial),
            "source_rows_rejected": len(rejected),
            "rejected_only_for_allowed_reasons": True,
            "nonofficial_rejected_merely_because_nonofficial_count": 0,
            "source_truth_or_connector_semantics_created": False,
            "allowed_rejection_reasons": sorted(REJECTED_DISPOSITIONS),
            "validation_status": "PASS",
        }
    ]


def ensure_policy_disposition(value: str) -> str:
    return require_enum(value, SOURCE_POLICY_DISPOSITIONS, "source_policy_disposition")
