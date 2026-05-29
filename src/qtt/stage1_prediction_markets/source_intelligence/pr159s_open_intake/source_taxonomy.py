"""PR159S taxonomy report projection."""

from __future__ import annotations

from typing import Any

from . import constants as c


def build_source_taxonomy_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source_class in c.OfficialSourceClass:
        records.append(
            {
                "taxonomy_family": "OFFICIAL_SOURCE_CLASSES",
                "enum_value": source_class.value,
                "may_satisfy_official_external_fact": True,
                "may_feed_replay_paper_candidate": False,
                "executable_trust_allowed": False,
            }
        )
    for source_class in c.OpenResearchSourceClass:
        records.append(
            {
                "taxonomy_family": "OPEN_RESEARCH_SOURCE_CLASSES",
                "enum_value": source_class.value,
                "may_satisfy_official_external_fact": False,
                "may_feed_replay_paper_candidate": True,
                "executable_trust_allowed": False,
            }
        )
    for prohibited in c.ProhibitedExecutableTrustInput:
        records.append(
            {
                "taxonomy_family": "PROHIBITED_AS_EXECUTABLE_TRUST",
                "enum_value": prohibited.value,
                "may_satisfy_official_external_fact": False,
                "may_feed_replay_paper_candidate": False,
                "executable_trust_allowed": False,
                "quarantine_or_risk_summary_only": True,
            }
        )
    return records


def taxonomy_counts() -> dict[str, int]:
    return {
        "official_source_class_count": len(c.OfficialSourceClass),
        "open_research_source_class_count": len(c.OpenResearchSourceClass),
        "prohibited_executable_trust_input_count": len(c.ProhibitedExecutableTrustInput),
        "authority_class_count": len(c.AuthorityClass),
        "source_provenance_tag_count": len(c.SourceProvenanceTag),
        "profit_validation_tag_count": len(c.ProfitValidationTag),
        "terminal_completion_state_count": len(c.TerminalCompletionState),
        "atomicrows_readiness_state_count": len(c.AtomicRowsReadinessState),
        "quantum_applicability_class_count": len(c.QuantumApplicabilityClass),
    }

