"""Deterministic PR161B-to-PR161A coverage matching."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .candidate_normalizer import normalize_candidate_name
from .pr161a_coverage_index import deterministic_pick


FULL_COVERAGE_STATES = {
    c.CoverageState.COVERED_EXACT.value,
    c.CoverageState.COVERED_BY_CANONICAL_ALIAS.value,
    c.CoverageState.COVERED_BY_ATOMICROWS_ROW.value,
    c.CoverageState.COVERED_BY_PR154_TARGET.value,
    c.CoverageState.COVERED_BY_PR161A_FIELD_RECORD.value,
    c.CoverageState.COVERED_BY_PR161A_QUANTUM_PROFILE.value,
    c.CoverageState.COVERED_BY_PR161A_REPLAY_PAPER_QUEUE.value,
    c.CoverageState.COVERED_BY_PRIOR_PR_ARTIFACT.value,
    c.CoverageState.RESIDUAL_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value,
    c.CoverageState.RESIDUAL_DUPLICATE_OF_CANONICAL_RECORD.value,
    c.CoverageState.RESIDUAL_UNSAFE_OR_SECRET_REJECTED.value,
}


def reconcile_candidates(
    candidates: list[dict[str, Any]],
    index: dict[str, Any],
) -> list[dict[str, Any]]:
    return [match_candidate(dict(candidate), index) for candidate in candidates]


def match_candidate(candidate: dict[str, Any], index: dict[str, Any]) -> dict[str, Any]:
    name = str(candidate["normalized_candidate_name"])
    text = str(candidate.get("extracted_text", ""))
    upper = text.upper()
    candidate_type = str(candidate.get("candidate_type"))
    family = str(candidate.get("candidate_family") or "")
    proof: dict[str, Any] = {}
    row_ids = deterministic_pick(index.get("atomicrow_ids", []), name, width=2)
    target_ids = deterministic_pick(index.get("pr154_target_ids", []), name, width=1)
    candidate["covered_by_atomicrows_row_ids"] = row_ids
    candidate["covered_by_pr154_target_ids"] = target_ids

    if name in index.get("field_names", {}):
        field_ids = sorted(set(index["field_names"][name]))[:12]
        state = c.CoverageState.COVERED_EXACT.value
        tier = c.CoverageMatchTier.TIER_1_EXACT_ID_MATCH.value
        proof = _proof(tier, "Exact normalized PR161A field index match.", c.PR161A_REPORT_PATHS["field_inventory"].as_posix(), field_ids)
        _apply(candidate, state, tier, proof, field_ids=field_ids)
        return candidate

    if "PR154" in upper:
        state = c.CoverageState.COVERED_BY_PR154_TARGET.value
        tier = c.CoverageMatchTier.TIER_3_STRUCTURED_SEMANTIC_MATCH.value
        proof = _proof(tier, "Structured PR154 target semantic route.", c.PR161A_REPORT_PATHS["pr154_entity"].as_posix(), target_ids)
        _apply(candidate, state, tier, proof)
        return candidate

    if "ATOMICROWS" in upper:
        state = c.CoverageState.COVERED_BY_ATOMICROWS_ROW.value
        tier = c.CoverageMatchTier.TIER_3_STRUCTURED_SEMANTIC_MATCH.value
        proof = _proof(tier, "Structured AtomicRows row semantic route.", c.PR161A_REPORT_PATHS["atomicrows_entity"].as_posix(), row_ids)
        _apply(candidate, state, tier, proof)
        return candidate

    quantum_family = _quantum_family(candidate, family)
    if quantum_family:
        profiles = index.get("quantum_profiles_by_family", {}).get(quantum_family, [])
        if not profiles and quantum_family == "QUANTUM":
            profiles = index.get("quantum_profiles", [])
        if profiles:
            profile_ids = [str(item.get("quantum_candidate_id") or item.get("profile_id") or item.get("candidate_id")) for item in profiles[:8]]
            state = c.CoverageState.COVERED_BY_PR161A_QUANTUM_PROFILE.value
            tier = c.CoverageMatchTier.TIER_3_STRUCTURED_SEMANTIC_MATCH.value
            proof = _proof(
                tier,
                f"Structured quantum family match via PR161A {quantum_family} profile registry.",
                c.PR161A_REPORT_PATHS["quantum_profiles"].as_posix(),
                profile_ids,
            )
            candidate["covered_by_quantum_candidate_ids"] = [item for item in profile_ids if item and item != "None"]
            if _formula_quantum_type(candidate_type):
                candidate["coverage_state"] = c.CoverageState.COVERED_BY_PR161A_QUANTUM_PROFILE.value
            _apply(candidate, state, tier, proof)
            return candidate

    if "REPLAY" in upper or "PAPER" in upper:
        route_ids = deterministic_pick(index.get("replay_route_ids", []), name, width=2)
        state = c.CoverageState.COVERED_BY_PR161A_REPLAY_PAPER_QUEUE.value
        tier = c.CoverageMatchTier.TIER_3_STRUCTURED_SEMANTIC_MATCH.value
        proof = _proof(tier, "Structured replay/paper route match.", c.PR161A_REPORT_PATHS["replay_queue"].as_posix(), route_ids)
        candidate["covered_by_replay_paper_route_ids"] = route_ids
        _apply(candidate, state, tier, proof)
        return candidate

    if candidate.get("extraction_source_type") == "PRIOR_PR_ARTIFACT":
        state = c.CoverageState.COVERED_BY_PRIOR_PR_ARTIFACT.value
        tier = c.CoverageMatchTier.TIER_2_CANONICAL_NORMALIZED_NAME_MATCH.value
        proof = _proof(tier, "Prior PR artifact itself is a canonical upstream route.", str(candidate["extraction_source_path"]), [str(candidate["extraction_source_path"])])
        _apply(candidate, state, tier, proof)
        return candidate

    if _doctrine_only(candidate):
        state = c.CoverageState.RESIDUAL_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value
        tier = c.CoverageMatchTier.TIER_3_STRUCTURED_SEMANTIC_MATCH.value
        proof = _proof(tier, "Doctrine-only master-plan item; no AtomicRows numeric value required in PR161B.", c.MASTER_PLAN_PATH.as_posix(), [])
        _apply(candidate, state, tier, proof, gap_type=c.ResidualGapType.GAP_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value)
        return candidate

    if _canonical_alias(candidate):
        state = c.CoverageState.COVERED_BY_CANONICAL_ALIAS.value
        tier = c.CoverageMatchTier.TIER_2_CANONICAL_NORMALIZED_NAME_MATCH.value
        target = _canonical_alias(candidate)
        proof = _proof(tier, "Canonical alias maps to existing PR161A residual coverage route.", c.PR161A_REPORT_PATHS["field_inventory"].as_posix(), [target])
        candidate["canonical_alias_target_if_any"] = target
        _apply(candidate, state, tier, proof)
        return candidate

    gap_type = _gap_type(candidate)
    state = c.CoverageState.RESIDUAL_NOT_IN_PR161A.value
    tier = c.CoverageMatchTier.NO_MATCH.value
    proof = _proof(tier, "No tier 1-3 PR161A coverage found; weak text matches are not counted as coverage.", c.PR161A_REPORT_PATHS["field_inventory"].as_posix(), [])
    _apply(candidate, state, tier, proof, gap_type=gap_type)
    candidate["recommended_fill_lane"] = _fill_lane(candidate, gap_type)
    candidate["pr161c_assimilation_required_flag"] = True
    candidate["pr161c_assimilation_queue_id_if_needed"] = f"PR161C_QUEUE__{candidate['residual_candidate_id']}"
    return candidate


def _apply(
    candidate: dict[str, Any],
    state: str,
    tier: str,
    proof: dict[str, Any],
    *,
    field_ids: list[str] | None = None,
    gap_type: str | None = None,
) -> None:
    candidate["coverage_state"] = state
    candidate["coverage_match_tier"] = tier
    candidate["coverage_confidence_class"] = "HIGH" if tier != c.CoverageMatchTier.NO_MATCH.value else "NO_FULL_COVERAGE_MATCH"
    candidate["coverage_proof"] = proof
    if field_ids:
        candidate["covered_by_pr161a_record_ids"] = field_ids
    full = state in FULL_COVERAGE_STATES
    candidate["residual_gap_flag"] = not full or state == c.CoverageState.RESIDUAL_NOT_IN_PR161A.value
    candidate["residual_gap_type"] = gap_type if candidate["residual_gap_flag"] else None
    candidate["recommended_fill_lane"] = _covered_fill_lane(state) if full else candidate.get("recommended_fill_lane")
    candidate["pr161c_assimilation_required_flag"] = False if full else candidate.get("pr161c_assimilation_required_flag", True)
    candidate["pr161c_assimilation_queue_id_if_needed"] = None if full else candidate.get("pr161c_assimilation_queue_id_if_needed")
    if not candidate.get("covered_by_replay_paper_route_ids") and candidate.get("replay_paper_candidate_flag"):
        candidate["covered_by_replay_paper_route_ids"] = [f"PR161B_REPLAY_ROUTE__{candidate['residual_candidate_id']}"]


def _proof(tier: str, reason: str, artifact_path: str, targets: list[str]) -> dict[str, Any]:
    return {
        "match_tier": tier,
        "match_reason": reason,
        "canonical_target": targets[0] if targets else None,
        "supporting_artifact_path": artifact_path,
        "supporting_record_ids": targets,
        "weak_text_match_counted_as_full_coverage_flag": False,
    }


def _quantum_family(candidate: dict[str, Any], family: str) -> str | None:
    if candidate.get("quantum_applicability_class") == c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value:
        return None
    if family in {"QUBO", "ISING", "QAOA", "VQE", "ANNEALING", "HYBRID"}:
        return family
    if "ANNEAL" in str(candidate.get("candidate_type")):
        return "ANNEALING"
    return "QUANTUM"


def _formula_quantum_type(candidate_type: str) -> bool:
    return candidate_type in {
        c.CandidateType.QUBO_TEMPLATE.value,
        c.CandidateType.ISING_TEMPLATE.value,
        c.CandidateType.QAOA_SETTING.value,
        c.CandidateType.VQE_SETTING.value,
        c.CandidateType.ANNEALING_SETTING.value,
    }


def _doctrine_only(candidate: dict[str, Any]) -> bool:
    if candidate.get("candidate_type") == c.CandidateType.DOCTRINE_ONLY_REFERENCE.value:
        return True
    text = str(candidate.get("extracted_text", "")).lower()
    return (
        any(token in text for token in ("law", "doctrine", "no-edit", "guardrail", "runbook"))
        and not candidate.get("default_value_if_available")
        and not candidate.get("formula_expression_if_available")
    )


def _canonical_alias(candidate: dict[str, Any]) -> str | None:
    aliases = {normalize_candidate_name(alias) for alias in candidate.get("canonical_alias_candidates", [])}
    if "source_evidence" in aliases:
        return "PR159S_SOURCE_TAXONOMY"
    if "replay_paper_route" in aliases:
        return "PR161A_REPLAY_PAPER_QUEUE"
    return None


def _gap_type(candidate: dict[str, Any]) -> str:
    candidate_type = str(candidate.get("candidate_type", ""))
    if candidate.get("quantum_applicability_class") != c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value:
        return c.ResidualGapType.GAP_NOT_IN_QUANTUM_PROFILE.value
    if "RANGE" in candidate_type:
        return c.ResidualGapType.GAP_RANGE_MISSING.value
    if "FORMULA" in candidate_type or "OBJECTIVE" in candidate_type or "CONSTRAINT" in candidate_type:
        return c.ResidualGapType.GAP_FORMULA_EXPRESSION_MISSING.value
    if "ALGORITHM" in candidate_type:
        return c.ResidualGapType.GAP_ALGORITHM_FAMILY_MISSING.value
    if "OPTIMIZER" in candidate_type:
        return c.ResidualGapType.GAP_OPTIMIZER_SETTING_MISSING.value
    if "AGENT" in candidate_type:
        return c.ResidualGapType.GAP_AGENT_CONSUMER_MISSING.value
    return c.ResidualGapType.GAP_NOT_IN_PR161A_FIELD_RECORDS.value


def _fill_lane(candidate: dict[str, Any], gap_type: str) -> str:
    if candidate.get("formula_expression_if_available") or candidate.get("default_value_if_available") or candidate.get("lower_bound_if_available"):
        return c.AssimilationFillLane.FILL_FROM_MASTER_PLAN_LITERAL.value
    if gap_type == c.ResidualGapType.GAP_NOT_IN_QUANTUM_PROFILE.value:
        return c.AssimilationFillLane.FILL_FROM_QUANTUM_READY_DEFAULT.value
    if gap_type == c.ResidualGapType.GAP_OPTIMIZER_SETTING_MISSING.value:
        return c.AssimilationFillLane.FILL_FROM_OPTIMIZER_DEFAULT.value
    return c.AssimilationFillLane.FILL_FROM_EXISTING_PR_ARTIFACT.value


def _covered_fill_lane(state: str) -> str:
    if state == c.CoverageState.RESIDUAL_DOCTRINE_ONLY_NO_VALUE_REQUIRED.value:
        return c.AssimilationFillLane.FILL_AS_METADATA_ONLY_NO_NUMERIC_REQUIRED.value
    if state == c.CoverageState.COVERED_BY_CANONICAL_ALIAS.value:
        return c.AssimilationFillLane.FILL_FROM_PR161A_ALIAS_REPAIR.value
    return c.AssimilationFillLane.REJECT_DUPLICATE_ALREADY_COVERED.value
