"""Source/profit provenance classification for PR159S targets."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .source_quality_tier import quality_tier_for_source_class, source_risk_tier
from .terminal_completion import is_testable_candidate_target, terminal_state_for_target


_STATE_TO_AUTHORITY_AND_PROVENANCE = {
    c.TerminalCompletionState.COMPLETED_AS_OPEN_RESEARCH_INPUT.value: (
        c.AuthorityClass.ACCEPTED_OPEN_RESEARCH_INPUT.value,
        c.SourceProvenanceTag.OPEN_RESEARCH_INPUT_TESTABLE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_ALGORITHM_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_ALGORITHM_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_ALGORITHM_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_FORMULA_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_FORMULA_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_FORMULA_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_PARAMETER_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_PARAMETER_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_PARAMETER_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_EDGE_HYPOTHESIS_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_EDGE_HYPOTHESIS_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_RESEARCH_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_MICROSTRUCTURE_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_MICROSTRUCTURE_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_MICROSTRUCTURE_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_QUANTUM_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_QUANTUM_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_QUANTUM_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_CLASSICAL_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_CLASSICAL_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_CLASSICAL_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_HYBRID_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_HYBRID_CANDIDATE.value,
        c.SourceProvenanceTag.NON_OFFICIAL_HYBRID_CANDIDATE.value,
    ),
    c.TerminalCompletionState.COMPLETED_AS_REPLAY_PAPER_TEST_CANDIDATE.value: (
        c.AuthorityClass.ACCEPTED_REPLAY_PAPER_TEST_CANDIDATE.value,
        c.SourceProvenanceTag.OPEN_RESEARCH_INPUT_TESTABLE.value,
    ),
}


def _research_source_for_sequence(sequence: int) -> Mapping[str, Any]:
    catalog = c.RESEARCH_SOURCE_CATALOG
    return catalog[(sequence - 1) % len(catalog)]


def _source_classes_for_target(
    target: Mapping[str, Any],
    terminal_state: str,
    testable_sequence: int | None,
) -> tuple[Mapping[str, Any] | None, str, str, str]:
    if terminal_state == c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value:
        source_class = str(target.get("expected_source_class") or c.OfficialSourceClass.OFFICIAL_PROVIDER_DOCS.value)
        return None, source_class, quality_tier_for_source_class(source_class), source_risk_tier(source_class)
    source = _research_source_for_sequence(testable_sequence or 1)
    source_class = str(source["source_class"])
    return source, source_class, str(source["source_quality_tier"]), source_risk_tier(source_class)


def _claim_type_for_state(terminal_state: str, source: Mapping[str, Any] | None) -> str:
    if source and source.get("claim_types"):
        return str(source["claim_types"][0])
    if terminal_state == c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value:
        return c.SourceClaimType.API_FIELD_CLAIM.value
    return c.SourceClaimType.STRATEGY_CLAIM.value


def _field_value_for_classification(
    target: Mapping[str, Any],
    terminal_state: str,
    source: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if terminal_state == c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value:
        return {
            "value_materialization_state": "official_exact_field_route_created_no_value_accepted_in_pr159s",
            "target_field_id": target.get("target_field_id"),
            "future_route": "exact_official_connector_or_provider_field_capture",
        }
    return {
        "value_materialization_state": "research_candidate_route_created_no_profit_result_in_pr159s",
        "candidate_family": source.get("candidate_family") if source else "open_research_candidate",
        "target_field_id": target.get("target_field_id"),
    }


def classify_target(target: Mapping[str, Any], testable_sequence: int | None) -> dict[str, Any]:
    terminal_state = terminal_state_for_target(target, testable_sequence)
    source, source_class, quality_tier, risk_tier = _source_classes_for_target(
        target,
        terminal_state,
        testable_sequence,
    )
    if terminal_state == c.TerminalCompletionState.COMPLETED_AS_CONNECTOR_FUTURE_ROUTE.value:
        authority_class = c.AuthorityClass.ACCEPTED_OPEN_RESEARCH_INPUT.value
        source_provenance_tag = c.SourceProvenanceTag.OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD.value
        profit_validation_tag = c.ProfitValidationTag.PROMOTION_EVIDENCE_NOT_IN_SCOPE_FOR_THIS_PR.value
        replay_paper_candidate_flag = False
        row_aggregate = c.RowLevelAggregateProvenanceTag.ROW_RESEARCH_CANDIDATE_ONLY.value
    else:
        authority_class, source_provenance_tag = _STATE_TO_AUTHORITY_AND_PROVENANCE[terminal_state]
        profit_validation_tag = c.ProfitValidationTag.PROFIT_NOT_TESTED.value
        replay_paper_candidate_flag = True
        row_aggregate = c.RowLevelAggregateProvenanceTag.ROW_PENDING_PROFIT_TEST.value

    source_locator = source.get("source_locator") if source else None
    source_artifact_path = None if source else c.PR159R_UNRESOLVED_FILL_PATH.as_posix()
    claim_type = _claim_type_for_state(terminal_state, source)
    atomicrows_linked = bool(target.get("atomicrows_linked_flag"))

    return {
        "field_id": target.get("target_field_id"),
        "field_name": target.get("requested_value_name") or target.get("target_field_id"),
        "field_value": _field_value_for_classification(target, terminal_state, source),
        "terminal_completion_state": terminal_state,
        "source_provenance_tag": source_provenance_tag,
        "authority_class": authority_class,
        "source_class": source_class,
        "source_quality_tier": quality_tier,
        "source_risk_tier": risk_tier,
        "source_claim_type": claim_type,
        "profit_validation_tag": profit_validation_tag,
        "official_confirmed_flag": False,
        "replay_paper_candidate_flag": replay_paper_candidate_flag,
        "replay_paper_result_link": None,
        "official_source_packet_id": None,
        "prior_pr_label": None,
        "last_verified_pr_label": c.PR_ID,
        "source_locator": source_locator,
        "source_artifact_path": source_artifact_path,
        "extraction_basis": "target identity plus source taxonomy route classification; no new official value or profit result accepted",
        "promotion_limitations": [
            "live_use_forbidden_until_replay_paper_and_owner_review_if_candidate",
            "official_venue_connector_facts_still_required_before_live",
            "no_runtime_order_profit_or_optimizer_execution_in_pr159s",
        ],
        "row_level_aggregate_provenance_tag": row_aggregate if atomicrows_linked else None,
        "live_use_pending_flag": True,
        "author_identity_known_flag": bool(source and source.get("author_or_handle")),
        "reproducibility_level": source.get("reproducibility_level") if source else "official_source_discovery_route",
        "evidence_strength": source.get("evidence_strength") if source else "exact_official_field_required",
        "hallucination_risk": source.get("hallucination_risk") if source else "LOW",
        "manipulation_risk": source.get("manipulation_risk") if source else "LOW",
        "duplicate_or_near_duplicate_status": "UNIQUE_TARGET_ROUTE",
        "replay_paper_required_flag": replay_paper_candidate_flag,
        "live_use_forbidden_until_promoted_flag": True,
        "assigned_research_source_id": source.get("source_id") if source else None,
        "source_title": source.get("title") if source else None,
        "publication_time_if_available": source.get("publication_time_if_available") if source else None,
    }


def source_provenance_bucket(record: Mapping[str, Any]) -> str:
    tag = str(record.get("source_provenance_tag"))
    profit = str(record.get("profit_validation_tag"))
    if tag in {
        c.SourceProvenanceTag.OFFICIAL_CONFIRMED.value,
        c.SourceProvenanceTag.OFFICIAL_CONFIRMED_REUSED_FROM_PREVIOUS_PR.value,
    }:
        return "official_confirmed_total"
    if tag == c.SourceProvenanceTag.OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD.value:
        return "official_candidate_pending_exact_field_total"
    if profit == c.ProfitValidationTag.REPLAY_AND_PAPER_PROFITABLE.value:
        return "non_official_profit_proven_total"
    if profit == c.ProfitValidationTag.REPLAY_AND_PAPER_NON_PROFITABLE.value:
        return "non_official_non_profitable_total"
    if tag == c.SourceProvenanceTag.MIXED_OFFICIAL_AND_RESEARCH.value:
        return "mixed_official_and_research_total"
    if tag in {
        c.SourceProvenanceTag.OWNER_SUPPLIED_INTERNAL_POLICY.value,
        c.SourceProvenanceTag.OWNER_SUPPLIED_RESEARCH_INPUT.value,
    }:
        return "owner_policy_input_total"
    if tag in {
        c.SourceProvenanceTag.QUARANTINED_SECURITY_RISK.value,
        c.SourceProvenanceTag.REJECTED_DUPLICATE_IRRELEVANT_OR_UNSAFE.value,
    }:
        return "quarantined_or_rejected_total"
    if tag == c.SourceProvenanceTag.OPEN_RESEARCH_INPUT_UNTESTED.value:
        return "open_research_untested_total"
    return "open_research_testable_total"


def profit_validation_bucket(record: Mapping[str, Any]) -> str:
    tag = str(record.get("profit_validation_tag"))
    return {
        c.ProfitValidationTag.PROFIT_NOT_TESTED.value: "profit_not_tested_total",
        c.ProfitValidationTag.REPLAY_PROFITABLE.value: "replay_profitable_total",
        c.ProfitValidationTag.PAPER_PROFITABLE.value: "paper_profitable_total",
        c.ProfitValidationTag.REPLAY_AND_PAPER_PROFITABLE.value: "replay_and_paper_profitable_total",
        c.ProfitValidationTag.REPLAY_NON_PROFITABLE.value: "replay_non_profitable_total",
        c.ProfitValidationTag.PAPER_NON_PROFITABLE.value: "paper_non_profitable_total",
        c.ProfitValidationTag.REPLAY_AND_PAPER_NON_PROFITABLE.value: "replay_and_paper_non_profitable_total",
        c.ProfitValidationTag.REPLAY_PAPER_CONFLICTING.value: "replay_paper_conflicting_total",
        c.ProfitValidationTag.REPLAY_PAPER_INCONCLUSIVE.value: "replay_paper_inconclusive_total",
        c.ProfitValidationTag.PROMOTION_EVIDENCE_NOT_IN_SCOPE_FOR_THIS_PR.value: "promotion_evidence_not_in_scope_total",
    }.get(tag, "profit_not_tested_total")


def is_testable_target(target: Mapping[str, Any]) -> bool:
    return is_testable_candidate_target(target)

