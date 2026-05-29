"""Source quality and risk classification for PR159S."""

from __future__ import annotations

from . import constants as c


def quality_tier_for_source_class(source_class: str) -> str:
    if source_class in c.enum_values(c.OfficialSourceClass):
        return c.SourceQualityTier.TIER_0_OFFICIAL_FACT_SOURCE.value
    if source_class in {
        c.OpenResearchSourceClass.ACADEMIC_PAPER.value,
        c.OpenResearchSourceClass.PREPRINT.value,
    }:
        return c.SourceQualityTier.TIER_1_PEER_REVIEWED_OR_FORMAL_RESEARCH.value
    if source_class in {
        c.OpenResearchSourceClass.GITHUB_REPOSITORY.value,
        c.OpenResearchSourceClass.CODE_SNIPPET_REFERENCE.value,
    }:
        return c.SourceQualityTier.TIER_2_REPRODUCIBLE_RESEARCH_OR_CODE.value
    if source_class in {
        c.OpenResearchSourceClass.BLOG_POST.value,
        c.OpenResearchSourceClass.NEWS_ARTICLE.value,
        c.OpenResearchSourceClass.NEWSLETTER.value,
        c.OpenResearchSourceClass.THIRD_PARTY_ANALYSIS.value,
        c.OpenResearchSourceClass.TRADING_ARTICLE.value,
        c.OpenResearchSourceClass.MICROSTRUCTURE_WRITEUP.value,
        c.OpenResearchSourceClass.STRATEGY_WRITEUP.value,
    }:
        return c.SourceQualityTier.TIER_3_MARKET_ANALYSIS_OR_NEWS.value
    if source_class in {
        c.OpenResearchSourceClass.SOCIAL_POST.value,
        c.OpenResearchSourceClass.X_POST.value,
        c.OpenResearchSourceClass.FORUM_THREAD.value,
    }:
        return c.SourceQualityTier.TIER_4_SOCIAL_FORUM_SIGNAL.value
    return c.SourceQualityTier.TIER_5_OWNER_SUBMITTED_OR_PRIVATE_ATTESTED.value


def source_risk_tier(source_class: str) -> str:
    if source_class in c.enum_values(c.OfficialSourceClass):
        return c.SourceRiskTier.LOW.value
    if source_class in {
        c.OpenResearchSourceClass.SOCIAL_POST.value,
        c.OpenResearchSourceClass.X_POST.value,
        c.OpenResearchSourceClass.FORUM_THREAD.value,
        c.OpenResearchSourceClass.GITHUB_REPOSITORY.value,
        c.OpenResearchSourceClass.CODE_SNIPPET_REFERENCE.value,
    }:
        return c.SourceRiskTier.HIGH.value
    if source_class in {
        c.OpenResearchSourceClass.TRADING_ARTICLE.value,
        c.OpenResearchSourceClass.STRATEGY_WRITEUP.value,
        c.OpenResearchSourceClass.THIRD_PARTY_ANALYSIS.value,
    }:
        return c.SourceRiskTier.MEDIUM.value
    return c.SourceRiskTier.LOW.value

