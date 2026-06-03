"""Source quality policy for PR162D."""

from __future__ import annotations

from . import constants as c


def source_quality_score(source_tier: str, official: bool) -> float:
    base = {
        "TIER_0": 0.92,
        "TIER_1": 0.88,
        "TIER_2": 0.76,
        "TIER_3": 0.62,
        "TIER_4": 0.45,
        "TIER_5": 0.25,
    }[source_tier]
    return min(1.0, base + (0.05 if official else 0.0))


def authority_for_source(source_tier: str, source_class: str) -> str:
    if source_tier == "TIER_0":
        return "REPO_LOCAL_CANDIDATE_NOT_LIVE_TRUTH"
    if source_class.startswith("OFFICIAL"):
        return "OFFICIAL_PUBLIC_CANDIDATE_NOT_LIVE_TRUTH"
    if source_tier == "TIER_4":
        return "SOCIAL_WEB_SIGNAL_REPLAY_PAPER_ONLY"
    return "PUBLIC_RESEARCH_CANDIDATE_NOT_OFFICIAL_TRUTH"


def confidence_for_source(source_tier: str, source_class: str) -> str:
    if source_class.startswith("OFFICIAL"):
        return "HIGH_OFFICIAL_LOCATOR"
    if source_tier == "TIER_2":
        return "MEDIUM_REPUTABLE_TECHNICAL_SOURCE"
    if source_tier == "TIER_3":
        return "MEDIUM_PUBLIC_RESEARCH"
    if source_tier == "TIER_4":
        return "LOW_SOCIAL_WEB_SIGNAL"
    return "LOW_OWNER_DEFAULT_CANDIDATE"


def policy_record() -> dict[str, object]:
    return {
        "record_id": "PR162D-SOURCE-QUALITY-POLICY",
        "source_tiers": list(c.SOURCE_TIERS),
        "source_classes": list(c.SOURCE_CLASSES),
        "authority_classes": list(c.AUTHORITY_CLASSES),
        "confidence_classes": list(c.CONFIDENCE_CLASSES),
        "source_quality_is_priority_not_gate_flag": True,
        "non_official_mappable_candidate_rejection_for_source_quality_only_allowed_flag": False,
        "partial_candidate_rejection_for_missing_fields_only_allowed_flag": False,
        "hard_quarantine_reasons": list(c.HARD_QUARANTINE_REASONS),
    }
