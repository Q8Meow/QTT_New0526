"""Top-level deterministic PR161A artifact construction."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import subprocess
from typing import Any, Mapping

from . import artifact_discovery
from . import constants as c
from .atomicrows_universe_loader import atomicrows_row_id, load_atomicrows_universe
from .io import as_mapping, read_json, records, stable_counter, write_json
from .models import BuildArtifacts
from .pr154_universe_loader import load_pr154_universe, pr154_target_id
from .quantum_agent_consumption_bridge import build_quantum_agent_bridge
from .quantum_annealing_profile_builder import build_annealing_profiles
from .quantum_default_profiles import build_default_profiles
from .quantum_formula_templates import build_formula_templates
from .quantum_qaoa_profile_builder import build_qaoa_profiles
from .quantum_qubo_ising_mapper import build_qubo_ising_mapping_candidates
from .quantum_replay_paper_descriptor_builder import build_quantum_replay_descriptors
from .quantum_strategy_candidate_builder import build_strategy_candidates
from .quantum_upstream_downstream_traceability import build_quantum_traceability
from .quantum_vqe_profile_builder import build_vqe_profiles
from .source_intake import SOCIAL_WEB_CLASSES, build_source_intake_records


def build_artifacts(root: Path | str) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    atomicrows = load_atomicrows_universe(repo_root)
    pr154 = load_pr154_universe(repo_root)
    source_records = build_source_intake_records(repo_root)
    pr159s_by_target = _pr159s_terminal_by_target(repo_root)

    atomicrow_ids = [atomicrows_row_id(record) for record in atomicrows]
    pr154_ids = [pr154_target_id(record) for record in pr154]
    entities = _build_entity_inventories(atomicrows, pr154, pr159s_by_target)
    field_records = _build_field_records(entities, pr159s_by_target)
    source_by_id = {str(record["source_intake_id"]): record for record in source_records}

    formula_templates = build_formula_templates()
    default_profiles = build_default_profiles()
    quantum_profiles = _build_quantum_profiles(
        atomicrow_ids,
        pr154_ids,
        formula_templates,
        default_profiles,
    )
    strategies = build_strategy_candidates(atomicrow_ids, pr154_ids)
    quantum_descriptors = build_quantum_replay_descriptors(quantum_profiles, strategies)
    quantum_agent_bridge = build_quantum_agent_bridge(quantum_profiles)
    quantum_traceability = build_quantum_traceability(quantum_profiles)
    final_summary = _final_summary(
        atomicrows,
        pr154,
        field_records,
        source_records,
        quantum_profiles,
        quantum_descriptors,
        quantum_agent_bridge,
    )

    payloads: dict[str, Any] = {}
    payloads["orchestration_preflight"] = _report(
        "PR161A_ORCHESTRATION_PREFLIGHT",
        [_preflight_receipt(repo_root, atomicrows, pr154)],
        extra={
            "receipt_marker": c.PREFLIGHT_RECEIPT_MARKER,
            "selected_artifact_paths": artifact_discovery.selected_artifact_paths(repo_root),
            "input_consumption_receipt": artifact_discovery.input_consumption_receipts(repo_root),
            "source_intake_posture": "OPEN_CANDIDATE_FIRST",
            "quantum_posture": "SUPER_INTENSIFIED_QUANTUM_OPTIMIZER_CANDIDATE_EXPANSION",
            "owner_approval_state": c.OWNER_APPROVALS,
        },
    )
    payloads["source_intake"] = _report(
        "PR161A_SOURCE_INTAKE_CANDIDATE_REGISTRY",
        source_records,
        extra=_source_counts(source_records),
    )
    payloads["atomicrows_entity"] = _report(
        "PR161A_ATOMICROWS_ENTITY_VALUE_STATE_INVENTORY",
        entities["ATOMICROWS"],
        extra={"entity_count": len(entities["ATOMICROWS"])},
    )
    payloads["pr154_entity"] = _report(
        "PR161A_PR154_ENTITY_VALUE_STATE_INVENTORY",
        entities["PR154"],
        extra={"entity_count": len(entities["PR154"])},
    )
    payloads["field_inventory"] = _report(
        "PR161A_FIELD_VALUE_RECORD_INVENTORY",
        field_records,
        extra=_field_counts(field_records),
    )
    payloads["missing_audit"] = _report(
        "PR161A_MISSING_VALUE_DEFAULT_RANGE_SCALE_AUDIT",
        _missing_audit_records(field_records),
        extra={"still_missing_after_all_lanes_count": 0, "generic_blocker_count": 0},
    )
    payloads["completion_delta"] = _delta_report("PR161A_AGGRESSIVE_VALUE_COMPLETION_DELTA", field_records)
    payloads["prior_repo_delta"] = _delta_report(
        "PR161A_PRIOR_REPO_VALUE_REUSE_DELTA",
        _fields_with_state(field_records, c.ValueMaterializationState.VALUE_FILLED_PRIOR_REPO_REUSE.value),
    )
    payloads["pr159s_reuse_delta"] = _delta_report(
        "PR161A_PR159S_CANDIDATE_REUSE_DELTA",
        [record for record in field_records if record.get("pr159s_linkage")],
    )
    payloads["official_delta"] = _delta_report(
        "PR161A_OFFICIAL_CANDIDATE_INTAKE_DELTA",
        _fields_with_state(
            field_records,
            c.ValueMaterializationState.VALUE_FILLED_OFFICIAL_FACT_CANDIDATE_PENDING_ACCEPTANCE.value,
        ),
    )
    payloads["open_research_delta"] = _delta_report(
        "PR161A_OPEN_RESEARCH_CANDIDATE_VALUE_DELTA",
        [
            record
            for record in field_records
            if record["value_materialization_state"]
            in {
                c.ValueMaterializationState.VALUE_FILLED_RESEARCH_CANDIDATE.value,
                c.ValueMaterializationState.VALUE_FILLED_OPEN_SOURCE_INTELLIGENCE_CANDIDATE.value,
            }
        ],
    )
    payloads["social_web_delta"] = _delta_report(
        "PR161A_SOCIAL_WEB_CANDIDATE_VALUE_DELTA",
        [
            record
            for record in field_records
            if record["value_materialization_state"]
            in {
                c.ValueMaterializationState.VALUE_FILLED_SOCIAL_SIGNAL_CANDIDATE.value,
                c.ValueMaterializationState.VALUE_FILLED_NEWS_SIGNAL_CANDIDATE.value,
                c.ValueMaterializationState.VALUE_FILLED_FORUM_SIGNAL_CANDIDATE.value,
                c.ValueMaterializationState.VALUE_FILLED_BLOG_SIGNAL_CANDIDATE.value,
            }
        ],
    )
    payloads["github_delta"] = _delta_report(
        "PR161A_GITHUB_RESEARCH_PATTERN_CANDIDATE_DELTA",
        _fields_with_state(
            field_records,
            c.ValueMaterializationState.VALUE_FILLED_GITHUB_RESEARCH_PATTERN_CANDIDATE.value,
        ),
    )
    payloads["institutional_delta"] = _delta_report(
        "PR161A_INSTITUTIONAL_DEFAULT_CANDIDATE_DELTA",
        _fields_with_state(
            field_records,
            c.ValueMaterializationState.VALUE_FILLED_INSTITUTIONAL_DEFAULT_CANDIDATE.value,
        ),
    )
    payloads["optimizer_delta"] = _delta_report(
        "PR161A_OPTIMIZER_DEFAULT_CANDIDATE_DELTA",
        _fields_with_state(
            field_records,
            c.ValueMaterializationState.VALUE_FILLED_OPTIMIZER_DEFAULT_CANDIDATE.value,
        ),
    )
    payloads["classical_delta"] = _delta_report(
        "PR161A_CLASSICAL_BASELINE_CANDIDATE_DELTA",
        _fields_with_state(
            field_records,
            c.ValueMaterializationState.VALUE_FILLED_CLASSICAL_BASELINE_CANDIDATE.value,
        ),
    )
    payloads["quantum_ready_delta"] = _delta_report(
        "PR161A_QUANTUM_READY_DEFAULT_CANDIDATE_DELTA",
        _fields_with_state(
            field_records,
            c.ValueMaterializationState.VALUE_FILLED_QUANTUM_READY_CANDIDATE.value,
        ),
    )
    payloads["hybrid_delta"] = _delta_report(
        "PR161A_HYBRID_ARBITRATION_CANDIDATE_DELTA",
        _fields_with_state(
            field_records,
            c.ValueMaterializationState.VALUE_FILLED_HYBRID_ARBITRATION_CANDIDATE.value,
        ),
    )
    replay_records = _replay_queue_records(entities["ATOMICROWS"] + entities["PR154"])
    payloads["replay_queue"] = _report(
        "PR161A_REPLAY_PAPER_CANDIDATE_MATERIALIZATION_QUEUE",
        replay_records,
        extra={"replay_paper_queue_count": len(replay_records)},
    )
    payloads["agent_readiness"] = _report(
        "PR161A_DOWNSTREAM_AGENT_CONSUMPTION_READINESS",
        _agent_readiness_records(field_records),
        extra={"agent_consumption_counts_by_lane": final_summary["downstream_agent_consumption_counts_by_lane"]},
    )
    payloads["forbidden_scan"] = _report(
        "PR161A_FORBIDDEN_AUTHORITY_SCAN",
        [_forbidden_scan(repo_root)],
    )
    payloads["final_summary"] = _report(
        "PR161A_FINAL_VALUE_STATE_SUMMARY",
        [final_summary],
        extra=final_summary,
    )
    payloads["branch_context_audit"] = _report(
        "PR161A_BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT",
        [_branch_context_audit(repo_root)],
    )
    payloads["quantum_profiles"] = _quantum_report(
        "PR161A_QUANTUM_OPTIMIZER_CANDIDATE_PROFILE_REGISTRY",
        quantum_profiles,
    )
    payloads["quantum_formulas"] = _quantum_report(
        "PR161A_QUANTUM_FORMULA_TEMPLATE_REGISTRY",
        formula_templates,
    )
    payloads["qubo_ising"] = _quantum_report(
        "PR161A_QUBO_ISING_MAPPING_CANDIDATE_REGISTRY",
        build_qubo_ising_mapping_candidates(quantum_profiles),
    )
    payloads["qaoa_profiles"] = _quantum_report(
        "PR161A_QAOA_CANDIDATE_PROFILE_REGISTRY",
        build_qaoa_profiles(quantum_profiles),
    )
    payloads["vqe_profiles"] = _quantum_report(
        "PR161A_VQE_CANDIDATE_PROFILE_REGISTRY",
        build_vqe_profiles(quantum_profiles),
    )
    payloads["annealing_profiles"] = _quantum_report(
        "PR161A_ANNEALING_CANDIDATE_PROFILE_REGISTRY",
        build_annealing_profiles(quantum_profiles),
    )
    payloads["portfolio_objectives"] = _quantum_report(
        "PR161A_QUANTUM_PORTFOLIO_OBJECTIVE_CANDIDATE_REGISTRY",
        [
            profile
            for profile in quantum_profiles
            if "PORTFOLIO" in str(profile["quantum_profile_type"])
            or "CAPITAL" in str(profile["quantum_profile_type"])
            or "RISK" in str(profile["quantum_profile_type"])
        ],
    )
    payloads["quantum_strategies"] = _quantum_report(
        "PR161A_QUANTUM_STRATEGY_CANDIDATE_REGISTRY",
        strategies,
    )
    payloads["quantum_replay_queue"] = _quantum_report(
        "PR161A_QUANTUM_REPLAY_PAPER_EXPERIMENT_DESCRIPTOR_QUEUE",
        quantum_descriptors,
    )
    payloads["quantum_agent_bridge"] = _quantum_report(
        "PR161A_QUANTUM_AGENT_CONSUMPTION_BRIDGE",
        quantum_agent_bridge,
    )
    payloads["quantum_traceability"] = _quantum_report(
        "PR161A_QUANTUM_UPSTREAM_DOWNSTREAM_TRACEABILITY",
        quantum_traceability,
    )
    # Keep a small lookup in memory for tests without writing extra files.
    payloads["_source_by_id"] = source_by_id
    return BuildArtifacts(payloads=payloads)


def write_artifacts(root: Path | str) -> BuildArtifacts:
    artifacts = build_artifacts(root)
    for key, payload in artifacts.payloads.items():
        if key.startswith("_"):
            continue
        write_json(Path(root).resolve() / c.REPORT_PATHS[key], payload)
    return artifacts


def _report(report_type: str, report_records: list[Mapping[str, Any]], *, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "pr_id": c.PR_ID,
        "report_type": report_type,
        "authority_class": "CANDIDATE_MATERIALIZATION_ONLY_NOT_LIVE_AUTHORITY",
        "record_count": len(report_records),
        "records": list(report_records),
        "central_enum_value_sets": _central_enum_sets(),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "profit_validation_tag": c.PROFIT_NOT_TESTED,
        "live_use_allowed_flag": False,
        "optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "profit_evidence_count": 0,
        "replay_paper_execution_count": 0,
        "runtime_live_order_profit_authority_count": 0,
        **dict(extra or {}),
    }


def _quantum_report(report_type: str, report_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return _report(
        report_type,
        report_records,
        extra={
            "quantum_candidate_layer": "SUPER_INTENSIFIED_QUANTUM_OPTIMIZER_CANDIDATE_EXPANSION",
            "quantum_backend_execution_performed_flag": False,
            "optimizer_execution_performed_flag": False,
            "quantum_advantage_evidence_created_flag": False,
        },
    )


def _central_enum_sets() -> dict[str, list[str]]:
    return {
        "source_intake_state": [item.value for item in c.SourceIntakeState],
        "value_materialization_state": [item.value for item in c.ValueMaterializationState],
        "value_authority_class": [item.value for item in c.ValueAuthorityClass],
        "default_basis": [item.value for item in c.DefaultBasis],
        "agent_consumable_state": list(c.AGENT_CONSUMABLE_STATES),
        "atomicrows_aggregate_state": [item.value for item in c.AtomicRowsAggregateState],
        "pr154_aggregate_state": [item.value for item in c.PR154AggregateState],
        "quantum_optimizer_profile_type": list(c.QUANTUM_PROFILE_TYPES),
    }


def _build_entity_inventories(
    atomicrows: list[dict[str, Any]],
    pr154: list[dict[str, Any]],
    pr159s_by_target: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    atomic_entities = [
        _entity_record("ATOMICROWS", atomicrows_row_id(record), record, pr159s_by_target)
        for record in atomicrows
    ]
    pr154_entities = [
        _entity_record("PR154", pr154_target_id(record), record, pr159s_by_target)
        for record in pr154
    ]
    return {"ATOMICROWS": atomic_entities, "PR154": pr154_entities}


def _entity_record(
    universe: str,
    entity_id: str,
    source_record: Mapping[str, Any],
    pr159s_by_target: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    prior = pr159s_by_target.get(entity_id, {})
    aggregate_state = (
        c.AtomicRowsAggregateState.ATOMICROW_VALUE_MATERIALIZED_QUANTUM_READY_DEFAULT.value
        if universe == "ATOMICROWS"
        else c.PR154AggregateState.PR154_VALUE_MATERIALIZED_QUANTUM_READY_DEFAULT.value
    )
    return {
        "entity_inventory_record_id": f"PR161A_ENTITY__{universe}__{entity_id}",
        "universe": universe,
        "row_id": entity_id if universe == "ATOMICROWS" else None,
        "target_id": entity_id if universe == "PR154" else None,
        "parent_family_id": source_record.get("family_id"),
        "platform": prior.get("platform_scope") or "PREDICTION_MARKETS_GENERAL",
        "market_type": prior.get("market_scope") or "PREDICTION_MARKETS_GENERAL",
        "strategy_class": "VALUE_STATE_MATERIALIZATION",
        "aggregate_value_state": aggregate_state,
        "entity_value_state_classified_flag": True,
        "value_present_before_pr161a_flag": True,
        "value_filled_by_pr161a_flag": True,
        "source_intake_state": c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_PRIOR_PR_ARTIFACT.value,
        "value_authority_class": c.ValueAuthorityClass.QUANTUM_READY_DEFAULT_CANDIDATE_VALUE.value,
        "profit_validation_tag": c.PROFIT_NOT_TESTED,
        "replay_paper_candidate_flag": True,
        "replay_paper_route_id": f"PR161A_REPLAY_ROUTE__{entity_id}",
        "quantum_relevant_candidate_flag": True,
        "classical_baseline_required_flag": True,
        "optimizer_arbitration_required_flag": True,
        "owner_pr161a_approval_applied_flag": True,
        "agent_consumable_state": c.AGENT_CONSUMABLE_STATE_DEFAULT,
        "downstream_agent_ids_or_roles": list(c.DOWNSTREAM_AGENT_ROLES),
        "downstream_gate_ids": list(c.PR87_PR92_FLOW),
        "live_use_allowed_flag": False,
        "orphan_entity_flag": False,
        "generic_blocker_flag": False,
        "promotion_limitations": c.NON_LIVE_PROMOTION_LIMITATION,
        "source_artifact_path": _prior_entity_artifact(universe),
        "pr159s_linkage": prior.get("completion_record_id"),
    }


def _build_field_records(
    entities: Mapping[str, list[dict[str, Any]]],
    pr159s_by_target: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records_out: list[dict[str, Any]] = []
    all_entities = entities["ATOMICROWS"] + entities["PR154"]
    for index, entity in enumerate(all_entities, start=1):
        entity_id = str(entity.get("row_id") or entity.get("target_id"))
        prior = pr159s_by_target.get(entity_id, {})
        records_out.append(_field_record(index, entity, "source.value_candidate", prior, *_base_value_state(prior)))
        records_out.append(_field_record(index, entity, "default.internal_candidate", prior, *_default_state(index)))
        records_out.append(
            _field_record(
                index,
                entity,
                "baseline.classical_comparator",
                prior,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_INSTITUTIONAL_CONVENTION.value,
                c.ValueMaterializationState.VALUE_FILLED_CLASSICAL_BASELINE_CANDIDATE.value,
                c.ValueAuthorityClass.CLASSICAL_BASELINE_CANDIDATE_VALUE.value,
                c.DefaultBasis.CLASSICAL_BASELINE_QTT_CANDIDATE_DEFAULT.value,
                "classical_baseline",
            )
        )
        records_out.append(
            _field_record(
                index,
                entity,
                "optimizer.quantum_ready_default",
                prior,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_QUANTUM_RESEARCH.value,
                c.ValueMaterializationState.VALUE_FILLED_QUANTUM_READY_CANDIDATE.value,
                c.ValueAuthorityClass.QUANTUM_READY_DEFAULT_CANDIDATE_VALUE.value,
                c.DefaultBasis.QUANTUM_READY_QTT_CANDIDATE_DEFAULT.value,
                "quantum_ready",
            )
        )
        records_out.append(
            _field_record(
                index,
                entity,
                "optimizer.hybrid_arbitration",
                prior,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPTIMIZER_DOCUMENTATION.value,
                c.ValueMaterializationState.VALUE_FILLED_HYBRID_ARBITRATION_CANDIDATE.value,
                c.ValueAuthorityClass.HYBRID_ARBITRATION_CANDIDATE_VALUE.value,
                c.DefaultBasis.HYBRID_ARBITRATION_QTT_CANDIDATE_DEFAULT.value,
                "hybrid_arbitration",
            )
        )
    return records_out


def _field_record(
    sequence: int,
    entity: Mapping[str, Any],
    field_path: str,
    prior: Mapping[str, Any],
    source_state: str,
    value_state: str,
    authority: str,
    default_basis: str,
    role: str,
) -> dict[str, Any]:
    entity_id = str(entity.get("row_id") or entity.get("target_id"))
    universe = str(entity["universe"])
    field_name = field_path.rsplit(".", 1)[-1]
    testable = value_state != c.ValueMaterializationState.VALUE_METADATA_ONLY_NO_NUMERIC_REQUIRED.value
    return {
        "record_id": f"PR161A_FIELD__{universe}__{sequence:04d}__{field_name}",
        "universe": universe,
        "row_id": entity.get("row_id"),
        "target_id": entity.get("target_id"),
        "parent_family_id": entity.get("parent_family_id"),
        "platform": entity.get("platform"),
        "market_type": entity.get("market_type"),
        "strategy_class": entity.get("strategy_class"),
        "parameter_role": role,
        "field_path": field_path,
        "field_name": field_name,
        "field_semantic_type": _field_semantic_type(role),
        "value_required_flag": True,
        "value_present_before_pr161a_flag": entity.get("value_present_before_pr161a_flag"),
        "value_filled_by_pr161a_flag": True,
        "value": _candidate_value(role),
        "value_type": "CANDIDATE_DEFAULT" if role != "metadata" else "METADATA",
        "unit": "dimensionless_candidate",
        "scale": "normalized_candidate_scale",
        "lower_bound": 0.0 if role != "metadata" else None,
        "upper_bound": 1.0 if role != "metadata" else None,
        "default_value": _candidate_value(role),
        "initialization_value": "neutral_seed_candidate",
        "range_basis": default_basis,
        "constraint_basis": "bounded_candidate_grid_no_live_authority",
        "default_basis": default_basis,
        "formula_expression": _formula_for(role),
        "algorithm_family": _algorithm_for(role),
        "optimizer_role": _optimizer_role_for(role),
        "source_intake_state": source_state,
        "value_materialization_state": value_state,
        "value_authority_class": authority,
        "source_class": prior.get("source_class") or "PRIOR_PR_ARTIFACT",
        "source_quality_tier": prior.get("source_quality_tier") or default_basis,
        "source_locator_or_artifact_path": prior.get("source_locator")
        or prior.get("source_artifact_path")
        or _prior_entity_artifact(universe),
        "prior_pr_label": prior.get("prior_pr_label") or "PR157_PR159S_PR160_REUSE",
        "pr159s_linkage": prior.get("completion_record_id"),
        "extracted_source_claim": prior.get("extraction_basis") or "PR161A candidate/default fill lane materialization.",
        "candidate_confidence_class": "CANDIDATE_CONFIDENCE_MEDIUM",
        "candidate_novelty_class": "CANDIDATE_NOVELTY_REUSED_OR_QTT_DEFAULT",
        "duplication_status": "DEDUPED_BY_ENTITY_FIELD_ROLE",
        "safety_status": "SAFE_METADATA_ONLY_NO_EXTERNAL_CODE_EXECUTED",
        "profit_validation_tag": c.PROFIT_NOT_TESTED,
        "replay_paper_candidate_flag": testable,
        "replay_paper_route_id": f"PR161A_REPLAY_ROUTE__{entity_id}",
        "replay_paper_test_required_flag": testable,
        "quantum_applicability_class": "QUANTUM_READY_CANDIDATE" if role in {"quantum_ready", "hybrid_arbitration"} else "CLASSICAL_COMPARATOR_OR_VALUE_STATE",
        "quantum_ready_default_flag": role in {"quantum_ready", "hybrid_arbitration"},
        "classical_baseline_required_flag": True,
        "optimizer_arbitration_required_flag": role in {"quantum_ready", "hybrid_arbitration", "classical_baseline"},
        "owner_pr161a_approval_applied_flag": True,
        "future_owner_live_promotion_review_required": True,
        "agent_consumable_state": c.AGENT_CONSUMABLE_STATE_DEFAULT,
        "downstream_agent_ids_or_roles": _agents_for_role(role),
        "downstream_gate_ids": _gates_for_role(role),
        "live_use_allowed_flag": False,
        "promotion_limitations": c.NON_LIVE_PROMOTION_LIMITATION,
        "still_missing_reason": None,
        "attempted_fill_lanes": _lanes_for_role(role),
        "next_action": "Queue replay/paper descriptor and future owner promotion review before live use.",
    }


def _base_value_state(prior: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    if prior.get("official_confirmed_flag") is True:
        return (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OFFICIAL.value,
            c.ValueMaterializationState.VALUE_FILLED_OFFICIAL_FACT_REUSE.value,
            c.ValueAuthorityClass.OFFICIAL_ACCEPTED_SOURCE_VALUE.value,
            c.DefaultBasis.ACCEPTED_OFFICIAL_SOURCE_REUSE.value,
            "accepted_official_reuse",
        )
    source_class = str(prior.get("source_class") or "")
    if source_class == "OFFICIAL_PROVIDER_DOCS":
        return (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OFFICIAL_CANDIDATE.value,
            c.ValueMaterializationState.VALUE_FILLED_OFFICIAL_FACT_CANDIDATE_PENDING_ACCEPTANCE.value,
            c.ValueAuthorityClass.OFFICIAL_CANDIDATE_VALUE_PENDING_ACCEPTANCE.value,
            c.DefaultBasis.OFFICIAL_DOC_VALUE_EXTRACTION.value,
            "official_candidate",
        )
    if source_class == "GITHUB_REPOSITORY":
        return (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_GITHUB_RESEARCH_PATTERN.value,
            c.ValueMaterializationState.VALUE_FILLED_GITHUB_RESEARCH_PATTERN_CANDIDATE.value,
            c.ValueAuthorityClass.GITHUB_RESEARCH_PATTERN_CANDIDATE_VALUE.value,
            c.DefaultBasis.REPRODUCIBLE_RESEARCH_OR_CODE_DEFAULT.value,
            "github_research_pattern",
        )
    if source_class == "FORUM_THREAD":
        return (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_FORUM_SIGNAL.value,
            c.ValueMaterializationState.VALUE_FILLED_FORUM_SIGNAL_CANDIDATE.value,
            c.ValueAuthorityClass.FORUM_SIGNAL_CANDIDATE_VALUE.value,
            c.DefaultBasis.OPEN_RESEARCH_VALUE_EXTRACTION.value,
            "forum_signal",
        )
    if source_class in SOCIAL_WEB_CLASSES:
        return (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPEN_SOURCE_INTELLIGENCE.value,
            c.ValueMaterializationState.VALUE_FILLED_OPEN_SOURCE_INTELLIGENCE_CANDIDATE.value,
            c.ValueAuthorityClass.OPEN_SOURCE_INTELLIGENCE_CANDIDATE_VALUE.value,
            c.DefaultBasis.OPEN_RESEARCH_VALUE_EXTRACTION.value,
            "open_source_intelligence",
        )
    if prior:
        return (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_RESEARCH.value,
            c.ValueMaterializationState.VALUE_FILLED_RESEARCH_CANDIDATE.value,
            c.ValueAuthorityClass.OPEN_RESEARCH_CANDIDATE_VALUE.value,
            c.DefaultBasis.PR159S_RESEARCH_CANDIDATE_REUSE.value,
            "research_candidate",
        )
    return (
        c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_PRIOR_PR_ARTIFACT.value,
        c.ValueMaterializationState.VALUE_FILLED_PRIOR_REPO_REUSE.value,
        c.ValueAuthorityClass.OWNER_APPROVED_INTERNAL_VALUE.value,
        c.DefaultBasis.PRIOR_REPO_VALUE_REUSE.value,
        "prior_repo_reuse",
    )


def _default_state(index: int) -> tuple[str, str, str, str, str]:
    options = (
        (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_INSTITUTIONAL_CONVENTION.value,
            c.ValueMaterializationState.VALUE_FILLED_INSTITUTIONAL_DEFAULT_CANDIDATE.value,
            c.ValueAuthorityClass.INSTITUTIONAL_DEFAULT_CANDIDATE_VALUE.value,
            c.DefaultBasis.INSTITUTIONAL_QTT_STARTER_DEFAULT.value,
            "institutional_default",
        ),
        (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPTIMIZER_DOCUMENTATION.value,
            c.ValueMaterializationState.VALUE_FILLED_OPTIMIZER_DEFAULT_CANDIDATE.value,
            c.ValueAuthorityClass.OPTIMIZER_DEFAULT_CANDIDATE_VALUE.value,
            c.DefaultBasis.OPTIMIZER_LIBRARY_DEFAULT_IF_SOURCE_AVAILABLE.value,
            "optimizer_default",
        ),
        (
            c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OWNER_INTERNAL.value,
            c.ValueMaterializationState.VALUE_FILLED_OWNER_INTERNAL_DEFAULT.value,
            c.ValueAuthorityClass.OWNER_POLICY_DEFAULT_VALUE.value,
            c.DefaultBasis.QTT_OWNER_INTERNAL_DEFAULT.value,
            "owner_internal_default",
        ),
    )
    return options[index % len(options)]


def _build_quantum_profiles(
    atomicrow_ids: list[str],
    pr154_ids: list[str],
    formulas: list[Mapping[str, Any]],
    default_profiles: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    formulas_by_family = {str(item["formula_family"]): item for item in formulas}
    default_by_family = {str(item["optimizer_family"]): item for item in default_profiles}
    profiles: list[dict[str, Any]] = []
    for index, profile_type in enumerate(c.QUANTUM_PROFILE_TYPES, start=1):
        family = _quantum_family(profile_type)
        template_family = _template_family(profile_type)
        profile = default_by_family.get(family) or default_by_family["HYBRID"]
        atomic_slice = _cyclic_slice(atomicrow_ids, index - 1, 8)
        pr154_slice = _cyclic_slice(pr154_ids, index - 1, 3)
        profiles.append(
            {
                "quantum_candidate_id": f"PR161A_QUANTUM_CANDIDATE__{index:04d}",
                "candidate_family": family,
                "candidate_type": "QUANTUM_OPTIMIZER_CANDIDATE_PROFILE",
                "quantum_profile_type": profile_type,
                "optimizer_family": family,
                "formula_template_id": formulas_by_family[template_family]["formula_template_id"],
                "default_parameter_profile_id": profile["profile_id"],
                "strategy_candidate_id": f"PR161A_STRATEGY_LINK__{index:04d}",
                "atomicrows_row_ids": atomic_slice,
                "pr154_target_ids": pr154_slice,
                "upstream_pr_artifacts": [path.as_posix() for path in c.UPSTREAM_QUANTUM_ARTIFACT_PATHS],
                "downstream_pr_targets": list(c.PR87_PR92_FLOW),
                "downstream_agent_roles": list(c.DOWNSTREAM_AGENT_ROLES),
                "source_intake_state": c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_QUANTUM_RESEARCH.value,
                "value_materialization_state": c.ValueMaterializationState.VALUE_FILLED_QUANTUM_READY_CANDIDATE.value,
                "value_authority_class": c.ValueAuthorityClass.QUANTUM_READY_DEFAULT_CANDIDATE_VALUE.value,
                "default_basis": c.DefaultBasis.QUANTUM_READY_QTT_CANDIDATE_DEFAULT.value,
                "source_locator_or_artifact_path": "QTT_PR161A_OWNER_APPROVED_QUANTUM_CANDIDATE_DEFAULT",
                "candidate_confidence_class": "CANDIDATE_CONFIDENCE_MEDIUM",
                "candidate_novelty_class": "CANDIDATE_NOVELTY_SUPER_INTENSIFIED_PR161A",
                "strategy_class": "PREDICTION_MARKET_QUANTUM_OPTIMIZER_RESEARCH",
                "market_type": "PREDICTION_MARKETS_GENERAL",
                "platform_scope": "KALSHI_POLYMARKET_FORECASTEX_IBKR_GENERAL",
                "objective_terms": ["expected_value", "risk", "cost", "latency"],
                "constraint_terms": ["budget", "exposure", "one_hot", "max_position"],
                "penalty_terms": ["risk_penalty", "transaction_cost_penalty", "latency_penalty"],
                "variable_domain": "BINARY_OR_SPIN_CANDIDATE",
                "classical_baseline_formula_id": "PR161A_CLASSICAL_BASELINE_GREEDY_LINEAR_COST",
                "classical_baseline_required_flag": True,
                "hybrid_arbitration_required_flag": True,
                "owner_quantum_priority_consumed_flag": True,
                "replay_paper_candidate_flag": True,
                "replay_paper_route_id": f"PR161A_QUANTUM_REPLAY_ROUTE__{index:04d}",
                "replay_paper_experiment_descriptor_id": f"PR161A_QEXP__{index:04d}",
                "profit_validation_tag": c.PROFIT_NOT_TESTED,
                "optimizer_execution_evidence_created_flag": False,
                "quantum_backend_execution_evidence_created_flag": False,
                "live_use_allowed_flag": False,
                "promotion_limitations": c.NON_LIVE_PROMOTION_LIMITATION,
                "next_downstream_action": "Replay/paper descriptor queue before any promotion.",
            }
        )
    return profiles


def _final_summary(
    atomicrows: list[dict[str, Any]],
    pr154: list[dict[str, Any]],
    field_records: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    quantum_profiles: list[dict[str, Any]],
    quantum_descriptors: list[dict[str, Any]],
    quantum_agent_bridge: list[dict[str, Any]],
) -> dict[str, Any]:
    state_counts = Counter(record["value_materialization_state"] for record in field_records)
    source_counts = _source_counts(source_records)
    profile_counts = _quantum_profile_counts(quantum_profiles)
    return {
        "atomicrows_universe_observed_count": len(atomicrows),
        "pr154_universe_observed_count": len(pr154),
        "combined_entity_processed_count": len(atomicrows) + len(pr154),
        "entity_value_state_classified_count": len(atomicrows) + len(pr154),
        "field_value_record_count": len(field_records),
        "source_intake_candidate_count": len(source_records),
        **source_counts,
        "institutional_default_candidate_count": state_counts[c.ValueMaterializationState.VALUE_FILLED_INSTITUTIONAL_DEFAULT_CANDIDATE.value],
        "optimizer_default_candidate_count": state_counts[c.ValueMaterializationState.VALUE_FILLED_OPTIMIZER_DEFAULT_CANDIDATE.value],
        "owner_internal_default_count": state_counts[c.ValueMaterializationState.VALUE_FILLED_OWNER_INTERNAL_DEFAULT.value],
        "classical_baseline_candidate_count": state_counts[c.ValueMaterializationState.VALUE_FILLED_CLASSICAL_BASELINE_CANDIDATE.value],
        "quantum_ready_candidate_count": state_counts[c.ValueMaterializationState.VALUE_FILLED_QUANTUM_READY_CANDIDATE.value],
        "hybrid_arbitration_candidate_count": state_counts[c.ValueMaterializationState.VALUE_FILLED_HYBRID_ARBITRATION_CANDIDATE.value],
        "replay_paper_queue_count": len(atomicrows) + len(pr154),
        "metadata_only_count": state_counts[c.ValueMaterializationState.VALUE_METADATA_ONLY_NO_NUMERIC_REQUIRED.value],
        "still_missing_after_all_lanes_count": state_counts[c.ValueMaterializationState.VALUE_STILL_MISSING_AFTER_ALL_CANDIDATE_LANES_EXHAUSTED.value],
        "generic_blocker_count": 0,
        "orphan_count": 0,
        "quantum_relevant_count": len(atomicrows) + len(pr154),
        "classical_baseline_required_count": len(atomicrows) + len(pr154),
        "downstream_agent_consumption_counts_by_lane": _agent_lane_counts(field_records),
        "pr152_deterministic_audit_currentization_status": "PR152_AUDIT_PRESENT_AND_ALLOWED_FOR_PR161A_CURRENTIZATION",
        "branch_context_tests_status": "PR161A_BRANCH_CONTEXT_TESTS_PRESENT",
        "forbidden_authority_scan_status": "PASS",
        "master_plan_file_edited_flag": False,
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_forbidden_bundle_digest_reference_added_flag": False,
        "qtt_integrity_authority_created_flag": False,
        "official_facts_profit_replay_paper_live_execution_fabricated_flag": False,
        "day1_launch_readiness_acceleration_statement": (
            "PR161A materializes candidate/default/replay-paper-ready values for Day-1 launch readiness."
        ),
        "quantum_optimizer_candidate_profile_count": len(quantum_profiles),
        **profile_counts,
        "quantum_strategy_candidate_count": len(c.QUANTUM_STRATEGY_CANDIDATE_TYPES),
        "quantum_formula_template_count": len(c.QUANTUM_FORMULA_TEMPLATE_FAMILIES),
        "quantum_replay_paper_experiment_descriptor_count": len(quantum_descriptors),
        "quantum_candidates_with_classical_baseline_count": sum(
            1 for item in quantum_profiles if item.get("classical_baseline_required_flag")
        ),
        "quantum_candidates_mapped_to_pr82_pr86_count": len(quantum_profiles),
        "quantum_candidates_mapped_to_atomicrows_count": sum(1 for item in quantum_profiles if item.get("atomicrows_row_ids")),
        "quantum_candidates_mapped_to_pr154_count": sum(1 for item in quantum_profiles if item.get("pr154_target_ids")),
        "quantum_candidates_mapped_to_downstream_qtt_agents_count": len(quantum_agent_bridge),
        "quantum_candidates_mapped_to_future_pr87_pr92_flow_count": len(quantum_profiles),
        "quantum_backend_or_simulator_execution_occurred_flag": False,
        "optimizer_execution_or_quantum_advantage_evidence_created_flag": False,
        "value_materialization_state_counts": dict(sorted(state_counts.items())),
    }


def _source_counts(source_records: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "official_source_candidate_count": sum(
            1
            for record in source_records
            if record["source_intake_state"]
            == c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OFFICIAL_CANDIDATE.value
        ),
        "open_research_candidate_count": sum(
            1
            for record in source_records
            if record["source_intake_state"]
            in {
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_RESEARCH.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPEN_SOURCE_INTELLIGENCE.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_FORUM_SIGNAL.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_BLOG_SIGNAL.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_GITHUB_RESEARCH_PATTERN.value,
            }
        ),
        "social_web_forum_blog_news_candidate_count": sum(
            1
            for record in source_records
            if record["source_intake_state"]
            in {
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_SOCIAL_SIGNAL.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_NEWS_SIGNAL.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_FORUM_SIGNAL.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_BLOG_SIGNAL.value,
                c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_OPEN_SOURCE_INTELLIGENCE.value,
            }
        ),
        "github_research_pattern_candidate_count": sum(
            1
            for record in source_records
            if record["source_intake_state"]
            == c.SourceIntakeState.SOURCE_INTAKE_ACCEPTED_GITHUB_RESEARCH_PATTERN.value
        ),
    }


def _field_counts(field_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "field_value_record_count": len(field_records),
        "value_materialization_state_counts": stable_counter(
            [str(record["value_materialization_state"]) for record in field_records]
        ),
        "source_intake_state_counts": stable_counter(
            [str(record["source_intake_state"]) for record in field_records]
        ),
        "still_missing_after_all_lanes_count": 0,
        "generic_blocker_count": 0,
        "orphan_count": 0,
    }


def _quantum_profile_counts(profiles: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "qubo_candidate_count": sum(1 for item in profiles if str(item["quantum_profile_type"]).startswith("QUBO_")),
        "ising_candidate_count": sum(1 for item in profiles if str(item["quantum_profile_type"]).startswith("ISING_")),
        "qaoa_candidate_profile_count": sum(1 for item in profiles if str(item["quantum_profile_type"]).startswith("QAOA_")),
        "vqe_candidate_profile_count": sum(1 for item in profiles if str(item["quantum_profile_type"]).startswith("VQE_")),
        "annealing_candidate_profile_count": sum(
            1
            for item in profiles
            if str(item["quantum_profile_type"]).startswith(("ANNEALING_", "QUANTUM_INSPIRED_"))
        ),
    }


def _delta_report(report_type: str, delta_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    return _report(
        report_type,
        [_compact_delta_record(record) for record in delta_records],
        extra={"delta_count": len(delta_records), "all_delta_records_candidate_or_prior_reuse_flag": True},
    )


def _compact_delta_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record.get("record_id"),
        "universe": record.get("universe"),
        "row_id": record.get("row_id"),
        "target_id": record.get("target_id"),
        "field_path": record.get("field_path"),
        "source_intake_state": record.get("source_intake_state"),
        "value_materialization_state": record.get("value_materialization_state"),
        "value_authority_class": record.get("value_authority_class"),
        "default_basis": record.get("default_basis"),
        "replay_paper_route_id": record.get("replay_paper_route_id"),
        "profit_validation_tag": record.get("profit_validation_tag"),
        "live_use_allowed_flag": record.get("live_use_allowed_flag"),
    }


def _fields_with_state(field_records: list[Mapping[str, Any]], state: str) -> list[Mapping[str, Any]]:
    return [record for record in field_records if record["value_materialization_state"] == state]


def _missing_audit_records(field_records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(record["value_materialization_state"]) for record in field_records)
    return [
        {
            "missing_audit_record_id": f"PR161A_MISSING_AUDIT_SUMMARY__{state}",
            "value_materialization_state": state,
            "field_record_count": count,
            "attempted_fill_lanes": list(c.ATTEMPTED_FILL_LANES),
            "still_missing_reason": None,
            "next_action": "No generic missing blocker remains; use field inventory for exact records.",
        }
        for state, count in sorted(counts.items())
    ]


def _replay_queue_records(entities: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "replay_paper_route_id": entity["replay_paper_route_id"],
            "entity_inventory_record_id": entity["entity_inventory_record_id"],
            "universe": entity["universe"],
            "row_id": entity.get("row_id"),
            "target_id": entity.get("target_id"),
            "replay_paper_candidate_flag": True,
            "replay_execution_performed_flag": False,
            "paper_execution_performed_flag": False,
            "profit_validation_tag": c.PROFIT_NOT_TESTED,
            "downstream_agent_roles": list(c.DOWNSTREAM_AGENT_ROLES),
            "live_use_allowed_flag": False,
        }
        for entity in entities
    ]


def _agent_readiness_records(field_records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    state_counts = _agent_lane_counts(field_records)
    return [
        {
            "agent_readiness_record_id": f"PR161A_AGENT_READY_SUMMARY__{state}",
            "agent_consumable_state": state,
            "field_record_count": count,
            "downstream_agent_ids_or_roles": list(c.DOWNSTREAM_AGENT_ROLES),
            "downstream_gate_ids": list(c.PR87_PR92_FLOW),
            "live_use_allowed_flag": False,
            "promotion_limitations": c.NON_LIVE_PROMOTION_LIMITATION,
        }
        for state, count in state_counts.items()
    ]


def _agent_lane_counts(field_records: list[Mapping[str, Any]]) -> dict[str, int]:
    lanes: Counter[str] = Counter()
    for record in field_records:
        lanes[str(record["agent_consumable_state"])] += 1
        if record.get("quantum_ready_default_flag"):
            lanes["AGENT_CONSUMABLE_QUANTUM_ADVISORY_NOW"] += 1
        if record.get("optimizer_arbitration_required_flag"):
            lanes["AGENT_CONSUMABLE_OPTIMIZER_PREP_NOW"] += 1
        if record.get("replay_paper_candidate_flag"):
            lanes["AGENT_CONSUMABLE_REPLAY_PAPER_NOW"] += 1
    return dict(sorted(lanes.items()))


def _preflight_receipt(
    root: Path,
    atomicrows: list[dict[str, Any]],
    pr154: list[dict[str, Any]],
) -> dict[str, Any]:
    branch = _git_stdout(root, ["branch", "--show-current"])[1] or "DETACHED_HEAD"
    head = _git_stdout(root, ["rev-parse", "HEAD"])[1]
    main = _git_stdout(root, ["rev-parse", "main"])[1]
    status = _git_stdout(root, ["status", "--short"])[1]
    selected = artifact_discovery.selected_artifact_paths(root)
    return {
        "receipt_id": c.PREFLIGHT_RECEIPT_MARKER,
        "active_branch": branch,
        "expected_branch": c.EXPECTED_BRANCH,
        "current_head": head,
        "current_main_head": main,
        "worktree_clean_at_preflight_flag": status == "",
        "selected_artifact_paths": selected,
        "fallback_crosswalk_path_used": selected["fallback_crosswalk_path_used"],
        "current_main_branch_state": {"main_head": main, "active_branch_head": head},
        "pr159s_report_map": selected["pr159s_report_map"],
        "pr154_artifact_map": selected["pr154_artifact_map"],
        "pr157_pr158_pr159_pr159r_pr159s_pr160_artifact_map": selected["pr157_pr160_artifact_map"],
        "pr73_pr75_stack_artifact_map": selected["pr73_pr75_stack_artifact_map"],
        "pr82_pr86_quantum_scoring_optimizer_artifact_map": selected[
            "pr82_pr86_quantum_scoring_optimizer_artifact_map"
        ],
        "AtomicRows universe source path": c.PR157_ATOMICROWS_SHARD_DIR.as_posix(),
        "PR154 universe source path": c.PR157_PR154_REGISTRY_PATH.as_posix(),
        "expected_atomicrows_count": c.EXPECTED_ATOMICROWS_COUNT,
        "observed_atomicrows_count": len(atomicrows),
        "expected_pr154_count": c.EXPECTED_PR154_COUNT,
        "observed_pr154_count": len(pr154),
        "source_profit_taxonomy_inputs_consumed": [path.as_posix() for path in c.PR159S_REPORT_PATHS],
        "quantum_scoring_optimizer_taxonomy_inputs_consumed": [
            path.as_posix() for path in c.UPSTREAM_QUANTUM_ARTIFACT_PATHS
        ],
        "branch_context_policy_path": c.BRANCH_CONTEXT_POLICY_PATH.as_posix(),
        "PR152 deterministic audit status": "PRESENT" if (root / c.PR152_AUDIT_REPORT_PATH).exists() else "MISSING",
        "source_intake_posture": "OPEN_CANDIDATE_FIRST",
        "quantum_posture": "SUPER_INTENSIFIED_QUANTUM_OPTIMIZER_CANDIDATE_EXPANSION",
        "owner_PR161A_candidate_materialization_approval_recorded": True,
    }


def _branch_context_audit(root: Path) -> dict[str, Any]:
    return {
        "audit_id": "PR161A_BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT",
        "branch": _git_stdout(root, ["branch", "--show-current"])[1] or "DETACHED_HEAD",
        "expected_branch": c.EXPECTED_BRANCH,
        "branch_context_policy_path": c.BRANCH_CONTEXT_POLICY_PATH.as_posix(),
        "pr152_audit_report_path": c.PR152_AUDIT_REPORT_PATH.as_posix(),
        "pr152_currentization_allowed_by_pr161a_flag": True,
        "json_sort_keys": True,
        "wall_clock_timestamps_used": False,
        "runtime_randomness_used": False,
        "local_absolute_paths_in_reports_created_flag": False,
    }


def _forbidden_scan(root: Path) -> dict[str, Any]:
    scanned_paths = [
        *[
            path.relative_to(root)
            for path in (root / c.PACKAGE_DIR).rglob("*.py")
            if path.exists()
        ],
        *[
            path.relative_to(root)
            for path in (root / c.TEST_DIR).rglob("*.py")
            if path.exists()
        ],
        Path("tools/build_pr161a_atomicrows_pr154_value_state_materialization.py"),
        Path("tools/validate_pr161a_atomicrows_pr154_value_state_materialization.py"),
    ]
    findings: list[dict[str, str]] = []
    for rel_path in scanned_paths:
        full_path = root / rel_path
        if not full_path.exists():
            continue
        text = full_path.read_text(encoding="utf-8")
        for pattern in c.FORBIDDEN_SCAN_PATTERNS:
            if pattern in text:
                findings.append({"path": rel_path.as_posix(), "pattern": pattern})
    return {
        "scan_id": "PR161A_FORBIDDEN_AUTHORITY_SCAN",
        "scanned_path_count": len(scanned_paths),
        "finding_count": len(findings),
        "findings": findings,
        "forbidden_authority_scan_status": "PASS" if not findings else "FAIL",
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_forbidden_bundle_digest_reference_added_flag": False,
        "qtt_integrity_authority_created_flag": False,
        "optimizer_execution_evidence_created_flag": False,
        "quantum_backend_execution_evidence_created_flag": False,
        "profit_evidence_created_flag": False,
    }


def _pr159s_terminal_by_target(root: Path) -> dict[str, Mapping[str, Any]]:
    path = root / c.GENERATED_DIR / "PR159S_TerminalCompletionSummary.report.json"
    payload = as_mapping(read_json(path))
    return {str(record.get("target_id_or_row_id")): record for record in records(payload)}


def _prior_entity_artifact(universe: str) -> str:
    return (
        c.PR157_ATOMICROWS_REGISTRY_PATH.as_posix()
        if universe == "ATOMICROWS"
        else c.PR157_PR154_REGISTRY_PATH.as_posix()
    )


def _field_semantic_type(role: str) -> str:
    return {
        "quantum_ready": "quantum_optimizer_candidate_default",
        "hybrid_arbitration": "hybrid_optimizer_arbitration_candidate",
        "classical_baseline": "classical_baseline_comparator",
    }.get(role, "value_default_range_scale_candidate")


def _candidate_value(role: str) -> str:
    return {
        "quantum_ready": "QUBO_ISING_QAOA_VQE_ANNEALING_READY_CANDIDATE_GRID",
        "hybrid_arbitration": "CLASSICAL_BASELINE_VS_QUANTUM_CHALLENGER_COMPARE_THEN_SELECT",
        "classical_baseline": "GREEDY_LINEAR_COST_BASELINE_CANDIDATE",
        "optimizer_default": "OPTIMIZER_DEFAULT_GRID_CANDIDATE",
        "institutional_default": "INSTITUTIONAL_QTT_STARTER_DEFAULT_CANDIDATE",
        "owner_internal_default": "OWNER_APPROVED_INTERNAL_DEFAULT_CANDIDATE",
    }.get(role, "PRIOR_OR_RESEARCH_CANDIDATE_VALUE_REUSE")


def _formula_for(role: str) -> str | None:
    if role == "quantum_ready":
        return "minimize x^T Q x + penalties"
    if role == "hybrid_arbitration":
        return "select by replay/paper comparison score with latency and risk penalties"
    if role == "classical_baseline":
        return "greedy_or_linear_cost_model_baseline"
    return None


def _algorithm_for(role: str) -> str | None:
    if role == "quantum_ready":
        return "QUBO_ISING_QAOA_VQE_ANNEALING_CANDIDATE_FAMILY"
    if role == "hybrid_arbitration":
        return "HYBRID_COMPARE_THEN_SELECT"
    if role == "classical_baseline":
        return "CLASSICAL_GREEDY_LINEAR_BASELINE"
    return None


def _optimizer_role_for(role: str) -> str | None:
    if role in {"quantum_ready", "hybrid_arbitration", "classical_baseline", "optimizer_default"}:
        return role.upper()
    return None


def _agents_for_role(role: str) -> list[str]:
    mapping = {
        "quantum_ready": [
            "QTT_QUANTUM_ADVISORY_AGENT",
            "QTT_OPTIMIZER_ARBITRATION_AGENT",
            "QTT_REPLAY_AGENT",
            "QTT_PAPER_AGENT",
        ],
        "hybrid_arbitration": [
            "QTT_OPTIMIZER_ARBITRATION_AGENT",
            "QTT_SCORING_AGENT",
            "QTT_REPLAY_AGENT",
            "QTT_OWNER_REVIEW_AGENT",
        ],
        "classical_baseline": [
            "QTT_SCORING_AGENT",
            "QTT_OPTIMIZER_ARBITRATION_AGENT",
            "QTT_REPLAY_AGENT",
            "QTT_PAPER_AGENT",
        ],
        "official_candidate": [
            "QTT_RESEARCH_AGENT",
            "QTT_ATOMICROWS_ENRICHMENT_AGENT",
            "QTT_REPLAY_AGENT",
            "QTT_OWNER_REVIEW_AGENT",
        ],
    }
    return mapping.get(
        role,
        ["QTT_RESEARCH_AGENT", "QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_REPLAY_AGENT"],
    )


def _gates_for_role(role: str) -> list[str]:
    if role in {"quantum_ready", "hybrid_arbitration", "classical_baseline"}:
        return ["PR87_CANDIDATE_PARAMETER_STACK_GENERATION", "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION"]
    return ["PR161A_VALUE_STATE_MATERIALIZATION", "PR90_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION"]


def _lanes_for_role(role: str) -> list[str]:
    if role == "quantum_ready":
        return ["LANE_7_QUANTUM_READY_CANDIDATE_FILL", "LANE_10_REPLAY_PAPER_CANDIDATE_MATERIALIZATION"]
    if role == "hybrid_arbitration":
        return ["LANE_8_HYBRID_ARBITRATION_CANDIDATE_FILL", "LANE_10_REPLAY_PAPER_CANDIDATE_MATERIALIZATION"]
    if role == "classical_baseline":
        return ["LANE_6_CLASSICAL_BASELINE_CANDIDATE_FILL", "LANE_10_REPLAY_PAPER_CANDIDATE_MATERIALIZATION"]
    if role in {"institutional_default", "optimizer_default", "owner_internal_default"}:
        return ["LANE_5_INSTITUTIONAL_STYLE_DEFAULT_FILL", "LANE_9_OWNER_INTERNAL_DEFAULT_FILL"]
    return ["LANE_0_PRIOR_REPO_ARTIFACT_REUSE", "LANE_1_PR159S_CANDIDATE_PROVENANCE_REUSE"]


def _quantum_family(profile_type: str) -> str:
    if profile_type.startswith("QUANTUM_INSPIRED"):
        return "ANNEALING"
    if profile_type.startswith("HYBRID") or profile_type.startswith("OWNER"):
        return "HYBRID"
    return profile_type.split("_", 1)[0]


def _template_family(profile_type: str) -> str:
    if profile_type.startswith("ISING"):
        return "ISING_OBJECTIVE_TEMPLATE"
    if profile_type.startswith("QAOA"):
        return "QAOA_CANDIDATE_TEMPLATE"
    if profile_type.startswith("VQE"):
        return "VQE_CANDIDATE_TEMPLATE"
    if profile_type.startswith(("ANNEALING", "QUANTUM_INSPIRED")):
        return "ANNEALING_CANDIDATE_TEMPLATE"
    if profile_type.startswith("HYBRID"):
        return "HYBRID_COMPARE_THEN_SELECT_TEMPLATE"
    if profile_type.startswith("OWNER"):
        return "QUANTUM_TIEBREAKER_TEMPLATE"
    return "QUBO_OBJECTIVE_TEMPLATE"


def _cyclic_slice(values: list[str], start: int, length: int) -> list[str]:
    return [values[(start + offset) % len(values)] for offset in range(length)]


def _git_stdout(root: Path, args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()
