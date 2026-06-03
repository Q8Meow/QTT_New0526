"""Source quality scoring for PR162D-R1."""

from __future__ import annotations


def score_source(source_tier: str, official_truth_flag: bool) -> tuple[float, str, str]:
    if official_truth_flag and source_tier.startswith("TIER_1"):
        return 0.94, "OFFICIAL_PUBLIC_DOC_CANDIDATE", "HIGH_OFFICIAL_LOCATOR"
    if source_tier.startswith("TIER_2"):
        return 0.82, "REPUTABLE_RESEARCH_CANDIDATE", "MEDIUM_HIGH_RESEARCH_LOCATOR"
    if source_tier.startswith("TIER_3"):
        return 0.68, "PUBLIC_CODE_OR_RESEARCH_CANDIDATE", "MEDIUM_PUBLIC_LOCATOR"
    return 0.52, "PROVISIONAL_NON_OFFICIAL_CANDIDATE", "LOWER_CONFIDENCE_REPLAY_PAPER_REQUIRED"
