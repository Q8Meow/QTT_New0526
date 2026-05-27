"""AtomicRows aggregate ingestion lane for PR156."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c
from .io import as_mapping
from .models import AtomicRowsUniverseState, OptionalArtifactSet


def atomicrows_universe_state(
    pr137r_payload: Mapping[str, Any],
    optional: OptionalArtifactSet,
) -> AtomicRowsUniverseState:
    validation = as_mapping(pr137r_payload.get("atomicrows_validation_state"))
    count_proven = validation.get("row_count_proven") is True
    row_count = validation.get("row_count_value")
    optional_paths = tuple(
        sorted(
            str(item["artifact_path"])
            for item in optional.consumed_artifacts
            if item.get("artifact_key") in c.ATOMICROWS_OPTIONAL_KEYS
        )
    )
    source_paths = tuple(
        sorted(
            {
                c.PR137R_RECONCILIATION_PATH.as_posix(),
                c.PR138_SEMANTIC_CONTRACT_PATH.as_posix(),
                *optional_paths,
            }
        )
    )
    if count_proven and row_count == c.EXPECTED_ATOMICROWS_UNIVERSE_COUNT:
        return AtomicRowsUniverseState(
            confirmed_count=c.EXPECTED_ATOMICROWS_UNIVERSE_COUNT,
            count_state=c.ATOMICROWS_UNIVERSE_COUNT_CONFIRMED,
            source_artifact_paths=source_paths,
            missing_source_state=None,
        )
    return AtomicRowsUniverseState(
        confirmed_count=None,
        count_state=c.ATOMICROWS_UNIVERSE_COUNT_UNCONFIRMED,
        source_artifact_paths=source_paths,
        missing_source_state=c.PR156_ATOMICROWS_UNIVERSE_SOURCE_MISSING_AGGREGATE_ONLY,
    )


def build_atomicrows_universe_record(state: AtomicRowsUniverseState) -> dict[str, Any]:
    block_codes = (
        [state.missing_source_state] if state.missing_source_state is not None else []
    )
    return {
        "pr156_record_id": "PR156__ATOMICROWS_UNIVERSE_INGESTION__AGGREGATE",
        "record_kind": c.ATOMICROWS_UNIVERSE_INGESTION_SUMMARY_RECORD,
        "source_population": c.SOURCE_POPULATION_ATOMICROWS_UNIVERSE,
        "source_record_ref": "ATOMICROWS_UNIVERSE_AGGREGATE",
        "source_record_type": c.SOURCE_RECORD_TYPE_ATOMICROWS_AGGREGATE,
        "source_artifact_path": c.PR137R_RECONCILIATION_PATH.as_posix(),
        "source_authority_class": c.AUTHORITY_CLASS,
        "population_lane": c.ATOMICROWS_UNIVERSE_COMPLETION_INGESTION_LANE,
        "agent_binding_state": c.BINDING_PENDING_ATOMICROWS_COMPLETION,
        "bound_agent_ids": [],
        "bound_agent_roles": [],
        "bound_consumer_classes": [],
        "binding_basis_artifacts": list(state.source_artifact_paths),
        "binding_basis_reason": c.ATOMICROWS_COMPLETION_BINDING_REASON,
        "binding_block_codes": [c.PR156_ATOMICROWS_COMPLETION_REQUIRED, *block_codes],
        "template_type": None,
        "candidate_instance_state": c.CANDIDATE_INSTANCE_PENDING_ATOMICROWS_MAPPING,
        "candidate_origin": c.SOURCE_POPULATION_ATOMICROWS_UNIVERSE,
        "candidate_origin_authority_class": c.AUTHORITY_CLASS,
        "candidate_research_intake_state": c.SOURCE_EVIDENCE_PENDING_ATOMICROWS_MAPPING,
        "applicability_class": c.APPLICABILITY_PENDING_CLASSIFICATION,
        "owner_strategy_priority_state": c.STRATEGY_PRIORITY_PENDING_OWNER_POLICY,
        "atomicrows_ingestion_state": state.count_state,
        "scoring_ranking_readiness_state": c.SCORING_RANKING_PENDING_ATOMICROWS_MAPPING,
        "optimizer_routing_hint": c.OPTIMIZER_ROUTING_PENDING_CLASSIFICATION,
        "replay_paper_routing_hint": c.REPLAY_PAPER_PENDING_ATOMICROWS_COMPLETION,
        "market_scope": "PREDICTION_MARKETS_GENERAL",
        "platform_scope": "PREDICTION_MARKETS_GENERAL",
        "route_triage_domain": "PR136_ROUTE_TRIAGE_RECEIPT",
        "launch_readiness_domain": c.NO_EXACT_PR136_RECORD_MAPPING,
        "section_crosswalk_refs": [],
        "market_specific_index_refs": [],
        "command_action_matrix_refs": [],
        "atomicrows_reconciliation_refs": [
            {
                "report_path": c.PR137R_RECONCILIATION_PATH.as_posix(),
                "row_count_proven": state.count_state
                == c.ATOMICROWS_UNIVERSE_COUNT_CONFIRMED,
                "row_count_value": state.confirmed_count,
                "not_bundle_authority": True,
            }
        ],
        "atomicrows_semantic_contract_refs": [
            {
                "report_path": c.PR138_SEMANTIC_CONTRACT_PATH.as_posix(),
                "semantic_contract_consumed": True,
            }
        ],
        "pr155_registry_ref": None,
        "pr154_completion_ref": None,
        "blocked_completion_path_ref_or_inline": None,
        "future_completion_pr_hint": c.FUTURE_COMPLETION_PR_HINT,
        "future_scoring_ranking_pr_hint": c.FUTURE_SCORING_RANKING_PR_HINT,
        "future_optimizer_pr_hint": c.FUTURE_OPTIMIZER_PR_HINT,
        "future_replay_paper_pr_hint": c.FUTURE_REPLAY_PAPER_PR_HINT,
        **dict(c.NON_AUTHORITY_BOUNDARY),
        "non_authority_boundary": dict(c.NON_AUTHORITY_BOUNDARY),
        "created_by_pr": c.PR_ID,
        "authority_boundary": authority_boundary(),
    }


def authority_boundary() -> dict[str, Any]:
    return {
        "authority_class": c.AUTHORITY_CLASS,
        "atomicrows_universe_record_is_aggregate_only": True,
        "atomicrows_bundle_authority_created": False,
        "atomicrows_bundle_hash_authority_created": False,
        **dict(c.AUTHORITY_BOUNDARY_FALSE_FLAGS),
    }
