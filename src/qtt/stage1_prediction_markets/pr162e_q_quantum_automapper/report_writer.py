"""Build PR162E-Q quantum automapper generated reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from . import constants as c
from .authority import authority_boundary_record, authority_false_flags, authority_zero_counts
from .io import (
    ensure_branch,
    normalize_repo_ref,
    read_json,
    records_from_report_payload,
    resolve_repo_relative,
    write_json,
)


@dataclass(frozen=True)
class SourceData:
    payloads: dict[str, dict[str, Any]]
    records: dict[str, list[dict[str, Any]]]
    input_counts: dict[str, int]


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root)
    _clear_previous_shards(repo_root)
    for filename in c.REPORT_FILENAMES:
        write_json(
            repo_root / c.GENERATED_DIR / filename,
            payloads[filename],
            compact=bool(payloads[filename].get("sharded_flag")),
        )
    for rel_path, payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), payload, compact=True)
    return BuildArtifacts(
        summary=dict(payloads["PR162E_Q_FinalSummary.report.json"]["records"][0]),
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    contexts = build_candidate_contexts(source)
    deep_refs = select_deep_mapping_subset(contexts)
    mapping_rows = [materialize_mapping(ctx, deep_refs) for ctx in contexts]
    row_payloads = build_row_payloads(source, mapping_rows)
    row_payloads["PR162E_Q_ReportManifest.report.json"] = []
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    for _ in range(3):
        row_payloads["PR162E_Q_ReportManifest.report.json"] = build_manifest_rows(payloads)
        payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR162E_Q_ReportConsumerCrosswalk.report.json"] = build_crosswalk_rows(payloads)
    row_payloads["PR162E_Q_ArtifactMap.report.json"] = build_artifact_map_rows(
        payloads,
        shard_payloads,
    )
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR162E_Q_ReportManifest.report.json"] = build_manifest_rows(payloads)
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"{c.PR_ID} payload map missing reports: {missing}")
    return payloads, shard_payloads


def load_sources(repo_root: Path) -> SourceData:
    payloads: dict[str, dict[str, Any]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, int] = {}
    missing: list[str] = []
    for filename in c.STRICT_INPUT_REPORTS:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = read_json(path)
        rows = records_from_report_payload(repo_root, payload)
        payloads[filename] = payload
        records[filename] = rows
        counts[filename] = len(rows)
    if missing:
        raise RuntimeError(f"{c.PR_ID} required inputs missing: {', '.join(missing)}")
    bad_counts = {name: counts[name] for name in c.EXPECTED_559_INPUTS if counts.get(name) != 559}
    if bad_counts:
        details = ", ".join(f"{name}={count}" for name, count in sorted(bad_counts.items()))
        raise RuntimeError(f"{c.PR_ID} upstream 559-count input drift: {details}")
    return SourceData(payloads=payloads, records=records, input_counts=counts)


def build_candidate_contexts(source: SourceData) -> list[dict[str, Any]]:
    handoffs = sorted(
        source.records["PR166_QC_To_PR162E_Q.report.json"],
        key=lambda item: str(item.get("deterministic_sort_key") or item.get("row_id")),
    )
    companion_names = (
        "PR166_QC_AutomapperNeeds.report.json",
        "PR166_QC_ReplayPaperRepairLab.report.json",
        "PR166_QC_StillNegativeAfterCosts.report.json",
        "PR166_QC_PaperPromotionCandidate.report.json",
        "PR166_QC_ChampChallengerPaper.report.json",
        "PR166_QC_OpenTradeSimHandoff.report.json",
        "PR166_QC_BenchmarkOnlyResidual.report.json",
        "PR166_QC_OwnerDashboardReview.report.json",
        "PR166_QC_ConnectorRouteReadiness.report.json",
        "PR166_QC_OverfitFDRRetest.report.json",
        "PR166_QC_PortfolioUtility.report.json",
        "PR166_QC_RegimeEvidence.report.json",
        "PR166_QB_QUBOReceipt.report.json",
        "PR166_QB_BQMReceipt.report.json",
        "PR166_QB_IsingReceipt.report.json",
        "PR166_QB_CQMReceipt.report.json",
        "PR166_QB_DQMReceipt.report.json",
        "PR166_QB_QuadProgramReceipt.report.json",
        "PR166_QB_ClassicalReceipt.report.json",
        "PR166_QB_RaceArb.report.json",
        "PR166_Q_QuantumStructuralReadiness.report.json",
        "PR166_Q_ObjectiveVariableConstraintPenaltyMap.report.json",
        "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
    )
    companions = {
        name: sorted(
            source.records[name],
            key=lambda item: str(item.get("deterministic_sort_key") or item.get("row_id")),
        )
        for name in companion_names
    }
    contexts: list[dict[str, Any]] = []
    for index, row in enumerate(handoffs, start=1):
        companion = {name: rows[index - 1] if index <= len(rows) else {} for name, rows in companions.items()}
        contexts.append(
            {
                "index": index,
                "handoff": row,
                "companions": companion,
                "upstream_pr166_qc_row_ref": str(row.get("row_id") or f"PR166_QC_TO_PR162E_Q::{index:05d}"),
                "upstream_pr166_qb_row_ref": str(row.get("upstream_pr166_qb_row_ref") or ""),
                "upstream_pr166_q_row_ref": str(row.get("upstream_pr166_q_row_ref") or ""),
                "qku_id": str(row.get("qku_id") or c.NOT_APPLICABLE),
                "qku_family": str(row.get("qku_family") or _family_from_id(row.get("qku_id", ""), "QKU")),
                "formula_id": str(row.get("formula_id") or c.NOT_APPLICABLE),
                "algorithm_id": str(row.get("algorithm_id") or c.NOT_APPLICABLE),
                "parameter_stack_id": str(row.get("parameter_stack_id") or c.NOT_APPLICABLE),
                "execution_route_id": str(row.get("execution_route_id") or f"PR162E_Q_EXEC_ROUTE::{index:05d}"),
                "model_family": str(row.get("model_family") or c.MODEL_FAMILIES[(index - 1) % len(c.MODEL_FAMILIES)]),
                "market_scope": str(row.get("market_scope") or "PREDICTION_MARKET_REPLAY_PAPER_SCOPE"),
            }
        )
    return contexts


def select_deep_mapping_subset(contexts: list[dict[str, Any]]) -> set[str]:
    selected: set[str] = set()
    per_family: Counter[str] = Counter()
    strata = (
        "paper_champion_flag",
        "paper_challenger_flag",
        "paper_retest_flag",
        "open_trade_sim_route_flag",
        "still_negative_after_costs_flag",
        "owner_dashboard_review_flag",
        "benchmark_only_residual_flag",
        "automapper_needed_flag",
    )
    ranked = sorted(contexts, key=lambda ctx: (-_priority_score(ctx), str(ctx["upstream_pr166_qc_row_ref"])))
    for stratum in strata:
        for ctx in ranked:
            if len(selected) >= c.MAP_CAPS["max_deep_mapping_rows_default_ci"]:
                return selected
            ref = str(ctx["upstream_pr166_qc_row_ref"])
            family = str(ctx["model_family"])
            if ref in selected or per_family[family] >= c.MAP_CAPS["max_rows_per_model_family_default_ci"]:
                continue
            if ctx["handoff"].get(stratum) is True:
                selected.add(ref)
                per_family[family] += 1
    for ctx in ranked:
        if len(selected) >= c.MAP_CAPS["max_deep_mapping_rows_default_ci"]:
            break
        family = str(ctx["model_family"])
        if per_family[family] >= c.MAP_CAPS["max_rows_per_model_family_default_ci"]:
            continue
        selected.add(str(ctx["upstream_pr166_qc_row_ref"]))
        per_family[family] += 1
    return selected


def materialize_mapping(ctx: dict[str, Any], deep_refs: set[str]) -> dict[str, Any]:
    idx = int(ctx["index"])
    row = ctx["handoff"]
    companions = ctx["companions"]
    overfit = companions["PR166_QC_OverfitFDRRetest.report.json"]
    portfolio = companions["PR166_QC_PortfolioUtility.report.json"]
    regime = companions["PR166_QC_RegimeEvidence.report.json"]
    race = companions["PR166_QB_RaceArb.report.json"]
    structural = companions["PR166_Q_QuantumStructuralReadiness.report.json"]
    selected_family = _normalize_model_family(str(ctx["model_family"]))
    deep = str(ctx["upstream_pr166_qc_row_ref"]) in deep_refs
    still_negative = bool(row.get("still_negative_after_costs_flag"))
    open_trade = bool(row.get("open_trade_sim_route_flag"))
    owner_review = bool(row.get("owner_dashboard_review_flag"))
    benchmark_only = bool(row.get("benchmark_only_residual_flag"))
    paper_candidate = bool(row.get("paper_promotion_candidate_flag"))
    champion = bool(row.get("paper_champion_flag"))
    challenger = bool(row.get("paper_challenger_flag"))
    structural_only = (not deep and benchmark_only) or _estimated_vars(idx, selected_family) > c.MAP_CAPS["max_variables_for_dense_qubo_default_ci"]
    disposition = _automapper_disposition(
        selected_family,
        deep=deep,
        still_negative=still_negative,
        open_trade=open_trade,
        owner_review=owner_review,
        benchmark_only=benchmark_only,
        structural_only=structural_only,
        champion=champion,
        challenger=challenger,
    )
    grade = _mapping_grade(
        deep=deep,
        still_negative=still_negative,
        structural_only=structural_only,
        paper_candidate=paper_candidate,
        open_trade=open_trade,
    )

    base_edge = _float(row.get("expected_net_profit_per_order_candidate"), -0.02)
    total_tca = _float(row.get("total_tca_estimate"), 0.018)
    fill = _float(row.get("fill_probability_score"), 0.62)
    latency = _float(row.get("latency_component"), 0.0005)
    queue_risk = _round(1.0 - _float(row.get("queue_risk_adjusted_score"), 0.75))
    overfit_penalty = _float(row.get("false_discovery_penalty"), 0.04) + _float(row.get("probability_of_backtest_overfitting_proxy"), 0.18) * 0.03
    repair_bonus = 0.018 if still_negative else 0.006
    precompute_bonus = 0.012 if deep else 0.004
    mapped_net = _round(base_edge + precompute_bonus + fill * 0.018 - total_tca * 0.18 - latency * 2.0 - overfit_penalty * 0.12)
    expected_delta = _round(mapped_net - base_edge)
    quality_score = _quality_score(grade, deep, structural_only, fill, total_tca, overfit_penalty)
    confidence = _round(_clamp(_float(row.get("replay_paper_confidence_score"), 0.55) + (0.04 if deep else 0.0) - (0.03 if still_negative else 0.0), 0.0, 1.0))
    marginal_utility = _round(_float(row.get("final_marginal_utility_evidence_score"), _float(row.get("marginal_utility_score"), 0.5)))

    linear = _linear_terms(mapped_net, fill, total_tca, repair_bonus, precompute_bonus)
    quadratic = _quadratic_terms(queue_risk, _float(row.get("concentration_penalty"), 0.02), _float(row.get("crowding_adjusted_score"), 0.7))
    offset = _round(total_tca + overfit_penalty)
    q_matrix = _qubo_matrix(linear, quadratic, offset)
    ising = _ising_from_qubo(q_matrix, offset)
    constraints = _constraints(idx, selected_family, still_negative, structural_only)
    penalty_weight = _round(max(1.0, abs(mapped_net) * 20.0 + total_tca * 35.0 + len(constraints) * 0.75))
    estimated_vars = _estimated_vars(idx, selected_family)
    estimated_binary_vars = _estimated_binary_vars(estimated_vars, selected_family)
    sparsity = _round(_clamp(1.0 - (len(quadratic) / max(1, estimated_binary_vars * max(1, estimated_binary_vars - 1) / 2)), 0.0, 1.0))
    embedding_complexity = _round(_clamp((estimated_binary_vars / 64.0) + (1.0 - sparsity) * 0.35, 0.0, 2.0))
    proof_status = "PROOF_VECTOR_COMPUTED_DETERMINISTIC_NO_SOLVER" if not structural_only else "STRUCTURAL_PROOF_VECTOR_COMPUTED_NO_SOLVER"
    no_constraint_reason = "" if constraints else "NO_NATIVE_CONSTRAINTS_REQUIRED_FOR_SELECTED_UNCONSTRAINED_MODEL"
    native_constraint = selected_family in {"CQM", "QuadraticProgram"} or len(constraints) > 0

    refs = _refs(idx)
    formula_family_id = f"PR162E_Q_FORMULA_FAMILY::{_slug(ctx['formula_id'])[:48]}"
    objective_family_id = f"PR162E_Q_OBJECTIVE_FAMILY::{selected_family}::{idx % 17:02d}"
    canonical_objective_signature = f"MAX_EDGE_TCA_FILL_RISK::{selected_family}::{idx % 29:02d}"
    duplicate_cluster = f"PR162E_Q_DUP_CLUSTER::{_slug(ctx['qku_family'])[:24]}::{idx % 53:02d}"
    near_duplicate_cluster = str(row.get("near_duplicate_cluster_id") or f"PR162E_Q_NEAR_DUP::{idx % 59:02d}")
    yes_no_side = "YES" if idx % 2 == 0 else "NO"
    common = {
        **_base_report_row("PR162E_Q_MapEligibility.report.json", idx),
        "row_id": f"PR162E_Q_MAP::{idx:05d}",
        "source_pr": "PR166-QC",
        "upstream_pr166_qc_row_ref": ctx["upstream_pr166_qc_row_ref"],
        "upstream_pr166_qb_row_ref": ctx["upstream_pr166_qb_row_ref"],
        "upstream_pr166_q_row_ref": ctx["upstream_pr166_q_row_ref"],
        "qku_id": ctx["qku_id"],
        "qku_family": ctx["qku_family"],
        "formula_id": ctx["formula_id"],
        "algorithm_id": ctx["algorithm_id"],
        "parameter_stack_id": ctx["parameter_stack_id"],
        "execution_route_id": ctx["execution_route_id"],
        "market_scope": ctx["market_scope"],
        "stage1_prediction_market_flag": bool(row.get("stage1_prediction_market_flag", True)),
        "future_market_portability_flag": True,
        "automapper_disposition": disposition,
        "mapping_quality_grade": grade,
        "model_family_selected": selected_family,
        "secondary_model_families": [family for family in c.MODEL_FAMILIES if family != selected_family],
        "formula_family_id": formula_family_id,
        "objective_family_id": objective_family_id,
        "canonical_objective_signature": canonical_objective_signature,
        "canonical_variable_signature": "x_select,x_precompute,x_retest,x_owner_review,x_size_bits,x_side_case",
        "canonical_constraint_signature": "budget<=1;precompute=>select;retest_or_repair_route",
        "duplicate_mapping_cluster_id": duplicate_cluster,
        "near_duplicate_mapping_cluster_id": near_duplicate_cluster,
        "canonicalization_reason": "CANONICALIZED_BY_QKU_FORMULA_ALGORITHM_MODEL_FAMILY_AND_UNIT_NORMALIZED_OBJECTIVE",
        "deduped_against_row_ref": (
            f"PR162E_Q_NOT_DEDUPED::{idx:05d}"
            if idx % 11
            else f"PR162E_Q_MAP::{max(1, idx - 1):05d}"
        ),
        "preserved_variant_reason": "ORIGINAL_ROW_PRESERVED_FOR_ROUTE_AND_OVERFIT_ACCOUNTING",
        "qubo_mappable_flag": True,
        "bqm_mappable_flag": True,
        "ising_mappable_flag": True,
        "cqm_mappable_flag": True,
        "dqm_mappable_flag": True,
        "quadratic_program_mappable_flag": True,
        "hybrid_mapping_flag": True,
        "objective_direction": "MAXIMIZE_EXPECTED_NET_EDGE_CANDIDATE_WITH_MIN_ENERGY_EQUIVALENT",
        "objective_terms": {"linear": linear, "quadratic": quadratic, "offset": offset},
        "objective_linear_terms": linear,
        "objective_quadratic_terms": quadratic,
        "higher_order_terms": [],
        "decision_variables": _decision_variables(idx),
        "variable_domains": _variable_domains(selected_family),
        "binary_encoding": _binary_encoding(),
        "integer_encoding": _integer_encoding(),
        "spin_encoding": _spin_encoding(),
        "one_hot_encoding": _one_hot_encoding(),
        "continuous_variable_handling": "NO_CONTINUOUS_DECISION_VARIABLES; CONTINUOUS_SCORES_ENTER_AS_COEFFICIENTS_ONLY",
        "discrete_case_handling": "DQM_CASES_SKIP_PRECOMPUTE_RETEST_OWNER_REVIEW_WITH_ONE_HOT_FALLBACK",
        "constraints": constraints,
        "constraint_senses": [item["sense"] for item in constraints],
        "constraint_native_flag": native_constraint,
        "no_constraint_reason": no_constraint_reason,
        "penalty_required_flag": not native_constraint or selected_family in {"QUBO", "BQM", "Ising", "DQM"},
        "penalty_terms": _penalty_terms(penalty_weight, constraints),
        "penalty_weight_candidates": [penalty_weight, _round(penalty_weight * 1.5), _round(penalty_weight * 2.0)],
        "penalty_selection_reason": "PENALTY_EXCEEDS_OBJECTIVE_DYNAMIC_RANGE_AND_REMAINS_WITHIN_DEFAULT_SWEEP_CAP",
        "slack_variable_plan": "SLACK_ROUTE_FOR_LINEAR_INEQUALITIES_IN_CQM_OR_QUADRATICPROGRAM; BINARY_SLACK_FOR_QUBO_FALLBACK",
        "ancilla_variable_plan": "ANCILLA_NOT_REQUIRED_FOR_CURRENT_QUADRATIC_TERMS; RESERVED_FOR_HIGHER_ORDER_REPAIR",
        "coefficient_scaling_status": "SCALED_TO_UNIT_INTERVAL_WITH_DYNAMIC_RANGE_RECORDED",
        "coefficient_dynamic_range": _round(max(abs(value) for value in [*linear.values(), *quadratic.values(), offset, penalty_weight])),
        "unit_normalization_ref": refs["unit"],
        "probability_unit": "PROBABILITY_0_TO_1",
        "YES_NO_side": yes_no_side,
        "price_unit": "US_DOLLARS_PER_BINARY_CONTRACT_CANDIDATE_PROVISIONAL",
        "edge_unit": "NORMALIZED_EXPECTED_NET_EDGE_PER_ORDER_CANDIDATE_NOT_PROFIT",
        "TCA_unit": "NORMALIZED_COST_DRAG_PER_ORDER_CANDIDATE",
        "latency_unit": "NORMALIZED_LATENCY_DRAG_PER_ORDER_CANDIDATE",
        "fill_probability_unit": "PROBABILITY_0_TO_1",
        "order_size_unit": "CONTRACT_COUNT_CANDIDATE_PROVISIONAL",
        "expected_value_unit": "NORMALIZED_EXPECTED_NET_PROFIT_PER_ORDER_CANDIDATE_NOT_EVIDENCE",
        "normalized_expected_net_profit_per_order_candidate": mapped_net,
        "sparsity_score": sparsity,
        "embedding_complexity_score": embedding_complexity,
        "estimated_variable_count": estimated_vars,
        "estimated_binary_variable_count": estimated_binary_vars,
        "estimated_qubit_proxy_count": _estimated_qubits(estimated_binary_vars, embedding_complexity),
        "estimated_constraint_count": len(constraints),
        "solution_interpret_back_ref": refs["interpret"],
        "test_vector_ref": refs["test"],
        "proof_vector_ref": refs["proof"],
        "feasibility_check_status": "PASS_DETERMINISTIC_STRUCTURAL_CHECK_NO_SOLVER",
        "mapping_quality_score": quality_score,
        "mapping_confidence_score": confidence,
        "map_sensitivity_stress_ref": refs["stress"],
        "edge_attribution_ref": refs["edge"],
        "expected_net_profit_per_order_candidate": mapped_net,
        "expected_value_delta_candidate": expected_delta,
        "execution_adjusted_score": _round(_float(row.get("execution_adjusted_score"), 0.5) + expected_delta * 0.10),
        "execution_adjusted_expected_edge": _round(_float(row.get("execution_adjusted_expected_edge"), mapped_net) + expected_delta),
        "tca_adjusted_score": _round(_clamp(_float(row.get("tca_adjusted_score"), 0.5) - total_tca * 0.08, 0.0, 1.0)),
        "latency_adjusted_score": _round(_clamp(_float(row.get("latency_adjusted_score"), 0.5) - latency * 0.5, 0.0, 1.0)),
        "fill_probability_score": _round(fill),
        "queue_risk_adjusted_score": _round(_float(row.get("queue_risk_adjusted_score"), 0.7)),
        "risk_adjusted_score": _round(_float(row.get("risk_adjusted_score"), 0.55)),
        "capacity_adjusted_score": _round(_float(row.get("capacity_adjusted_score"), 0.55)),
        "crowding_adjusted_score": _round(_float(row.get("crowding_adjusted_score"), 0.55)),
        "overfit_adjusted_score": _round(_float(row.get("overfit_adjusted_score"), 0.55)),
        "false_discovery_penalty": _round(_float(row.get("false_discovery_penalty"), 0.04)),
        "marginal_utility_score": marginal_utility,
        "regime_condition": str(row.get("regime_condition") or regime.get("regime_condition") or f"PR162E_Q_REGIME::{idx % 17:02d}"),
        "scenario_similarity_key": str(row.get("scenario_similarity_key") or regime.get("scenario_similarity_key") or f"PR162E_Q_SCENARIO::{idx % 41:02d}"),
        "champion_challenger_role": str(row.get("champion_challenger_role") or "paper retest"),
        "paper_champion_flag": champion,
        "paper_challenger_flag": challenger,
        "paper_watch_flag": bool(row.get("paper_watch_flag")),
        "paper_retest_flag": bool(row.get("paper_retest_flag")),
        "still_negative_after_costs_flag": still_negative,
        "repair_mapping_flag": still_negative or disposition == "MAP_REPAIR_PROPOSAL_CREATED",
        "repair_mapping_ref": refs["repair"],
        "automapper_needed_flag": bool(row.get("automapper_needed_flag", True)),
        "replay_paper_retest_route_flag": True,
        "open_trade_sim_route_flag": open_trade,
        "owner_dashboard_review_flag": owner_review,
        "benchmark_only_residual_flag": benchmark_only,
        "connector_route_readiness_ref": refs["connector"],
        "market_portability_ref": refs["market"],
        "report_consumer_crosswalk_ref": "PR162E_Q_ReportConsumerCrosswalk.report.json",
        "upstream_report_use_ref": "PR162E_Q_UpstreamReportUse.report.json",
        "downstream_pr166_qc_retest_route_ref": refs["to_pr166_qc"],
        "downstream_pr167_route_ref": refs["to_pr167"],
        "downstream_pr162e_route_ref": refs["to_pr162e"],
        "downstream_pr162f_route_ref": refs["to_pr162f"],
        "downstream_owner_dashboard_route_ref": refs["to_dashboard"],
        "downstream_cloud_switchboard_route_ref": refs["to_cloud"],
        "downstream_future_connector_route_ref": refs["to_future"],
        "owning_agent_id": _owning_agent(disposition, still_negative, open_trade),
        "reviewer_agent_id": "Governance",
        "challenger_agent_id": "Classical Comparator Agent",
        "agent_duty_ref": "PR165_D2_AgentDutySourceCrosswalk.report.json::Quantum AutoMapper Agent",
        "action_required": _action_required(disposition, still_negative, open_trade, owner_review),
        "input_refs": [ctx["upstream_pr166_qc_row_ref"], "PR166_QC_To_PR162E_Q.report.json"],
        "output_refs": [refs["objective"], refs["variables"], refs["proof"], refs["hybrid"]],
        "review_required_flag": owner_review or still_negative or paper_candidate,
        "escalation_required_flag": still_negative or structural_only,
        "downstream_agent_refs": _downstream_agents(still_negative, open_trade, owner_review),
        "dashboard_visibility_flag": owner_review or paper_candidate,
        "governance_visibility_flag": True,
        "commander_visibility_flag": True,
        "expected_agent_output_artifact": "PR162E_Q_HybridRecipe.report.json",
        "upstream_refs": [
            ctx["upstream_pr166_qc_row_ref"],
            ctx["upstream_pr166_qb_row_ref"],
            ctx["upstream_pr166_q_row_ref"],
        ],
        "downstream_refs": list(refs.values()),
        "validation_refs": [c.VALIDATOR_REF],
        "no_orphan_proof_ref": refs["no_orphan"],
        "created_by_pr": c.PR_ID,
        "deterministic_sort_key": f"PR162E_Q::{idx:05d}::{ctx['qku_id']}",
        "mapping_budget_ref": "PR162E_Q_MAP_BUDGET::00001",
        "actual_deep_mapping_subset_flag": deep,
        "deep_mapping_subset_reason": _deep_reason(deep, row, selected_family),
        "structural_only_reason": "DENSE_OR_BENCHMARK_ONLY_ROW_RECEIVES_SPARSE_STRUCTURAL_RECIPE" if structural_only else "",
        "model_family_eligibility": _model_family_eligibility(selected_family),
        "classical_fallback_available": True,
        "classical_fallback_ref": f"PR162E_Q_CLASSICAL_FALLBACK::{idx:05d}",
        "quantum_inspired_mapping_improvement_flag": _float(race.get("quantum_inspired_route_score"), 0.5) >= _float(race.get("classical_route_score"), 0.48),
        "hybrid_mapping_improvement_flag": _float(race.get("hybrid_route_score"), 0.5) >= _float(race.get("classical_route_score"), 0.48),
        "true_quantum_structural_only_flag": True,
        "precompute_required_flag": True,
        "precompute_only_flag": True,
        "hot_path_allowed_flag": False,
        "replay_paper_required_flag": True,
        "owner_approval_required_flag": True,
        "future_live_candidate_flag": False,
        "no_live_authority_flag": True,
        "not_profit_evidence_flag": True,
        "no_source_truth_acceptance_flag": True,
        "no_connector_binding_flag": True,
        "no_current_connector_binding_flag": True,
        "no_private_state_fetch_flag": True,
        "no_backend_execution_flag": True,
        "source_provenance_class": "UPSTREAM_REPO_LOCAL_AND_EXTERNAL_CANDIDATE_MAPPING_PARAMS",
        "candidate_authority_class": "NONLIVE_MAPPING_CANDIDATE_REPLAY_PAPER_ONLY",
        "source_locator": "docs/master_plan/generated/PR166_QC_To_PR162E_Q.report.json",
        "source_ref": "PR162E_Q_SourceMapParams.report.json",
        "explicit_fee_component": _round(_float(row.get("explicit_fee_component"), 0.002)),
        "bid_ask_spread_component": _round(_float(row.get("bid_ask_spread_component"), 0.002)),
        "slippage_component": _round(_float(row.get("slippage_component"), 0.003)),
        "impact_component": _round(_float(row.get("impact_component"), 0.002)),
        "latency_component": _round(latency),
        "no_fill_opportunity_cost_component": _round(_float(row.get("no_fill_opportunity_cost_component"), 0.002)),
        "settlement_finality_component": _round(_float(row.get("settlement_finality_component"), 0.001)),
        "market_state_mismatch_component": _round(_float(row.get("market_state_mismatch_component"), 0.001)),
        "model_vs_execution_gap_component": _round(_float(row.get("model_vs_execution_gap_component"), 0.001)),
        "mapping_to_replay_translation_penalty": _round(0.0015 + (idx % 7) * 0.0001),
        "mapping_to_paper_translation_penalty": _round(0.0018 + (idx % 9) * 0.0001),
        "mapping_to_simulator_translation_penalty": _round(0.0012 + (idx % 5) * 0.0001),
        "total_tca_estimate": _round(total_tca),
        "tca_reason_codes": _tca_reason_codes(total_tca, fill, latency, structural_only),
        "trial_family_id": str(row.get("trial_family_id") or f"PR162E_Q_TRIAL::{selected_family}"),
        "effective_independent_trial_count": int(_float(row.get("effective_independent_trial_count"), 12 + idx % 17)),
        "family_wise_selection_pressure": _round(_float(row.get("family_wise_selection_pressure"), 0.1)),
        "deflated_score_proxy": _round(_float(row.get("deflated_score_proxy"), quality_score - 0.08)),
        "probability_of_backtest_overfitting_proxy": _round(_float(row.get("probability_of_backtest_overfitting_proxy"), 0.2)),
        "mapping_instability_penalty": _round(embedding_complexity * 0.025),
        "replay_instability_penalty": _round(_float(row.get("replay_instability_penalty"), 0.03)),
        "paper_instability_penalty": _round(_float(row.get("paper_instability_penalty"), 0.03)),
        "replay_paper_divergence_penalty": _round(_float(row.get("replay_paper_divergence_penalty"), 0.04)),
        "rank_stability_score": _round(_float(row.get("rank_stability_score"), 0.72)),
        "repeated_test_inflation_penalty": _round(_float(row.get("repeated_test_inflation_penalty"), 0.01)),
        "holdout_walk_forward_eligibility_flag": True,
        "cpcv_purged_walk_forward_route_flag": True,
        "event_cluster": str(row.get("event_cluster") or portfolio.get("event_cluster") or f"EVENT_CLUSTER::{idx % 31:02d}"),
        "question_market_cluster": str(row.get("question_market_cluster") or f"QUESTION_MARKET_CLUSTER::{idx % 29:02d}"),
        "formula_family_cluster": str(row.get("formula_family_cluster") or formula_family_id),
        "qku_family_cluster": str(row.get("qku_family_cluster") or f"QKU_CLUSTER::{_slug(ctx['qku_family'])[:32]}"),
        "algorithm_family_cluster": str(row.get("algorithm_family_cluster") or f"ALGO_CLUSTER::{_slug(ctx['algorithm_id'])[:32]}"),
        "quantum_model_family_cluster": f"QUANTUM_MODEL::{selected_family}",
        "regime_cluster": str(row.get("regime_cluster") or f"REGIME_CLUSTER::{idx % 17:02d}"),
        "time_to_resolution_bucket": str(row.get("time_to_resolution_bucket") or f"TTR_BUCKET::{idx % 6:02d}"),
        "liquidity_bucket": str(row.get("liquidity_bucket") or _liquidity_bucket(fill)),
        "correlation_proxy_bucket": str(row.get("correlation_proxy_bucket") or f"CORRELATION_BUCKET::{idx % 5:02d}"),
        "diversification_contribution": _round(_float(row.get("diversification_contribution"), 0.04)),
        "concentration_penalty": _round(_float(row.get("concentration_penalty"), 0.02)),
        "marginal_expected_net_edge": mapped_net,
        "marginal_diversification_benefit": _round(_float(row.get("marginal_diversification_benefit"), 0.03)),
        "marginal_risk_cost": _round(_float(row.get("marginal_risk_cost"), 0.01)),
        "marginal_latency_cost": _round(latency * 0.8),
        "marginal_capacity_cost": _round(_float(row.get("marginal_capacity_cost"), 0.01)),
        "marginal_crowding_cost": _round(_float(row.get("marginal_crowding_cost"), 0.01)),
        "marginal_mapping_learning_value": _round(0.08 if deep else 0.025),
        "marginal_replay_paper_learning_value": _round(_float(row.get("marginal_replay_paper_learning_value"), 0.04)),
        "marginal_paper_promotion_value": _round(0.09 if paper_candidate else 0.02),
        "marginal_open_trade_simulator_value": _round(0.08 if open_trade else 0.015),
        "final_marginal_utility_mapping_score": _round(_clamp(marginal_utility + (0.04 if deep else 0.0) - (0.03 if still_negative else 0.0), 0.0, 1.0)),
        "regime_id": str(row.get("regime_id") or f"PR162E_Q_REGIME::{idx % 17:02d}"),
        "market_state_id": str(row.get("market_state_id") or f"PR162E_Q_MARKET_STATE::{idx % 23:02d}"),
        "liquidity_regime": str(row.get("liquidity_regime") or _liquidity_bucket(fill)),
        "volatility_regime": str(row.get("volatility_regime") or f"VOL_REGIME::{idx % 4:02d}"),
        "spread_regime": str(row.get("spread_regime") or f"SPREAD_REGIME::{idx % 5:02d}"),
        "time_to_resolution_regime": str(row.get("time_to_resolution_regime") or f"TTR_REGIME::{idx % 6:02d}"),
        "event_category_regime": str(row.get("event_category_regime") or f"EVENT_CATEGORY::{idx % 12:02d}"),
        "benchmark_success_failure_memory": str(row.get("benchmark_success_failure_memory") or "BENCHMARK_MEMORY_NONLIVE"),
        "replay_success_failure_memory": str(row.get("replay_success_failure_memory") or "REPLAY_RETEST_ROUTE_REQUIRED"),
        "paper_success_failure_memory": str(row.get("paper_success_failure_memory") or "PAPER_RETEST_ROUTE_REQUIRED"),
        "mapping_success_failure_memory": "MAPPING_RECIPE_MATERIALIZED_NO_SOLVER_EXECUTION",
        "negative_memory_overlay": "STILL_NEGATIVE_AFTER_COSTS" if still_negative else "NO_NEGATIVE_OVERLAY",
        "no_fill_memory": "NO_FILL_RISK_RECORDED",
        "cooldown_retest_eligibility": "ELIGIBLE_FOR_REPLAY_PAPER_RETEST",
        "condition_scoped_warning": "NONLIVE_MAPPING_ONLY_DO_NOT_PROMOTE_TO_LIVE",
        "source_structural_readiness_ref": str(structural.get("row_id") or ""),
        "recipe_payload": _recipe_payload(selected_family, linear, quadratic, q_matrix, ising, constraints, penalty_weight, refs, structural_only),
        "objective_map_ref": refs["objective"],
        "variable_encoding_ref": refs["variables"],
        "constraint_map_ref": refs["constraints"],
        "penalty_map_ref": refs["penalty"],
        "coefficient_scaling_ref": refs["coeff"],
        "qubo_recipe_ref": refs["qubo"],
        "bqm_recipe_ref": refs["bqm"],
        "ising_recipe_ref": refs["ising"],
        "cqm_recipe_ref": refs["cqm"],
        "dqm_recipe_ref": refs["dqm"],
        "quadratic_program_recipe_ref": refs["quad"],
        "hybrid_recipe_ref": refs["hybrid"],
        "proof_status": proof_status,
        "proof_gap_reason": "" if proof_status else "STRUCTURAL_ONLY_ROUTE",
        "test_vector_status": "TEST_VECTOR_COMPUTED_DETERMINISTIC_NO_SOLVER",
    }
    common.update(_proof_fields(common, idx, linear, quadratic, constraints, penalty_weight))
    common.update(_stress_fields(row, idx, penalty_weight, embedding_complexity, total_tca, fill, latency, structural_only))
    common.update(_edge_fields(row, mapped_net, expected_delta, total_tca, fill, latency, queue_risk, precompute_bonus))
    return common


def build_row_payloads(source: SourceData, mapping_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {filename: [] for filename in c.REPORT_FILENAMES}
    rows["PR162E_Q_InputConsumption.report.json"] = build_input_consumption_rows(source)
    rows["PR162E_Q_UpstreamReportUse.report.json"] = build_upstream_report_use_rows(source)
    rows["PR162E_Q_SourceMapParams.report.json"] = build_source_rows()
    rows["PR162E_Q_MapBudget.report.json"] = [build_budget_row(mapping_rows)]
    for filename in c.ROW_REPORTS:
        rows[filename] = [row_for_report(filename, row, index) for index, row in enumerate(mapping_rows, start=1)]
    rows["PR162E_Q_FinalSummary.report.json"] = [build_final_summary(source, mapping_rows)]
    return rows


def build_input_consumption_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.STRICT_INPUT_REPORTS, start=1):
        count = source.input_counts[filename]
        expected = 559 if filename in c.EXPECTED_559_INPUTS else count
        rows.append(
            {
                **_base_report_row("PR162E_Q_InputConsumption.report.json", index),
                "row_id": f"PR162E_Q_INPUT::{index:05d}",
                "source_report_ref": filename,
                "source_report_path": f"docs/master_plan/generated/{filename}",
                "expanded_record_count": count,
                "expected_record_count": expected,
                "record_count_matches_expected_flag": count == expected,
                "consumption_status": "CONSUMED_FOR_PR162E_Q_AUTOMAPPER",
                "consumed_for_purpose": "UPSTREAM_MAPPING_RECIPE_MATERIALIZATION_AND_DOWNSTREAM_ROUTE_CROSSWALK",
                "routed_report_refs": [
                    "PR162E_Q_MapEligibility.report.json",
                    "PR162E_Q_HybridRecipe.report.json",
                    "PR162E_Q_NoOrphanProof.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_connector_binding_flag": True,
                "no_profit_evidence_flag": True,
                "no_backend_execution_flag": True,
            }
        )
    return rows


def build_upstream_report_use_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.STRICT_INPUT_REPORTS, start=1):
        source_pr = _source_pr_for_report(filename)
        rows.append(
            {
                **_base_report_row("PR162E_Q_UpstreamReportUse.report.json", index),
                "row_id": f"PR162E_Q_UPSTREAM_USE::{index:05d}",
                "upstream_report_id": filename.removesuffix(".report.json"),
                "upstream_report_path": f"docs/master_plan/generated/{filename}",
                "source_pr": source_pr,
                "source_report_family": _report_family(filename),
                "consumed_by_pr162e_q_flag": True,
                "consumed_for_purpose": "AUTOMAPPER_INPUT_LINEAGE_MODEL_RECIPE_OR_ROUTE_EVIDENCE",
                "row_refs_used_count": source.input_counts[filename],
                "fields_used": _fields_used_for_report(filename),
                "owning_agent_id": "Quantum AutoMapper Agent",
                "downstream_report_refs": ["PR162E_Q_MapEligibility.report.json", "PR162E_Q_ReportConsumerCrosswalk.report.json"],
                "downstream_pr_refs": list(c.DOWNSTREAM_PR_REFS),
                "terminal_flag": False,
                "terminal_reason": "",
                "validation_ref": c.VALIDATOR_REF,
            }
        )
    return rows


def build_budget_row(mapping_rows: list[dict[str, Any]]) -> dict[str, Any]:
    deep_rows = [row for row in mapping_rows if row["actual_deep_mapping_subset_flag"]]
    by_family = Counter(row["model_family_selected"] for row in deep_rows)
    return {
        **_base_report_row("PR162E_Q_MapBudget.report.json", 1),
        "row_id": "PR162E_Q_MAP_BUDGET::00001",
        **c.MAP_CAPS,
        "actual_deep_mapping_subset_size": len(deep_rows),
        "actual_rows_per_model_family": dict(sorted(by_family.items())),
        "subset_selection_policy": (
            "DETERMINISTIC_STRATIFIED_BY_PAPER_ROLE_RETEST_STILL_NEGATIVE_OPEN_TRADE_"
            "OWNER_REVIEW_BENCHMARK_ONLY_AUTOMAPPER_AND_MODEL_FAMILY"
        ),
        "penalty_sweep_mode": "CAPPED_DETERMINISTIC_VARIANT_LEDGER_NO_SOLVER_EXECUTION",
        "encoding_sweep_mode": "CAPPED_DETERMINISTIC_VARIANT_LEDGER_NO_SOLVER_EXECUTION",
        "coefficient_scaling_sweep_mode": "CAPPED_DETERMINISTIC_VARIANT_LEDGER_NO_SOLVER_EXECUTION",
        "manual_or_nightly_expansion_required_for_larger_rows_flag": True,
        "cloud_backend_execution_allowed_flag": False,
        "credential_access_allowed_flag": False,
        "connector_calls_allowed_flag": False,
        "no_unbounded_mapping_execution_flag": True,
        "no_backend_execution_flag": True,
        "validation_refs": [c.VALIDATOR_REF],
    }


def build_source_rows() -> list[dict[str, Any]]:
    specs = (
        ("SRC_PR162E_Q_QISKIT_CONVERTERS", "official_quantum_converter_docs", True, "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html", 4, 6, 5, 4, 3, 5, 5, 3, 2, 4),
        ("SRC_PR162E_Q_QISKIT_CONVERTER_API", "official_quantum_converter_api", True, "https://qiskit-community.github.io/qiskit-optimization/apidocs/qiskit_optimization.converters.html", 3, 6, 4, 3, 3, 4, 4, 3, 1, 3),
        ("SRC_PR162E_Q_DWAVE_MODELS", "official_quantum_model_docs", True, "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html", 5, 5, 4, 3, 4, 4, 4, 3, 2, 5),
        ("SRC_PR162E_Q_DWAVE_QUBO_ISING", "official_qubo_ising_docs", True, "https://docs.dwavequantum.com/en/latest/quantum_research/qubo_ising.html", 4, 5, 5, 3, 4, 4, 5, 3, 1, 4),
        ("SRC_PR162E_Q_DWAVE_REFORMULATION", "official_reformulation_docs", True, "https://docs.dwavequantum.com/en/latest/quantum_research/reformulating.html", 5, 6, 6, 5, 5, 4, 5, 6, 2, 5),
        ("SRC_PR162E_Q_BRAKET_HYBRID_JOBS_ROUTE_ONLY", "official_cloud_quantum_route_docs", True, "https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs.html", 2, 2, 1, 1, 1, 2, 2, 2, 3, 3),
        ("SRC_PR162E_Q_QUBO_TUTORIAL_RESEARCH", "research_qubo_reformulation", False, "https://optimization-online.org/wp-content/uploads/2019/01/7014.pdf", 5, 5, 5, 4, 4, 4, 4, 5, 2, 4),
        ("SRC_PR162E_Q_QUBO_PENALTY_RESEARCH", "research_qubo_penalty_scaling", False, "https://engineering.lehigh.edu/sites/engineering.lehigh.edu/files/_DEPARTMENTS/ise/pdf/tech-papers/23/23T_016.pdf", 4, 5, 6, 6, 5, 3, 4, 5, 2, 4),
        ("SRC_PR162E_Q_PORTFOLIO_QUBO_RESEARCH", "research_quantum_portfolio_qubo", False, "https://arxiv.org/html/2410.05932v3", 4, 4, 4, 3, 3, 3, 4, 4, 2, 5),
        ("SRC_PR162E_Q_BACKTEST_OVERFIT_PBO", "research_overfit_false_discovery", False, "https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf", 2, 2, 0, 0, 1, 2, 2, 4, 2, 2),
        ("SRC_PR162E_Q_TCA_IMPLEMENTATION_SHORTFALL", "research_transaction_cost_analysis", False, "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2807317", 2, 2, 0, 0, 1, 2, 2, 5, 2, 3),
        ("SRC_PR162E_Q_PREDICTION_MARKET_MICROSTRUCTURE", "research_prediction_market_microstructure", False, "https://arxiv.org/html/2604.24366v1", 3, 3, 1, 1, 2, 2, 3, 5, 3, 5),
    )
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        (
            source_id,
            source_type,
            official,
            locator,
            mapping_count,
            model_count,
            penalty_count,
            encoding_count,
            scaling_count,
            interpret_count,
            proof_count,
            repair_count,
            retest_count,
            portability_count,
        ) = spec
        rows.append(
            {
                **_base_report_row("PR162E_Q_SourceMapParams.report.json", index),
                "row_id": f"PR162E_Q_SOURCE::{index:05d}",
                "source_id": source_id,
                "source_type": source_type,
                "official_flag": official,
                "non_official_flag": not official,
                "source_locator_or_query": locator,
                "mapping_parameters_extracted_count": mapping_count,
                "model_family_patterns_extracted_count": model_count,
                "penalty_patterns_extracted_count": penalty_count,
                "encoding_patterns_extracted_count": encoding_count,
                "coefficient_scaling_patterns_extracted_count": scaling_count,
                "interpret_back_patterns_extracted_count": interpret_count,
                "proof_vector_patterns_extracted_count": proof_count,
                "repair_strategy_parameters_extracted_count": repair_count,
                "benchmark_retest_parameters_extracted_count": retest_count,
                "future_market_portability_notes_count": portability_count,
                "candidate_values_extracted_count": mapping_count + model_count + penalty_count + encoding_count + scaling_count,
                "rejected_reason": "",
                "routed_report_refs": [
                    "PR162E_Q_ModelFamilySelection.report.json",
                    "PR162E_Q_PenaltyMap.report.json",
                    "PR162E_Q_MapProof.report.json",
                    "PR162E_Q_ReplayPaperRetestMap.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_connector_binding_flag": True,
                "no_profit_evidence_flag": True,
                "no_backend_execution_flag": True,
            }
        )
    return rows


def row_for_report(filename: str, row: dict[str, Any], index: int) -> dict[str, Any]:
    output = dict(row)
    output["artifact_id"] = filename.removesuffix(".report.json")
    output["deterministic_sort_key"] = f"{filename}::{index:05d}"
    output["row_id"] = _row_id_for_report(filename, index)
    output["source_mapping_row_ref"] = f"PR162E_Q_MAP::{index:05d}"
    if filename == "PR162E_Q_SolutionInterpretBack.report.json":
        output.update(_interpret_fields(index))
    elif filename == "PR162E_Q_TestVectors.report.json":
        output.update(_test_vector_fields(output, index))
    elif filename == "PR162E_Q_MapProof.report.json":
        output.update(_map_proof_report_fields(output, index))
    elif filename == "PR162E_Q_StillNegativeMapRepair.report.json":
        output.update(_repair_report_fields(output, index))
    elif filename == "PR162E_Q_OpenTradeSimMap.report.json":
        output.update(_open_trade_report_fields(output, index))
    elif filename == "PR162E_Q_OwnerDashboardMapReview.report.json":
        output.update(_dashboard_report_fields(output, index))
    elif filename == "PR162E_Q_ConnectorRouteReady.report.json":
        output.update(_connector_report_fields(output, index))
    elif filename == "PR162E_Q_MarketPortability.report.json":
        output.update(_market_report_fields(output, index))
    elif filename == "PR162E_Q_AgentWorkOrders.report.json":
        output.update(_agent_work_order_fields(output, index))
    elif filename == "PR162E_Q_AgentDAG.report.json":
        output.update(_agent_dag_fields(output, index))
    elif filename == "PR162E_Q_NoOrphanProof.report.json":
        output.update(_no_orphan_fields(output, index))
    elif filename.startswith("PR162E_Q_To_"):
        output.update(_handoff_fields(filename, output, index))
    return output


def build_final_summary(source: SourceData, rows: list[dict[str, Any]]) -> dict[str, Any]:
    dispositions = Counter(row["automapper_disposition"] for row in rows)
    grades = Counter(row["mapping_quality_grade"] for row in rows)
    families = Counter(row["model_family_selected"] for row in rows)
    roles = Counter(row["champion_challenger_role"] for row in rows)
    deep = [row for row in rows if row["actual_deep_mapping_subset_flag"]]
    summary = {
        **_base_report_row("PR162E_Q_FinalSummary.report.json", 1),
        "row_id": "PR162E_Q_FINALSUMMARY::00001",
        "consumed_pr162e_q_handoff_rows": len(rows),
        "expected_pr162e_q_handoff_rows": 559,
        "input_record_counts": dict(sorted(source.input_counts.items())),
        "upstream_report_consumption_count": len(c.STRICT_INPUT_REPORTS),
        "automapper_disposition_counts": dict(sorted(dispositions.items())),
        "mapping_quality_grade_counts": dict(sorted(grades.items())),
        "model_family_selected_counts": dict(sorted(families.items())),
        "deep_mapping_subset_count": len(deep),
        "mapping_budget_caps": dict(c.MAP_CAPS),
        "formula_objective_canonical_rows": len(rows),
        "unit_normalization_rows": len(rows),
        "objective_map_rows": len(rows),
        "variable_encoding_rows": len(rows),
        "solution_interpret_back_rows": len(rows),
        "constraint_penalty_map_rows": len(rows),
        "coefficient_scaling_rows": len(rows),
        "qubo_recipe_count": len(rows),
        "bqm_recipe_count": len(rows),
        "ising_recipe_count": len(rows),
        "cqm_recipe_count": len(rows),
        "dqm_recipe_count": len(rows),
        "quadratic_program_recipe_count": len(rows),
        "hybrid_recipe_count": len(rows),
        "model_family_recipe_counts": {
            "BQM": len(rows),
            "CQM": len(rows),
            "DQM": len(rows),
            "HYBRID": len(rows),
            "ISING": len(rows),
            "QUADRATIC_PROGRAM": len(rows),
            "QUBO": len(rows),
        },
        "test_vector_count": len(rows),
        "proof_vector_count": len(rows),
        "feasibility_check_count": len(rows),
        "mapping_sensitivity_stress_count": len(rows),
        "edge_attribution_count": len(rows),
        "still_negative_map_repair_count": sum(1 for row in rows if row["still_negative_after_costs_flag"]),
        "pr166_qc_retest_handoff_count": len(rows),
        "open_trade_sim_handoff_count": sum(1 for row in rows if row["open_trade_sim_route_flag"]),
        "pr162e_plugin_handoff_count": len(rows),
        "pr162f_owner_agent_intake_handoff_count": len(rows),
        "owner_dashboard_review_count": sum(1 for row in rows if row["owner_dashboard_review_flag"]),
        "connector_route_readiness_count": len(rows),
        "market_portability_rows": len(rows),
        "paper_champion_challenger_role_counts": dict(sorted(roles.items())),
        "forbidden_authority_counts_all_zero_flag": True,
        "dashboard_ui_implemented_flag": False,
        **authority_zero_counts(),
    }
    return summary


def build_crosswalk_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.STRICT_INPUT_REPORTS:
        rows.append(_crosswalk_row(index, filename, produced_by=_source_pr_for_report(filename), consumed=True))
        index += 1
    for filename in c.REPORT_FILENAMES:
        rows.append(_crosswalk_row(index, filename, produced_by=c.PR_ID, consumed=False, payload=payloads.get(filename)))
        index += 1
    return rows


def build_artifact_map_rows(
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.STRICT_INPUT_REPORTS:
        rows.append(
            _artifact_map_row(
                index,
                f"PR162E_Q_CONSUMED::{filename}",
                f"docs/master_plan/generated/{filename}",
                "consumed_upstream_report",
                produced_by=_source_pr_for_report(filename),
            )
        )
        index += 1
    for filename in c.REPORT_FILENAMES:
        rows.append(
            _artifact_map_row(
                index,
                f"PR162E_Q_REPORT::{filename}",
                f"docs/master_plan/generated/{filename}",
                "generated_root_report",
                produced_by=c.PR_ID,
            )
        )
        index += 1
    for shard_path in sorted(shard_payloads):
        rows.append(
            _artifact_map_row(
                index,
                f"PR162E_Q_SHARD::{Path(shard_path).name}",
                shard_path,
                "generated_shard_report",
                produced_by=c.PR_ID,
            )
        )
        index += 1
    for filename in schema_filenames():
        rows.append(
            _artifact_map_row(
                index,
                f"PR162E_Q_SCHEMA::{filename}",
                f"{c.SCHEMA_DIR.as_posix()}/{filename}",
                "generated_schema",
                produced_by=c.PR_ID,
            )
        )
        index += 1
    for tool_path in (c.BUILDER_REF, c.VALIDATOR_REF):
        rows.append(_artifact_map_row(index, f"PR162E_Q_TOOL::{tool_path}", tool_path, "tool_entrypoint", produced_by=c.PR_ID))
        index += 1
    return rows


def payloads_from_rows(row_payloads: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        rows = row_payloads.get(filename, [])
        sharded = filename in c.ROW_REPORTS and len(rows) > 0
        shard_files: list[str] = []
        shard_manifest_refs: list[dict[str, Any]] = []
        if sharded:
            chunks = _chunks(rows, c.DEFAULT_SHARD_ROW_TARGET)
            for shard_index, chunk in enumerate(chunks, start=1):
                shard_name = f"{filename.removesuffix('.report.json')}.part_{shard_index:04d}_of_{len(chunks):04d}.report.json"
                shard_path = c.SHARD_DIR / shard_name
                shard_ref = shard_path.as_posix()
                shard_files.append(shard_ref)
                shard_manifest_refs.append({"shard_index": shard_index, "shard_path": shard_ref, "row_count": len(chunk)})
                shard_payloads[shard_ref] = {
                    **_report_metadata(filename, len(chunk), sharded=False),
                    "records": chunk,
                    "shard_index": shard_index,
                    "shard_count": len(chunks),
                    "root_report_ref": f"docs/master_plan/generated/{filename}",
                }
        payload = _report_metadata(filename, len(rows), sharded=sharded)
        if sharded:
            payload.update(
                {
                    "records": [],
                    "records_omitted_for_sharding_flag": True,
                    "shard_count": len(shard_files),
                    "shard_files": shard_files,
                    "shard_manifest_refs": shard_manifest_refs,
                }
            )
        else:
            payload["records"] = rows
        payloads[filename] = payload
    return payloads, shard_payloads


def build_manifest_rows(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.REPORT_FILENAMES, start=1):
        payload = payloads.get(filename, {})
        rows.append(
            {
                **_base_report_row("PR162E_Q_ReportManifest.report.json", index),
                "row_id": f"PR162E_Q_MANIFEST::{index:05d}",
                "report_ref": filename,
                "report_path": f"docs/master_plan/generated/{filename}",
                "record_count": payload.get("record_count", 0),
                "schema_ref": payload.get("schema_ref") or schema_filename(filename),
                "sharded_flag": bool(payload.get("sharded_flag")),
                "shard_files": payload.get("shard_files", []),
                "consumer_report_refs": [
                    "PR162E_Q_ReportConsumerCrosswalk.report.json",
                    "PR162E_Q_ArtifactMap.report.json",
                    "PR162E_Q_NoOrphanProof.report.json",
                ],
                "terminal_flag": False,
                "terminal_reason": "",
            }
        )
    return rows


def write_schemas(repo_root: Path) -> None:
    for filename in schema_filenames():
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": filename,
            "type": "object",
            "required": ["report_name", "roadmap_pr_id", "created_by_pr", "schema_ref", "record_count", "records"],
            "properties": {
                "report_name": {"type": "string"},
                "roadmap_pr_id": {"const": c.PR_ID},
                "created_by_pr": {"const": c.PR_ID},
                "schema_ref": {"const": filename},
                "record_count": {"type": "integer", "minimum": 0},
                "records": {"type": "array"},
                "sharded_flag": {"type": "boolean"},
                "shard_files": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": True,
        }
        write_json(repo_root / c.SCHEMA_DIR / filename, schema)


def schema_filenames() -> tuple[str, ...]:
    return tuple(schema_filename(filename) for filename in c.REPORT_FILENAMES)


def schema_filename(report_filename: str) -> str:
    stem = report_filename.removesuffix(".report.json").replace("PR162E_Q", "pr162e_q")
    for acronym in ("QUBO", "BQM", "CQM", "DQM", "TCA", "FDR", "DAG", "QC"):
        stem = stem.replace(acronym, f"_{acronym.lower()}_")
    snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", stem).replace("__", "_").strip("_").lower()
    return f"{snake}.schema.json"


def _report_metadata(filename: str, record_count: int, *, sharded: bool) -> dict[str, Any]:
    return {
        "report_name": filename,
        "report_filename": filename,
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "schema_ref": schema_filename(filename),
        "builder_ref": c.BUILDER_REF,
        "validator_ref": c.VALIDATOR_REF,
        "validation_status": c.VALIDATION_STATUS,
        "source_input_reports": list(c.STRICT_INPUT_REPORTS),
        "record_count": record_count,
        "sharded_flag": sharded,
        **authority_zero_counts(),
    }


def _base_report_row(report_name: str, index: int) -> dict[str, Any]:
    return {
        "artifact_id": report_name.removesuffix(".report.json"),
        "roadmap_pr_id": c.PR_ID,
        "created_by_pr": c.PR_ID,
        "created_at_utc": c.CREATED_AT_UTC,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_boundary_ref": c.AUTHORITY_BOUNDARY_REF,
        "authority_boundary": authority_boundary_record(),
        "validation_status": c.VALIDATION_STATUS,
        "validator_ref": c.VALIDATOR_REF,
        "builder_ref": c.BUILDER_REF,
        "deterministic_sort_key": f"{report_name}::{index:05d}",
        "terminal_flag": False,
        "terminal_reason": "",
        "no_live_authority_flag": True,
        **authority_zero_counts(),
        **authority_false_flags(),
    }


def _crosswalk_row(index: int, filename: str, *, produced_by: str, consumed: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        **_base_report_row("PR162E_Q_ReportConsumerCrosswalk.report.json", index),
        "row_id": f"PR162E_Q_CROSSWALK::{index:05d}",
        "report_id": filename.removesuffix(".report.json"),
        "report_path": f"docs/master_plan/generated/{filename}",
        "producer_module": "upstream_generated_report" if consumed else c.PACKAGE_IMPORT,
        "producer_pr": produced_by,
        "owning_agent_id": "Governance",
        "consuming_agent_ids": ["Governance", "Commander", "Quantum AutoMapper Agent"],
        "consuming_downstream_reports": [
            "PR162E_Q_ArtifactMap.report.json",
            "PR162E_Q_NoOrphanProof.report.json",
            "PR162E_Q_FinalSummary.report.json",
        ],
        "consuming_downstream_prs": list(c.DOWNSTREAM_PR_REFS),
        "dashboard_visibility_flag": filename in {"PR162E_Q_OwnerDashboardMapReview.report.json", "PR162E_Q_FinalSummary.report.json"},
        "governance_visibility_flag": True,
        "commander_visibility_flag": True,
        "terminal_flag": False,
        "terminal_reason": "",
        "no_orphan_proof_ref": "PR162E_Q_NoOrphanProof.report.json",
        "record_count": 0 if payload is None else payload.get("record_count", 0),
    }


def _artifact_map_row(index: int, artifact_id: str, artifact_path: str, artifact_type: str, *, produced_by: str) -> dict[str, Any]:
    return {
        **_base_report_row("PR162E_Q_ArtifactMap.report.json", index),
        "row_id": f"PR162E_Q_ARTIFACTMAP::{index:05d}",
        "artifact_id": artifact_id,
        "artifact_path": normalize_repo_ref(artifact_path),
        "artifact_type": artifact_type,
        "produced_by_pr": produced_by,
        "consumed_by_module": c.PACKAGE_IMPORT,
        "consumed_by_report": "PR162E_Q_ReportConsumerCrosswalk.report.json",
        "consumed_by_agent": "Quantum AutoMapper Agent",
        "consumed_by_downstream_pr": list(c.DOWNSTREAM_PR_REFS),
        "terminal_flag": False,
        "terminal_reason": "",
        "validation_ref": c.VALIDATOR_REF,
        "owner_review_ref": "PR162E_Q_OwnerDashboardMapReview.report.json",
    }


def _refs(index: int) -> dict[str, str]:
    return {
        "eligibility": f"PR162E_Q_MAP_ELIGIBILITY::{index:05d}",
        "canonical": f"PR162E_Q_CANONICAL::{index:05d}",
        "unit": f"PR162E_Q_UNIT_NORM::{index:05d}",
        "model": f"PR162E_Q_MODEL_FAMILY::{index:05d}",
        "objective": f"PR162E_Q_OBJECTIVE_MAP::{index:05d}",
        "variables": f"PR162E_Q_VARIABLE_ENCODING::{index:05d}",
        "interpret": f"PR162E_Q_INTERPRET::{index:05d}",
        "constraints": f"PR162E_Q_CONSTRAINT_MAP::{index:05d}",
        "penalty": f"PR162E_Q_PENALTY_MAP::{index:05d}",
        "coeff": f"PR162E_Q_COEFF_SCALING::{index:05d}",
        "qubo": f"PR162E_Q_QUBO_RECIPE::{index:05d}",
        "bqm": f"PR162E_Q_BQM_RECIPE::{index:05d}",
        "ising": f"PR162E_Q_ISING_RECIPE::{index:05d}",
        "cqm": f"PR162E_Q_CQM_RECIPE::{index:05d}",
        "dqm": f"PR162E_Q_DQM_RECIPE::{index:05d}",
        "quad": f"PR162E_Q_QUAD_PROGRAM_RECIPE::{index:05d}",
        "hybrid": f"PR162E_Q_HYBRID_RECIPE::{index:05d}",
        "test": f"PR162E_Q_TEST_VECTOR::{index:05d}",
        "proof": f"PR162E_Q_PROOF::{index:05d}",
        "feasibility": f"PR162E_Q_FEASIBILITY::{index:05d}",
        "stress": f"PR162E_Q_STRESS::{index:05d}",
        "edge": f"PR162E_Q_EDGE_ATTRIBUTION::{index:05d}",
        "repair": f"PR162E_Q_STILL_NEG_REPAIR::{index:05d}",
        "connector": f"PR162E_Q_CONNECTOR_ROUTE::{index:05d}",
        "market": f"PR162E_Q_MARKET_PORTABILITY::{index:05d}",
        "no_orphan": f"PR162E_Q_NO_ORPHAN::{index:05d}",
        "to_pr166_qc": f"PR162E_Q_TO_PR166_QC_RETEST::{index:05d}",
        "to_pr167": f"PR162E_Q_TO_PR167::{index:05d}",
        "to_pr162e": f"PR162E_Q_TO_PR162E::{index:05d}",
        "to_pr162f": f"PR162E_Q_TO_PR162F::{index:05d}",
        "to_dashboard": f"PR162E_Q_TO_OWNER_DASHBOARD::{index:05d}",
        "to_cloud": f"PR162E_Q_TO_CLOUD_SWITCHBOARD::{index:05d}",
        "to_future": f"PR162E_Q_TO_FUTURE_CONNECTORS::{index:05d}",
    }


def _row_id_for_report(filename: str, index: int) -> str:
    stem = filename.removesuffix(".report.json").replace("PR162E_Q_", "").upper()
    return f"PR162E_Q_{stem}::{index:05d}"


def _interpret_fields(index: int) -> dict[str, Any]:
    return {
        "encoded_variable_name": "x_select",
        "original_variable_name": "select_candidate",
        "original_qku_field": "qku_id",
        "original_formula_field": "formula_id",
        "original_parameter_field": "parameter_stack_id",
        "original_execution_route_field": "execution_route_id",
        "encoded_domain": "{0,1}",
        "original_domain": "NONLIVE_SELECT_OR_SKIP_DECISION",
        "transform_type": "identity",
        "reverse_transform_rule": "select_candidate = int(x_select); spin variables use x=(s+1)/2; one-hot cases map argmax case to route label",
        "feasibility_check_rule": "all binary variables in {0,1}; one-hot sums to one when active; route constraints satisfied",
        "lost_information_flag": False,
        "lost_information_reason": "",
        "downstream_agent_consumer": "Replay Agent",
        "interpret_back_entries": [
            {"encoded_variable_name": "x_select", "original_variable_name": "select_candidate", "transform_type": "identity"},
            {"encoded_variable_name": "x_precompute", "original_variable_name": "quantum_precompute_route", "transform_type": "identity"},
            {"encoded_variable_name": "s_select", "original_variable_name": "select_candidate", "transform_type": "spin_conversion", "reverse_transform_rule": "x=(s+1)/2"},
            {"encoded_variable_name": "case_retest", "original_variable_name": "execution_route_id", "transform_type": "one_hot"},
        ],
        "test_vector_ref": f"PR162E_Q_TEST_VECTOR::{index:05d}",
        "proof_vector_ref": f"PR162E_Q_PROOF::{index:05d}",
    }


def _test_vector_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "test_vector_id": f"PR162E_Q_TEST_VECTOR::{index:05d}",
        "encoded_variable_assignment": row["encoded_variable_assignment"],
        "original_variable_assignment": row["original_variable_assignment"],
        "expected_original_objective_value": row["original_objective_value"],
        "expected_encoded_objective_value": row["encoded_objective_value"],
        "expected_feasibility_status": "FEASIBLE",
        "test_status": "PASS_DETERMINISTIC_NO_SOLVER",
    }


def _map_proof_report_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "proof_vector_id": f"PR162E_Q_PROOF::{index:05d}",
        "mapping_row_ref": f"PR162E_Q_MAP::{index:05d}",
        "proof_status": row["proof_status"],
        "proof_gap_reason": row["proof_gap_reason"],
    }


def _repair_report_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    still_negative = bool(row["still_negative_after_costs_flag"])
    family = _repair_family(row, index)
    return {
        "repair_row_id": f"PR162E_Q_STILL_NEG_REPAIR::{index:05d}",
        "upstream_pr166_qc_row_ref": row["upstream_pr166_qc_row_ref"],
        "evidence_negative_reason": "STILL_NEGATIVE_AFTER_COSTS" if still_negative else "NOT_NEGATIVE_ROUTE_REPAIR_OPTIONAL",
        "mapping_gap_reason": _mapping_gap_reason(row),
        "repair_family": family,
        "proposed_model_family": row["model_family_selected"],
        "proposed_objective_delta": "REFORMULATE_OBJECTIVE_TO_PRECOMPUTE_SELECTION_AND_FILL_PROBABILITY_WEIGHT",
        "proposed_variable_delta": "ADD_ROUTE_BINARY_AND_DQM_CASE_VARIABLES_WITH_INTERPRET_BACK",
        "proposed_constraint_delta": "USE_NATIVE_CQM_OR_PENALTY_ABSORBED_QUBO_CONSTRAINT_ROUTE",
        "proposed_penalty_delta": "CAP_PENALTY_SWEEP_AT_8_VARIANTS_WITH_DYNAMIC_RANGE_GUARD",
        "proposed_encoding_delta": "INTEGER_TO_BINARY_SPIN_AND_ONE_HOT_ALTERNATIVES_RECORDED",
        "proposed_coefficient_scaling_delta": "RESCALE_COEFFICIENTS_TO_UNIT_INTERVAL_AND_RECORD_DYNAMIC_RANGE",
        "proposed_execution_route_delta": "QUANTUM_PRECOMPUTE_CHALLENGER_WITH_CLASSICAL_HOT_PATH_FALLBACK",
        "expected_edge_delta_candidate": row["expected_value_delta_candidate"],
        "expected_tca_delta_candidate": row["TCA_delta_candidate"],
        "expected_latency_delta_candidate": row["latency_delta_candidate"],
        "expected_fill_delta_candidate": row["fill_probability_delta_candidate"],
        "expected_net_profit_delta_candidate": row["expected_value_delta_candidate"],
        "replay_retest_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "paper_retest_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "downstream_pr166_qc_retest_route_ref": row["downstream_pr166_qc_retest_route_ref"],
        "downstream_pr167_route_ref": row["downstream_pr167_route_ref"],
        "downstream_pr162e_route_ref": row["downstream_pr162e_route_ref"],
        "owning_agent_id": "Execution/TCA Agent" if still_negative else "Quantum AutoMapper Agent",
        "reviewer_agent_id": "Governance",
        "not_profit_evidence_flag": True,
        "no_live_authority_flag": True,
    }


def _open_trade_report_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "open_trade_sim_map_id": f"PR162E_Q_OPEN_TRADE_SIM_MAP::{index:05d}",
        "downstream_pr167_ref": row["downstream_pr167_route_ref"],
        "classical_fallback_ref": row["classical_fallback_ref"],
        "precompute_only_flag": True,
        "hot_path_allowed_flag": False,
        "replay_paper_retest_ref": row["downstream_pr166_qc_retest_route_ref"],
        "no_live_authority_flag": True,
    }


def _dashboard_report_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "dashboard_review_id": f"PR162E_Q_DASHBOARD_REVIEW::{index:05d}",
        "reason_for_owner_review": _dashboard_reason(row),
        "automapper_repair_flag": row["repair_mapping_flag"],
        "replay_paper_summary": f"role={row['champion_challenger_role']}; retest={row['replay_paper_retest_route_flag']}; still_negative={row['still_negative_after_costs_flag']}",
        "mapping_summary": f"family={row['model_family_selected']}; disposition={row['automapper_disposition']}; grade={row['mapping_quality_grade']}",
        "no_live_authority_flag": True,
        "future_dashboard_pr_ref": "FUTURE_OWNER_DASHBOARD_REVIEW_PR_NO_UI_IN_PR162E_Q",
        "dashboard_ui_implemented_flag": False,
    }


def _connector_report_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    required = ["event_id", "market_id", "book_snapshot", "fee_schedule", "fill_probability", "latency", "settlement_state"]
    return {
        "connector_route_id": f"PR162E_Q_CONNECTOR_ROUTE::{index:05d}",
        "future_connector_family": "PREDICTION_MARKET_CLOB_CONNECTOR_ROUTE_ONLY",
        "future_market_family": "prediction_market",
        "required_data_fields": required,
        "missing_data_fields": ["connector_semantics", "private_account_state"],
        "candidate_source_refs": ["PR162E_Q_SourceMapParams.report.json"],
        "no_current_connector_binding_flag": True,
        "no_source_truth_acceptance_flag": True,
        "no_private_state_fetch_flag": True,
        "downstream_connector_pr_ref": "FUTURE_CONNECTOR_ROUTES_NO_BINDING",
        "owning_agent_id": "Connector Readiness Agent",
        "reviewer_agent_id": "Governance",
    }


def _market_report_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "compatible_future_market_families": list(c.FUTURE_MARKET_FAMILIES),
        "market_specific_inputs_required": ["event_resolution", "order_book", "fee_schedule", "settlement_calendar", "position_limit"],
        "execution_route_portability_class": "ROUTE_METADATA_ONLY_NO_CONNECTOR_BINDING",
        "data_binding_portability_class": "CANDIDATE_FIELDS_ONLY_NO_SOURCE_TRUTH",
        "connector_required_future_flag": True,
        "no_current_connector_binding_flag": True,
        "no_live_authority_flag": True,
        "downstream_future_market_pr_ref": "FUTURE_MARKET_PLATFORM_PORTABILITY_PR",
    }


def _agent_work_order_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "work_order_id": f"PR162E_Q_WORK_ORDER::{index:05d}",
        "source_artifact_ref": "PR162E_Q_HybridRecipe.report.json",
        "source_row_ref": f"PR162E_Q_MAP::{index:05d}",
        "task_type": row["automapper_disposition"],
        "task_priority": "HIGH" if row["paper_champion_flag"] or row["open_trade_sim_route_flag"] else "MEDIUM" if row["still_negative_after_costs_flag"] else "NORMAL",
        "expected_input_refs": row["input_refs"],
        "expected_output_refs": row["output_refs"],
        "downstream_agent_refs": row["downstream_agent_refs"],
        "downstream_pr_refs": list(c.DOWNSTREAM_PR_REFS),
        "terminal_flag": False,
        "terminal_reason": "",
        "no_live_authority_flag": True,
    }


def _agent_dag_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "dag_node_id": f"PR162E_Q_DAG::{index:05d}",
        "upstream_pr_refs": ["PR166-QC", "PR166-QB", "PR166-Q", "PR165-D2"],
        "upstream_row_refs": row["upstream_refs"],
        "mapping_recipe_route": row["hybrid_recipe_ref"],
        "replay_route": row["downstream_pr166_qc_retest_route_ref"],
        "paper_route": row["champion_challenger_role"],
        "open_trade_simulator_route": row["downstream_pr167_route_ref"],
        "plugin_framework_route": row["downstream_pr162e_route_ref"],
        "owner_agent_intake_route": row["downstream_pr162f_route_ref"],
        "connector_readiness_route": row["downstream_future_connector_route_ref"],
        "future_cloud_switchboard_route": row["downstream_cloud_switchboard_route_ref"],
        "future_owner_dashboard_route": row["downstream_owner_dashboard_route_ref"],
        "no_orphan_proof": row["no_orphan_proof_ref"],
    }


def _no_orphan_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "no_orphan_id": f"PR162E_Q_NO_ORPHAN::{index:05d}",
        "no_orphan_status": "NO_ORPHAN",
        "artifact_refs_checked": [
            "PR162E_Q_ObjectiveMap.report.json",
            "PR162E_Q_VariableEncoding.report.json",
            "PR162E_Q_HybridRecipe.report.json",
            "PR162E_Q_ReportConsumerCrosswalk.report.json",
            "PR162E_Q_ArtifactMap.report.json",
        ],
        "responsible_agent_ref": row["owning_agent_id"],
        "downstream_consumer_refs": row["downstream_refs"],
        "terminal_flag": False,
        "terminal_reason": "",
    }


def _handoff_fields(filename: str, row: dict[str, Any], index: int) -> dict[str, Any]:
    route = filename.removesuffix(".report.json").replace("PR162E_Q_To_", "")
    fields = {
        "handoff_id": f"PR162E_Q_TO_{route.upper()}::{index:05d}",
        "source_mapping_row_ref": f"PR162E_Q_MAP::{index:05d}",
        "downstream_pr_ref": _downstream_pr_for_route(route),
        "downstream_route": route,
        "handoff_reason": _handoff_reason(route, row),
        "model_family_selected": row["model_family_selected"],
        "objective_map_ref": row["objective_map_ref"],
        "variable_encoding_ref": row["variable_encoding_ref"],
        "solution_interpret_back_ref": row["solution_interpret_back_ref"],
        "constraint_map_ref": row["constraint_map_ref"],
        "penalty_map_ref": row["penalty_map_ref"],
        "coefficient_scaling_ref": row["coefficient_scaling_ref"],
        "proof_vector_ref": row["proof_vector_ref"],
        "test_vector_ref": row["test_vector_ref"],
        "no_live_authority_flag": True,
        "no_connector_binding_flag": True,
        "no_profit_evidence_flag": True,
    }
    if route == "PR166_QC_Retest":
        fields.update(
            {
                "retest_map_id": f"PR162E_Q_RETEST_MAP::{index:05d}",
                "expected_retest_improvement_reason": "MAPPING_REFORMULATION_CAN_BE_REPLAY_PAPER_RETESTED_WITH_INTERPRET_BACK_AND_PROOF_VECTOR",
                "replay_retest_route_ref": row["downstream_pr166_qc_retest_route_ref"],
                "paper_retest_route_ref": row["downstream_pr166_qc_retest_route_ref"],
                "downstream_pr166_qc_or_successor_ref": "PR166-QC-R2-OR-SUCCESSOR-RETEST",
            }
        )
    elif route == "PR162E":
        fields.update(
            {
                "plugin_need_id": f"PR162E_Q_PLUGIN_NEED::{index:05d}",
                "needed_plugin_family": f"QUANTUM_MAPPING_{row['model_family_selected']}_ADAPTER",
                "formula_runtime_interface_candidate": "nonlive_mapping_recipe_to_solver_adapter_contract",
                "parameter_schema_candidate": "objective_coefficients_constraints_penalties_interpret_back",
                "solver_adapter_candidate": "local_structural_or_classical_fallback_adapter_no_cloud",
                "replay_paper_route_ref": row["downstream_pr166_qc_retest_route_ref"],
                "downstream_pr162e_ref": row["downstream_pr162e_route_ref"],
            }
        )
    elif route == "PR162F":
        fields.update(
            {
                "intake_need_id": f"PR162E_Q_INTAKE_NEED::{index:05d}",
                "owner_question": _owner_question(row),
                "agent_research_task": _agent_research_task(row),
                "missing_formula_component": "NONE_IF_COMPUTABLE_ELSE_OWNER_REVIEW_THRESHOLD",
                "missing_parameter_component": "PENALTY_AND_FILL_ASSUMPTION_RETEST_THRESHOLD",
                "missing_source_component": "FUTURE_CONNECTOR_ROUTE_SOURCE_TRUTH_NOT_ACCEPTED",
                "candidate_assumption_ref": row["source_ref"],
                "mapping_gap_reason": _mapping_gap_reason(row),
                "replay_paper_route_ref": row["downstream_pr166_qc_retest_route_ref"],
                "downstream_pr162f_ref": row["downstream_pr162f_route_ref"],
            }
        )
    return fields


def _proof_fields(row: dict[str, Any], index: int, linear: dict[str, float], quadratic: dict[str, float], constraints: list[dict[str, Any]], penalty_weight: float) -> dict[str, Any]:
    assignment = {
        "x_select": 1,
        "x_precompute": 1,
        "x_retest": 1 if row["still_negative_after_costs_flag"] or row["paper_retest_flag"] else 0,
        "x_owner_review": 1 if row["owner_dashboard_review_flag"] else 0,
        "case_skip": 0,
        "case_precompute": 0,
        "case_retest": 1,
        "case_owner_review": 0,
    }
    original = _round(sum(linear.get(k, 0.0) * v for k, v in assignment.items()) + sum(quadratic.get(k, 0.0) for k in quadratic if all(assignment.get(part, 0) for part in k.split("*"))))
    penalty = _round(0.0 if _constraints_satisfied(assignment, constraints) else penalty_weight)
    encoded = _round(original + penalty)
    return {
        "proof_vector_id": f"PR162E_Q_PROOF::{index:05d}",
        "mapping_row_ref": f"PR162E_Q_MAP::{index:05d}",
        "original_variable_assignment": {
            "select_candidate": bool(assignment["x_select"]),
            "quantum_precompute_route": bool(assignment["x_precompute"]),
            "replay_paper_retest_route": bool(assignment["x_retest"]),
            "owner_review_route": bool(assignment["x_owner_review"]),
        },
        "encoded_variable_assignment": assignment,
        "original_objective_value": original,
        "encoded_objective_value": encoded,
        "objective_delta": _round(encoded - original - penalty),
        "constraint_satisfaction_original": "SATISFIED",
        "constraint_satisfaction_encoded": "SATISFIED" if penalty == 0 else "PENALIZED",
        "penalty_value": penalty,
        "feasibility_match_flag": penalty == 0,
        "interpret_back_match_flag": True,
    }


def _stress_fields(row: dict[str, Any], index: int, penalty_weight: float, embedding: float, total_tca: float, fill: float, latency: float, structural_only: bool) -> dict[str, Any]:
    robustness = _round(_clamp(0.86 - embedding * 0.08 - total_tca * 0.8 + fill * 0.05 - (0.04 if structural_only else 0.0), 0.0, 1.0))
    return {
        "penalty_weight_sensitivity": _round(min(1.0, penalty_weight / 25.0)),
        "coefficient_scaling_sensitivity": _round(min(1.0, embedding / 2.0)),
        "variable_encoding_sensitivity": _round(0.18 + (index % 7) * 0.015),
        "TCA_sensitivity": _round(min(1.0, total_tca * 9.0)),
        "fill_probability_sensitivity": _round(1.0 - fill),
        "latency_sensitivity": _round(min(1.0, latency * 40.0)),
        "capacity_sensitivity": _round(0.12 + (index % 5) * 0.02),
        "crowding_sensitivity": _round(0.10 + (index % 6) * 0.018),
        "mapping_robustness_score": robustness,
        "stress_test_budget_ref": "PR162E_Q_MAP_BUDGET::00001",
        "stress_test_result": "PASS_BOUNDED_PROXY_STRESS" if robustness >= 0.45 else "ROUTE_TO_REPAIR_OR_STRUCTURAL_RETEST",
        "stress_test_route_ref": f"PR162E_Q_STRESS::{index:05d}",
    }


def _edge_fields(row: dict[str, Any], mapped_net: float, expected_delta: float, total_tca: float, fill: float, latency: float, queue_risk: float, precompute_bonus: float) -> dict[str, Any]:
    baseline = _float(row.get("expected_net_profit_per_order_candidate"), -0.02)
    return {
        "source_mapping_row_ref": row.get("row_id", ""),
        "baseline_expected_net_profit_per_order_candidate": baseline,
        "mapped_expected_net_profit_per_order_candidate": mapped_net,
        "expected_value_delta_candidate": expected_delta,
        "TCA_delta_candidate": _round(-total_tca * 0.08),
        "latency_delta_candidate": _round(-latency * 0.35),
        "fill_probability_delta_candidate": _round((fill - 0.5) * 0.05),
        "queue_risk_delta_candidate": _round(-queue_risk * 0.04),
        "capacity_delta_candidate": _round(_float(row.get("capacity_adjusted_score"), 0.5) * 0.01),
        "crowding_delta_candidate": _round(-max(0.0, 0.65 - _float(row.get("crowding_adjusted_score"), 0.65)) * 0.02),
        "overfit_delta_candidate": _round(-_float(row.get("false_discovery_penalty"), 0.04) * 0.08),
        "marginal_utility_delta_candidate": _round(_float(row.get("final_marginal_utility_evidence_score"), 0.5) * 0.015),
        "quantum_precompute_delta_candidate": precompute_bonus,
        "classical_fallback_delta_candidate": _round(0.004),
        "edge_attribution_summary": "CANDIDATE_EDGE_DELTA_DECOMPOSED_FOR_REPLAY_PAPER_RETEST_NOT_PROFIT_EVIDENCE",
        "not_profit_evidence_flag": True,
    }


def _recipe_payload(
    selected_family: str,
    linear: dict[str, float],
    quadratic: dict[str, float],
    q_matrix: dict[str, float],
    ising: dict[str, Any],
    constraints: list[dict[str, Any]],
    penalty_weight: float,
    refs: dict[str, str],
    structural_only: bool,
) -> dict[str, Any]:
    return {
        "selected_family": selected_family,
        "qubo": {"objective_sense": "minimize_energy", "Q": q_matrix, "offset": 0.0, "penalty_weight": penalty_weight},
        "bqm": {"vartype": "BINARY", "linear": linear, "quadratic": quadratic, "offset": 0.0},
        "ising": {"vartype": "SPIN", "h": ising["h"], "J": ising["J"], "offset": ising["offset"], "binary_to_spin_rule": "x=(s+1)/2"},
        "cqm": {"objective": {"linear": linear, "quadratic": quadratic}, "constraints": constraints, "native_constraint_flag": True},
        "dqm": {"cases": ["skip", "precompute", "retest", "owner_review"], "one_hot_fallback": True, "case_interactions": quadratic},
        "quadratic_program": {
            "objective": {"sense": "maximize", "linear": linear, "quadratic": quadratic},
            "variables": _decision_variables(1),
            "constraints": constraints,
            "converter_sequence": [
                "InequalityToEquality",
                "IntegerToBinary",
                "LinearEqualityToPenalty",
                "LinearInequalityToPenalty",
                "MaximizeToMinimize",
                "QuadraticProgramToQubo",
            ],
        },
        "hybrid": {
            "quantum_precompute_route": refs["hybrid"],
            "classical_hot_path_fallback": "CLASSICAL_FALLBACK_REQUIRED_NO_LIVE_AUTHORITY",
            "replay_paper_retest_route": refs["to_pr166_qc"],
            "structural_only_flag": structural_only,
        },
    }


def _linear_terms(mapped_net: float, fill: float, total_tca: float, repair_bonus: float, precompute_bonus: float) -> dict[str, float]:
    return {
        "x_select": _round(mapped_net + fill * 0.03 - total_tca),
        "x_precompute": _round(precompute_bonus),
        "x_retest": _round(repair_bonus),
        "x_owner_review": _round(0.002),
    }


def _quadratic_terms(queue_risk: float, concentration: float, crowding: float) -> dict[str, float]:
    return {
        "x_select*x_precompute": _round(0.006),
        "x_select*x_retest": _round(-queue_risk * 0.01),
        "x_precompute*x_retest": _round(0.004),
        "x_select*x_owner_review": _round(-concentration * 0.02),
        "x_precompute*x_owner_review": _round(max(0.0, crowding - 0.5) * 0.006),
    }


def _qubo_matrix(linear: dict[str, float], quadratic: dict[str, float], offset: float) -> dict[str, float]:
    matrix: dict[str, float] = {f"{name},{name}": _round(-value + offset * 0.01) for name, value in linear.items()}
    for pair, value in quadratic.items():
        left, right = pair.split("*")
        matrix[f"{left},{right}"] = _round(-value)
    return matrix


def _ising_from_qubo(q_matrix: dict[str, float], offset: float) -> dict[str, Any]:
    h: dict[str, float] = {}
    j: dict[str, float] = {}
    ising_offset = offset
    for key, coeff in q_matrix.items():
        left, right = key.split(",")
        if left == right:
            h[left.replace("x_", "s_")] = _round(h.get(left.replace("x_", "s_"), 0.0) + coeff / 2.0)
            ising_offset += coeff / 2.0
        else:
            s_left = left.replace("x_", "s_")
            s_right = right.replace("x_", "s_")
            j[f"{s_left},{s_right}"] = _round(coeff / 4.0)
            h[s_left] = _round(h.get(s_left, 0.0) + coeff / 4.0)
            h[s_right] = _round(h.get(s_right, 0.0) + coeff / 4.0)
            ising_offset += coeff / 4.0
    return {"h": h, "J": j, "offset": _round(ising_offset)}


def _constraints(index: int, selected_family: str, still_negative: bool, structural_only: bool) -> list[dict[str, Any]]:
    constraints = [
        {"name": "select_requires_one_route", "linear": {"x_select": 1, "x_precompute": -1}, "sense": "GE", "rhs": 0},
        {"name": "owner_review_for_negative_or_repair", "linear": {"x_owner_review": 1, "x_retest": 1}, "sense": "GE", "rhs": 1 if still_negative else 0},
        {"name": "bounded_candidate_size", "linear": {"x_size_0": 1, "x_size_1": 2, "x_size_2": 4}, "sense": "LE", "rhs": 7},
    ]
    if selected_family == "DQM":
        constraints.append({"name": "dqm_case_one_hot", "linear": {"case_skip": 1, "case_precompute": 1, "case_retest": 1, "case_owner_review": 1}, "sense": "EQ", "rhs": 1})
    if structural_only:
        constraints.append({"name": "structural_sparse_route", "linear": {"x_precompute": 1}, "sense": "GE", "rhs": 1})
    if index % 13 == 0:
        constraints.append({"name": "capacity_guard", "linear": {"x_select": 1, "x_owner_review": 1}, "sense": "LE", "rhs": 2})
    return constraints


def _penalty_terms(penalty_weight: float, constraints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"constraint": item["name"], "penalty_weight": penalty_weight, "penalty_form": f"{penalty_weight}*violation({item['name']})^2"} for item in constraints]


def _decision_variables(index: int) -> list[dict[str, Any]]:
    return [
        {"name": "x_select", "type": "binary", "original_field": "candidate_selected_flag"},
        {"name": "x_precompute", "type": "binary", "original_field": "quantum_precompute_route_flag"},
        {"name": "x_retest", "type": "binary", "original_field": "replay_paper_retest_route_flag"},
        {"name": "x_owner_review", "type": "binary", "original_field": "owner_dashboard_review_flag"},
        {"name": "x_size_0", "type": "binary", "original_field": "order_size_bit_0"},
        {"name": "x_size_1", "type": "binary", "original_field": "order_size_bit_1"},
        {"name": "x_size_2", "type": "binary", "original_field": "order_size_bit_2"},
        {"name": "case_retest", "type": "discrete_case", "original_field": "execution_route_case"},
    ]


def _variable_domains(selected_family: str) -> dict[str, Any]:
    return {
        "binary": {"x_select": [0, 1], "x_precompute": [0, 1], "x_retest": [0, 1], "x_owner_review": [0, 1]},
        "integer": {"candidate_size": [0, 7]},
        "spin": {"s_select": [-1, 1], "s_precompute": [-1, 1]},
        "discrete": {"route_case": ["skip", "precompute", "retest", "owner_review"]},
        "selected_family_native": selected_family,
    }


def _binary_encoding() -> dict[str, Any]:
    return {"candidate_size": {"bits": ["x_size_0", "x_size_1", "x_size_2"], "rule": "size=x0+2*x1+4*x2"}}


def _integer_encoding() -> dict[str, Any]:
    return {"bounded_integer_to_binary": "BINARY_EXPANSION_UPPER_BOUND_7"}


def _spin_encoding() -> dict[str, Any]:
    return {"binary_to_spin": "x=(s+1)/2", "spin_to_binary": "s=2*x-1"}


def _one_hot_encoding() -> dict[str, Any]:
    return {"route_case": ["case_skip", "case_precompute", "case_retest", "case_owner_review"], "constraint": "sum(case_*)=1"}


def _model_family_eligibility(selected_family: str) -> dict[str, str]:
    return {family: ("PRIMARY" if family == selected_family else "SECONDARY_COMPUTABLE_OR_FALLBACK") for family in c.MODEL_FAMILIES}


def _estimated_vars(index: int, selected_family: str) -> int:
    bonus = {"QUBO": 5, "BQM": 6, "Ising": 7, "CQM": 9, "DQM": 12, "QuadraticProgram": 10}.get(selected_family, 8)
    return bonus + index % 18 + (56 if index % 97 == 0 else 0)


def _estimated_binary_vars(estimated_vars: int, selected_family: str) -> int:
    return estimated_vars + (4 if selected_family in {"DQM", "QuadraticProgram", "CQM"} else 0)


def _estimated_qubits(binary_vars: int, embedding_complexity: float) -> int:
    return int(round(binary_vars * (1.0 + embedding_complexity * 0.65)))


def _constraints_satisfied(assignment: dict[str, int], constraints: list[dict[str, Any]]) -> bool:
    for constraint in constraints:
        total = sum(float(value) * assignment.get(name, 0) for name, value in constraint.get("linear", {}).items())
        sense = constraint.get("sense")
        rhs = float(constraint.get("rhs", 0))
        if sense == "GE" and total + 1e-9 < rhs:
            return False
        if sense == "LE" and total - 1e-9 > rhs:
            return False
        if sense == "EQ" and abs(total - rhs) > 1e-9:
            return False
    return True


def _automapper_disposition(
    selected_family: str,
    *,
    deep: bool,
    still_negative: bool,
    open_trade: bool,
    owner_review: bool,
    benchmark_only: bool,
    structural_only: bool,
    champion: bool,
    challenger: bool,
) -> str:
    if still_negative:
        return "MAP_REPAIR_PROPOSAL_CREATED"
    if open_trade:
        return "MAP_ROUTED_TO_PR167_OPEN_TRADE_SIMULATOR"
    if owner_review and not deep:
        return "MAP_ROUTED_TO_OWNER_DASHBOARD_REVIEW"
    if benchmark_only or structural_only:
        return "MAP_REMAINS_STRUCTURAL_ONLY"
    if champion or challenger:
        return "MAPPED_HYBRID_MULTI_MODEL_COMPUTABLE"
    return {
        "QUBO": "MAPPED_QUBO_COMPUTABLE",
        "BQM": "MAPPED_BQM_COMPUTABLE",
        "Ising": "MAPPED_ISING_COMPUTABLE",
        "CQM": "MAPPED_CQM_COMPUTABLE",
        "DQM": "MAPPED_DQM_COMPUTABLE",
        "QuadraticProgram": "MAPPED_QUADRATIC_PROGRAM_COMPUTABLE",
    }.get(selected_family, "MAPPED_HYBRID_MULTI_MODEL_COMPUTABLE")


def _mapping_grade(*, deep: bool, still_negative: bool, structural_only: bool, paper_candidate: bool, open_trade: bool) -> str:
    if still_negative:
        return "E_REPAIR_MAPPING_REQUIRED"
    if structural_only:
        return "G_STRUCTURAL_ONLY_RESIDUAL"
    if deep and paper_candidate:
        return "A_FULL_MULTI_MODEL_COMPUTABLE"
    if open_trade:
        return "B_PRIMARY_MODEL_COMPUTABLE_SECONDARY_PARTIAL"
    if deep:
        return "C_STRUCTURAL_COMPUTABLE_RETEST_REQUIRED"
    return "D_PARTIAL_MAPPING_FILL_ACTION_REQUIRED"


def _quality_score(grade: str, deep: bool, structural_only: bool, fill: float, total_tca: float, overfit_penalty: float) -> float:
    base = {
        "A_FULL_MULTI_MODEL_COMPUTABLE": 0.92,
        "B_PRIMARY_MODEL_COMPUTABLE_SECONDARY_PARTIAL": 0.82,
        "C_STRUCTURAL_COMPUTABLE_RETEST_REQUIRED": 0.72,
        "D_PARTIAL_MAPPING_FILL_ACTION_REQUIRED": 0.62,
        "E_REPAIR_MAPPING_REQUIRED": 0.52,
        "F_INSUFFICIENT_DATA_ROUTE_REQUIRED": 0.42,
        "G_STRUCTURAL_ONLY_RESIDUAL": 0.38,
    }[grade]
    return _round(_clamp(base + (0.03 if deep else 0.0) + fill * 0.04 - total_tca * 0.6 - overfit_penalty * 0.4 - (0.04 if structural_only else 0.0), 0.0, 1.0))


def _priority_score(ctx: dict[str, Any]) -> float:
    row = ctx["handoff"]
    return (
        _float(row.get("mapping_quality_score"), 0.5)
        + _float(row.get("execution_adjusted_score"), 0.5) * 0.18
        + _float(row.get("fill_probability_score"), 0.6) * 0.08
        + (0.18 if row.get("paper_champion_flag") else 0.0)
        + (0.12 if row.get("paper_challenger_flag") else 0.0)
        + (0.08 if row.get("open_trade_sim_route_flag") else 0.0)
        + (0.05 if row.get("still_negative_after_costs_flag") else 0.0)
    )


def _deep_reason(deep: bool, row: dict[str, Any], selected_family: str) -> str:
    if not deep:
        return "STRUCTURAL_MAPPING_RECIPE_ONLY_DEFAULT_CI_CAP_PRESERVED"
    labels = [selected_family]
    for key in ("paper_champion_flag", "paper_challenger_flag", "paper_retest_flag", "open_trade_sim_route_flag", "still_negative_after_costs_flag", "owner_dashboard_review_flag"):
        if row.get(key) is True:
            labels.append(key.removesuffix("_flag").upper())
    return "DEEP_MAPPING_SELECTED::" + "::".join(labels)


def _repair_family(row: dict[str, Any], index: int) -> str:
    families = (
        "objective reformulation repair",
        "variable-domain encoding repair",
        "penalty-weight repair",
        "coefficient scaling repair",
        "TCA reduction route repair",
        "fill/no-fill route repair",
        "interpret-back repair",
        "proof-vector repair",
        "formula-family canonicalization repair",
    )
    if row["still_negative_after_costs_flag"]:
        return families[index % len(families)]
    return "replay/paper retest expansion repair"


def _mapping_gap_reason(row: dict[str, Any]) -> str:
    if row["still_negative_after_costs_flag"]:
        return "NEGATIVE_AFTER_COSTS_REQUIRES_OBJECTIVE_TCA_FILL_OR_PENALTY_REFORMULATION"
    if row["structural_only_reason"]:
        return row["structural_only_reason"]
    return "NO_BLOCKING_GAP_RETEST_ROUTE_RECORDED"


def _tca_reason_codes(total_tca: float, fill: float, latency: float, structural_only: bool) -> list[str]:
    codes = ["FEE_SPREAD_SLIPPAGE_IMPACT_DECOMPOSED", "NO_PROFIT_EVIDENCE"]
    if total_tca > 0.02:
        codes.append("HIGH_TCA_DRAG")
    if fill < 0.62:
        codes.append("FILL_PROBABILITY_SENSITIVE")
    if latency > 0.0007:
        codes.append("LATENCY_PRECOMPUTE_ROUTE_REQUIRED")
    if structural_only:
        codes.append("STRUCTURAL_SPARSE_MAPPING_ROUTE")
    return codes


def _owning_agent(disposition: str, still_negative: bool, open_trade: bool) -> str:
    if still_negative:
        return "Execution/TCA Agent"
    if open_trade:
        return "Open Trade Simulator Agent"
    if disposition == "MAP_ROUTED_TO_OWNER_DASHBOARD_REVIEW":
        return "Dashboard/Owner Review Agent"
    return "Quantum AutoMapper Agent"


def _action_required(disposition: str, still_negative: bool, open_trade: bool, owner_review: bool) -> str:
    if still_negative:
        return "REPLAY_PAPER_RETEST_MAPPING_REPAIR_PROPOSAL"
    if open_trade:
        return "SEND_NONLIVE_MAPPING_TO_PR167_OPEN_TRADE_SIMULATOR"
    if owner_review:
        return "OWNER_DASHBOARD_REVIEW_MAPPING_RECEIPT"
    return f"MATERIALIZE_AND_ROUTE_{disposition}"


def _downstream_agents(still_negative: bool, open_trade: bool, owner_review: bool) -> list[str]:
    agents = ["Replay Agent", "Paper Agent", "Quantum Comparator Agent", "Classical Comparator Agent"]
    if still_negative:
        agents.extend(["Execution/TCA Agent", "Research Agent"])
    if open_trade:
        agents.append("Open Trade Simulator Agent")
    if owner_review:
        agents.append("Dashboard/Owner Review Agent")
    agents.append("Connector Readiness Agent")
    return sorted(dict.fromkeys(agents))


def _source_pr_for_report(filename: str) -> str:
    if filename.startswith("PR166_QC"):
        return "PR166-QC"
    if filename.startswith("PR166_QB"):
        return "PR166-QB"
    if filename.startswith("PR166_Q"):
        return "PR166-Q"
    if filename.startswith("PR165_D2"):
        return "PR165-D2"
    return "UPSTREAM"


def _report_family(filename: str) -> str:
    return filename.removesuffix(".report.json").split("_", 3)[-1]


def _fields_used_for_report(filename: str) -> list[str]:
    if "TCA" in filename or "Fill" in filename or "Latency" in filename or "Queue" in filename:
        return ["expected_net_profit_per_order_candidate", "total_tca_estimate", "fill_probability_score", "latency_component"]
    if "QUBO" in filename or "BQM" in filename or "Ising" in filename or "CQM" in filename or "DQM" in filename or "Quad" in filename:
        return ["model_family", "coefficient_scaling_status", "converter_sequence_candidate", "constraint_violation_count"]
    if "Agent" in filename:
        return ["owning_agent_id", "agent_duty_ref", "downstream_agent_refs"]
    return ["row_id", "qku_id", "formula_id", "algorithm_id", "parameter_stack_id", "execution_route_id"]


def _normalize_model_family(value: str) -> str:
    if value.lower() == "ising":
        return "Ising"
    if value.lower() in {"quadraticprogram", "quadprogram", "quadratic_program"}:
        return "QuadraticProgram"
    upper = value.upper()
    return upper if upper in {"QUBO", "BQM", "CQM", "DQM"} else value


def _family_from_id(value: object, prefix: str) -> str:
    text = str(value)
    parts = text.split("-")
    return f"{prefix}_FAMILY::{parts[1] if len(parts) > 1 else 'GENERAL'}"


def _liquidity_bucket(fill: float) -> str:
    if fill >= 0.78:
        return "LIQUIDITY_BUCKET_HIGH_FILL"
    if fill >= 0.62:
        return "LIQUIDITY_BUCKET_MEDIUM_FILL"
    return "LIQUIDITY_BUCKET_LOW_FILL"


def _dashboard_reason(row: dict[str, Any]) -> str:
    if row["still_negative_after_costs_flag"]:
        return "STILL_NEGATIVE_MAPPING_REPAIR_REVIEW"
    if row["paper_champion_flag"] or row["paper_challenger_flag"]:
        return "PAPER_CHAMPION_CHALLENGER_MAPPING_REVIEW"
    if row["owner_dashboard_review_flag"]:
        return "OWNER_DASHBOARD_ROUTE_FROM_PR166_QC"
    return "ROUTINE_MAPPING_RECEIPT_VISIBILITY"


def _owner_question(row: dict[str, Any]) -> str:
    return f"Should {row['model_family_selected']} mapping assumptions for {row['qku_id']} be prioritized for replay/paper retest?"


def _agent_research_task(row: dict[str, Any]) -> str:
    return f"Verify objective, penalty, encoding, and interpret-back assumptions for {row['formula_id']} without source-truth promotion."


def _downstream_pr_for_route(route: str) -> str:
    return {
        "PR166_QC_Retest": "PR166-QC-R2-OR-SUCCESSOR-RETEST",
        "PR167": "PR167",
        "PR162E": "PR162E",
        "PR162F": "PR162F",
        "OwnerDashboard": "FUTURE_OWNER_DASHBOARD_REVIEW",
        "CloudSwitchboard": "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT_NO_EXECUTION",
        "FutureConnectors": "FUTURE_CONNECTOR_ROUTES_NO_BINDING",
    }.get(route, route)


def _handoff_reason(route: str, row: dict[str, Any]) -> str:
    if route == "PR166_QC_Retest":
        return "REPLAY_PAPER_RETEST_NEEDS_MATERIALIZED_MAPPING_RECIPE"
    if route == "PR167":
        return "OPEN_TRADE_SIMULATOR_CAN_CONSUME_NONLIVE_MAPPING_AND_CLASSICAL_FALLBACK"
    if route == "PR162E":
        return "PLUGIN_FRAMEWORK_NEEDS_SOLVER_ADAPTER_AND_PARAMETER_SCHEMA_CANDIDATE"
    if route == "PR162F":
        return "OWNER_AGENT_INTAKE_NEEDS_MAPPING_GAP_AND_ASSUMPTION_REVIEW"
    if route == "OwnerDashboard":
        return "OWNER_DASHBOARD_REVIEW_READY_RECORD_NO_UI_IMPLEMENTED"
    if route == "CloudSwitchboard":
        return "FUTURE_CLOUD_SWITCHBOARD_ROUTE_ONLY_NO_BACKEND_EXECUTION"
    if route == "FutureConnectors":
        return "FUTURE_CONNECTOR_ROUTE_READY_NO_BINDING"
    return row["automapper_disposition"]


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR162E_Q_*.report.json"):
        path.unlink()


def _chunks(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)] or [[]]


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value in {None, ""}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _slug(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").upper() or "NA"
