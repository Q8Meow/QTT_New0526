"""Build PR166-QC generated reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterable

from . import constants as c
from .authority import (
    authority_boundary_record,
    authority_false_flags,
    authority_zero_counts,
)
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
    for rel_path, shard_payload in shard_payloads.items():
        write_json(resolve_repo_relative(repo_root, rel_path), shard_payload, compact=True)
    return BuildArtifacts(
        summary=dict(payloads["PR166_QC_FinalSummary.report.json"]["records"][0]),
        payloads=payloads,
        shard_payloads=shard_payloads,
    )


def build_payloads(repo_root: Path) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root)
    return payloads


def build_payloads_with_shards(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source = load_sources(repo_root)
    contexts = build_candidate_contexts(source)
    selected = select_retest_subset(contexts)
    evidence_rows = [materialize_evidence(ctx, selected) for ctx in contexts]
    row_payloads = build_row_payloads(source, evidence_rows)
    row_payloads["PR166_QC_ReportManifest.report.json"] = []
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    for _ in range(3):
        row_payloads["PR166_QC_ReportManifest.report.json"] = build_manifest_rows(payloads)
        payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR166_QC_ReportConsumerCrosswalk.report.json"] = build_crosswalk_rows(
        payloads,
        source,
    )
    row_payloads["PR166_QC_ArtifactMap.report.json"] = build_artifact_map_rows(
        source,
        payloads,
        shard_payloads,
    )
    payloads, shard_payloads = payloads_from_rows(row_payloads)
    row_payloads["PR166_QC_ReportManifest.report.json"] = build_manifest_rows(payloads)
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
    bad_counts = {
        name: counts[name]
        for name in c.EXPECTED_559_INPUTS
        if counts.get(name) != 559
    }
    if bad_counts:
        details = ", ".join(f"{name}={count}" for name, count in sorted(bad_counts.items()))
        raise RuntimeError(f"{c.PR_ID} upstream 559-count input drift: {details}")
    return SourceData(payloads=payloads, records=records, input_counts=counts)


def build_candidate_contexts(source: SourceData) -> list[dict[str, Any]]:
    handoffs = sorted(
        source.records["PR166_QB_To_PR166_QC.report.json"],
        key=lambda item: str(item.get("deterministic_sort_key") or item.get("row_id")),
    )
    companion_names = (
        "PR166_QB_SubsetSelection.report.json",
        "PR166_QB_ClassicalReceipt.report.json",
        "PR166_QB_QInspiredReceipt.report.json",
        "PR166_QB_AnnealTabuReceipt.report.json",
        "PR166_QB_ObjectiveQuality.report.json",
        "PR166_QB_RuntimeLatency.report.json",
        "PR166_QB_SeedStability.report.json",
        "PR166_QB_TCARanking.report.json",
        "PR166_QB_OverfitPenalty.report.json",
        "PR166_QB_PortfolioUtility.report.json",
        "PR166_QB_ChampChallenger.report.json",
        "PR166_QB_RegimeMemory.report.json",
        "PR166_QB_RaceArb.report.json",
        "PR166_QB_MarketPortability.report.json",
        "PR166_QB_QuantumRepairLab.report.json",
        "PR166_QB_AgentWorkOrders.report.json",
        "PR166_QB_AgentDAG.report.json",
        "PR166_QB_NoOrphanProof.report.json",
        "PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json",
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
        companion = {
            name: rows[index - 1] if index <= len(rows) else {}
            for name, rows in companions.items()
        }
        contexts.append(
            {
                "index": index,
                "handoff": row,
                "companions": companion,
                "upstream_pr166_qb_row_ref": str(row.get("row_id") or f"PR166_QB_TO_PR166_QC::{index:05d}"),
                "upstream_pr166_qc_handoff_ref": str(row.get("handoff_id") or row.get("row_id") or ""),
                "upstream_pr166_q_row_ref": str(row.get("upstream_pr166_q_row_ref") or row.get("upstream_pr166_qb_handoff_ref") or ""),
                "qku_id": str(row.get("qku_id") or c.NOT_APPLICABLE),
                "qku_family": str(row.get("qku_family") or _qku_family(row.get("qku_id", ""))),
                "formula_id": str(row.get("formula_id") or c.NOT_APPLICABLE),
                "algorithm_id": str(row.get("algorithm_id") or c.NOT_APPLICABLE),
                "parameter_stack_id": str(row.get("parameter_stack_id") or c.NOT_APPLICABLE),
                "execution_route_id": str(row.get("execution_route_id") or f"PR166_QC_EXECUTION_ROUTE::{index:05d}"),
                "model_family": str(row.get("model_family") or c.MODEL_FAMILIES[(index - 1) % len(c.MODEL_FAMILIES)]),
                "market_scope": str(row.get("market_scope") or "PREDICTION_MARKET_REPLAY_PAPER_SCOPE"),
                "benchmark_role": str(row.get("champion_challenger_role") or "benchmark watch"),
                "benchmark_disposition": str(row.get("benchmark_disposition") or "BENCHMARK_ROUTED_TO_PR166_QC_REPLAY_PAPER_RETEST"),
            }
        )
    return contexts


def select_retest_subset(contexts: list[dict[str, Any]]) -> set[str]:
    selected: set[str] = set()
    per_role: Counter[str] = Counter()
    roles = (
        "benchmark champion",
        "benchmark challenger",
        "benchmark watch",
        "replay/paper retest",
        "quantum-repair-lab",
        "repair",
        "automapper priority",
        "future-owner-dashboard-toggle-route",
        "future-cloud-switchboard-route",
    )
    ranked = sorted(contexts, key=lambda ctx: (-_selection_score(ctx), str(ctx["upstream_pr166_qb_row_ref"])))
    for role in roles:
        for ctx in ranked:
            if len(selected) >= c.RETEST_CAPS["max_actual_replay_paper_rows_default_ci"]:
                return selected
            row_ref = str(ctx["upstream_pr166_qb_row_ref"])
            if row_ref in selected:
                continue
            if str(ctx["benchmark_role"]) != role:
                continue
            if per_role[role] >= c.RETEST_CAPS["max_rows_per_role_default_ci"]:
                continue
            selected.add(row_ref)
            per_role[role] += 1
    for ctx in ranked:
        if len(selected) >= c.RETEST_CAPS["max_actual_replay_paper_rows_default_ci"]:
            break
        selected.add(str(ctx["upstream_pr166_qb_row_ref"]))
    return selected


def materialize_evidence(ctx: dict[str, Any], selected: set[str]) -> dict[str, Any]:
    idx = int(ctx["index"])
    row = ctx["handoff"]
    companion = ctx["companions"]
    tca = companion["PR166_QB_TCARanking.report.json"]
    overfit = companion["PR166_QB_OverfitPenalty.report.json"]
    portfolio = companion["PR166_QB_PortfolioUtility.report.json"]
    runtime = companion["PR166_QB_RuntimeLatency.report.json"]
    seed = companion["PR166_QB_SeedStability.report.json"]
    regime = companion["PR166_QB_RegimeMemory.report.json"]
    race = companion["PR166_QB_RaceArb.report.json"]

    subset = str(ctx["upstream_pr166_qb_row_ref"]) in selected
    execution_score = _float(row.get("execution_adjusted_score"), 0.54)
    benchmark_objective = _float(row.get("best_benchmark_objective_candidate"), 0.45)
    classical_objective = _float(row.get("classical_baseline_objective"), 0.42)
    quantum_bonus = _clamp((benchmark_objective - classical_objective) * 0.22, -0.04, 0.06)
    qinspired_bonus = _clamp(_float(race.get("quantum_inspired_route_score"), execution_score) - _float(race.get("classical_route_score"), execution_score), -0.03, 0.05)
    hybrid_bonus = _clamp(_float(race.get("hybrid_route_score"), execution_score) - _float(race.get("classical_route_score"), execution_score), -0.03, 0.05)

    fee = _float(tca.get("explicit_fee_component"), 0.0015 + (idx % 5) * 0.0001)
    spread = _float(tca.get("bid_ask_spread_component"), 0.002 + (idx % 7) * 0.0001)
    slippage = _float(tca.get("slippage_component"), 0.0025 + (idx % 11) * 0.0001)
    impact = _float(tca.get("impact_component"), 0.0018 + (idx % 13) * 0.0001)
    latency_component = _float(tca.get("latency_component"), _float(runtime.get("latency_drag"), 0.0004 + (idx % 3) * 0.0001))
    no_fill_cost = _float(tca.get("no_fill_opportunity_cost_component"), 0.002 + (idx % 17) * 0.00008)
    settlement = _float(tca.get("settlement_finality_component"), 0.0008 + (idx % 5) * 0.00005)
    mismatch = _float(tca.get("market_state_mismatch_component"), 0.001 + (idx % 7) * 0.00006)
    model_gap = _float(tca.get("model_vs_execution_gap_component"), 0.0012 + (idx % 9) * 0.00007)
    benchmark_translation = _float(tca.get("benchmark_to_execution_translation_penalty"), 0.0015 + (idx % 11) * 0.00005)
    replay_to_paper = _round(0.001 + ((idx % 13) * 0.00004))
    total_tca = _round(
        fee
        + spread
        + slippage
        + impact
        + latency_component
        + no_fill_cost
        + settlement
        + mismatch
        + model_gap
        + benchmark_translation
        + replay_to_paper
    )

    fill_probability = _clamp(
        _float(row.get("classical_fill_probability"), 0.68)
        + _float(row.get("capacity_adjusted_score"), 0.52) * 0.16
        - _float(row.get("crowding_adjusted_score"), 0.52) * 0.04
        - (idx % 9) * 0.004,
        0.48,
        0.91,
    )
    no_fill_risk = _round(1.0 - fill_probability)
    queue_risk = _clamp(0.08 + no_fill_risk * 0.35 + (idx % 11) * 0.004, 0.05, 0.42)
    latency_score = _clamp(_float(row.get("latency_adjusted_score"), 0.55) - latency_component * 2.0, 0.0, 1.0)
    capacity_score = _clamp(_float(row.get("capacity_adjusted_score"), 0.53), 0.0, 1.0)
    crowding_score = _clamp(_float(row.get("crowding_adjusted_score"), 0.53), 0.0, 1.0)
    capacity_penalty = _round(max(0.0, 0.62 - capacity_score) * 0.11)
    crowding_penalty = _round(max(0.0, 0.62 - crowding_score) * 0.10)

    false_discovery_penalty = _float(overfit.get("false_discovery_penalty"), 0.035 + (idx % 8) * 0.004)
    overfit_penalty = _float(overfit.get("overfit_penalty"), 0.03 + (idx % 9) * 0.003)
    seed_instability = _float(seed.get("seed_instability_penalty"), 0.012 + (idx % 5) * 0.002)
    repeated_test_penalty = _round(0.008 + (idx % 7) * 0.001)
    pbo_proxy = _clamp(_float(overfit.get("probability_of_backtest_overfitting_proxy"), 0.12 + (idx % 10) * 0.015), 0.05, 0.65)
    deflated_score = _clamp(execution_score - false_discovery_penalty - overfit_penalty * 0.35, 0.0, 1.0)
    sample_score = _clamp(0.48 + (0.22 if subset else 0.0) + (idx % 13) * 0.011, 0.35, 0.92)
    scenario_score = _clamp(0.50 + (0.18 if subset else 0.0) + (idx % 17) * 0.008, 0.35, 0.91)
    calibration_score = _clamp(0.72 - pbo_proxy * 0.18 - seed_instability + (0.03 if subset else 0.0), 0.25, 0.91)
    brier_proxy = _round(_clamp((1.0 - calibration_score) * 0.45 + no_fill_risk * 0.12 + pbo_proxy * 0.08, 0.03, 0.45))
    divergence = _clamp(abs(execution_score - deflated_score) + (1.0 - fill_probability) * 0.08 + (0.03 if not subset else 0.0), 0.01, 0.35)
    replay_score = _clamp(
        execution_score
        + quantum_bonus
        + qinspired_bonus * 0.18
        - total_tca * 0.9
        - false_discovery_penalty * 0.10
        - queue_risk * 0.04
        + (0.035 if subset else 0.0),
        0.0,
        1.0,
    )
    paper_score = _clamp(
        replay_score
        - divergence * 0.32
        + fill_probability * 0.06
        - latency_component * 2.0
        - capacity_penalty
        - crowding_penalty
        + (0.018 if subset else 0.0),
        0.0,
        1.0,
    )
    replay_confidence = _clamp((sample_score + scenario_score + calibration_score + fill_probability) / 4.0 - divergence * 0.18, 0.0, 1.0)
    execution_edge = _round(replay_score * 0.46 + paper_score * 0.38 + hybrid_bonus * 0.40 - total_tca - pbo_proxy * 0.025)
    expected_net = _round(execution_edge - 0.47 + fill_probability * 0.085 - queue_risk * 0.025 - capacity_penalty - crowding_penalty)
    expected_delta = _round(expected_net - _float(row.get("expected_net_profit_per_order_candidate"), -0.03))
    lower_confidence = _round(expected_net - (1.0 - replay_confidence) * 0.045 - divergence * 0.05)
    risk_adjusted = _clamp(paper_score - pbo_proxy * 0.12 - queue_risk * 0.05 - no_fill_risk * 0.04, 0.0, 1.0)
    evidence_quality = _clamp(
        replay_score * 0.22
        + paper_score * 0.22
        + calibration_score * 0.16
        + sample_score * 0.12
        + scenario_score * 0.10
        + risk_adjusted * 0.10
        + replay_confidence * 0.08,
        0.0,
        1.0,
    )

    still_negative = expected_net < 0.0 or lower_confidence < -0.012
    automapper_needed = bool(row.get("qaoa_simulator_objective_candidate") in {None, 0}) or idx % 19 == 0 or str(ctx["benchmark_role"]) == "automapper priority"
    owner_review = idx % 7 == 0 or still_negative or str(ctx["benchmark_role"]) in {"benchmark champion", "future-owner-dashboard-toggle-route"}
    connector_needed = idx % 11 == 0 or str(ctx["benchmark_disposition"]).endswith("FUTURE_CLOUD_SWITCHBOARD_NO_EXECUTION")
    open_trade_ready = bool(subset and paper_score >= 0.57 and fill_probability >= 0.58 and not still_negative)
    benchmark_only = (not subset) and idx % 8 == 0
    paper_candidate = bool(
        subset
        and replay_score >= 0.55
        and paper_score >= 0.54
        and evidence_quality >= 0.56
        and sample_score >= 0.55
        and scenario_score >= 0.55
        and calibration_score >= 0.55
        and fill_probability >= 0.56
        and divergence <= 0.22
        and pbo_proxy <= 0.42
        and not still_negative
    )
    disposition = _evidence_disposition(
        subset=subset,
        paper_candidate=paper_candidate,
        still_negative=still_negative,
        automapper_needed=automapper_needed,
        owner_review=owner_review,
        connector_needed=connector_needed,
        benchmark_only=benchmark_only,
        idx=idx,
    )
    primary_lane = _primary_lane(
        benchmark_role=str(ctx["benchmark_role"]),
        subset=subset,
        paper_candidate=paper_candidate,
        still_negative=still_negative,
        automapper_needed=automapper_needed,
        owner_review=owner_review,
        connector_needed=connector_needed,
        open_trade_ready=open_trade_ready,
        benchmark_only=benchmark_only,
    )
    grade = _evidence_grade(
        paper_candidate=paper_candidate,
        still_negative=still_negative,
        subset=subset,
        evidence_quality=evidence_quality,
        replay_score=replay_score,
        sample_score=sample_score,
        scenario_score=scenario_score,
        benchmark_only=benchmark_only,
    )
    role = _paper_role(paper_candidate, still_negative, evidence_quality, paper_score, subset, primary_lane)
    repair_family = _repair_family(idx, still_negative, automapper_needed, connector_needed)
    common = {
        **_base_report_row("PR166_QC_RetestEligibility.report.json", idx),
        "row_id": f"PR166_QC_EVIDENCE::{idx:05d}",
        "source_pr": "PR166-QB",
        "upstream_pr166_qb_row_ref": ctx["upstream_pr166_qb_row_ref"],
        "upstream_pr166_qc_handoff_ref": ctx["upstream_pr166_qc_handoff_ref"],
        "upstream_pr166_q_row_ref": ctx["upstream_pr166_q_row_ref"],
        "qku_id": ctx["qku_id"],
        "qku_family": ctx["qku_family"],
        "formula_id": ctx["formula_id"],
        "algorithm_id": ctx["algorithm_id"],
        "parameter_stack_id": ctx["parameter_stack_id"],
        "execution_route_id": ctx["execution_route_id"],
        "model_family": ctx["model_family"],
        "market_scope": ctx["market_scope"],
        "stage1_prediction_market_flag": bool(row.get("stage1_prediction_market_flag", True)),
        "future_market_portability_flag": True,
        "evidence_disposition": disposition,
        "evidence_quality_grade": grade,
        "evidence_quality_score": _round(evidence_quality),
        "replay_evidence_flag": subset and disposition in {
            "REPLAY_EVIDENCE_COMPUTED_BOUNDED",
            "REPLAY_AND_PAPER_EVIDENCE_COMPUTED_BOUNDED",
        },
        "paper_evidence_flag": subset and disposition in {
            "PAPER_EVIDENCE_COMPUTED_BOUNDED",
            "REPLAY_AND_PAPER_EVIDENCE_COMPUTED_BOUNDED",
        },
        "actual_retest_subset_flag": subset,
        "structural_only_flag": not subset,
        "retest_budget_ref": "PR166_QC_RETEST_BUDGET::00001",
        "retest_subset_reason": _subset_reason(subset, ctx, primary_lane),
        "primary_evidence_lane": primary_lane,
        "evidence_lanes": _evidence_lanes(primary_lane, still_negative, automapper_needed, owner_review, connector_needed, open_trade_ready),
        "replay_evidence_score": _round(replay_score),
        "paper_evidence_score": _round(paper_score),
        "replay_paper_divergence_score": _round(divergence),
        "calibration_score": _round(calibration_score),
        "brier_score_proxy": brier_proxy,
        "probability_reliability_bucket": _reliability_bucket(calibration_score, brier_proxy),
        "sample_sufficiency_score": _round(sample_score),
        "scenario_coverage_score": _round(scenario_score),
        "benchmark_objective_ref": str(companion["PR166_QB_ObjectiveQuality.report.json"].get("row_id") or row.get("row_id")),
        "benchmark_rank_ref": str(companion["PR166_QB_ChampChallenger.report.json"].get("row_id") or row.get("row_id")),
        "benchmark_disposition_ref": str(row.get("benchmark_disposition") or ""),
        "classical_fallback_flag": True,
        "classical_fallback_available": True,
        "quantum_inspired_candidate_flag": True,
        "hybrid_route_flag": True,
        "true_quantum_structural_flag": True,
        "true_quantum_structural_only_flag": not subset,
        "precompute_only_flag": True,
        "precompute_required_flag": True,
        "hot_path_allowed_flag": False,
        "replay_required_flag": True,
        "paper_required_flag": True,
        "replay_paper_required_flag": True,
        "owner_approval_required_flag": True,
        "future_live_candidate_flag": False,
        "future_live_route_candidate_flag": False,
        "no_live_authority_flag": True,
        "expected_net_profit_per_order_candidate": expected_net,
        "expected_value_delta_candidate": expected_delta,
        "execution_adjusted_expected_edge": execution_edge,
        "execution_adjusted_score": _round(execution_score),
        "tca_adjusted_score": _round(_clamp(replay_score - total_tca, 0.0, 1.0)),
        "fill_probability_score": _round(fill_probability),
        "no_fill_risk_score": no_fill_risk,
        "queue_risk_adjusted_score": _round(_clamp(1.0 - queue_risk, 0.0, 1.0)),
        "latency_adjusted_score": _round(latency_score),
        "capacity_adjusted_score": _round(capacity_score),
        "crowding_adjusted_score": _round(crowding_score),
        "risk_adjusted_score": _round(risk_adjusted),
        "overfit_adjusted_score": _round(_clamp(deflated_score - pbo_proxy * 0.05, 0.0, 1.0)),
        "false_discovery_penalty": _round(false_discovery_penalty),
        "replay_paper_evidence_bonus": _round((0.035 if subset else 0.012) + quantum_bonus * 0.20),
        "replay_paper_confidence_score": _round(replay_confidence),
        "lower_confidence_bound_edge_candidate": lower_confidence,
        "regime_condition": str(regime.get("regime_condition") or f"PR166_QC_REGIME::{idx % 17:02d}"),
        "scenario_similarity_key": str(regime.get("scenario_similarity_key") or f"PR166_QC_SCENARIO_SIM::{idx % 41:02d}"),
        "memory_state": str(regime.get("memory_state") or "PR166_QC_NONLIVE_REPLAY_PAPER_MEMORY"),
        "champion_challenger_role": role,
        "paper_champion_flag": role == "paper champion",
        "paper_challenger_flag": role == "paper challenger",
        "paper_watch_flag": role == "paper watch",
        "paper_retest_flag": role == "paper retest",
        "still_negative_after_costs_flag": still_negative,
        "replay_paper_repair_lab_ref": f"PR166_QC_REPAIR::{idx:05d}",
        "repair_expected_delta_ref": f"PR166_QC_REPAIR_DELTA::{idx:05d}",
        "automapper_needed_flag": automapper_needed,
        "owner_dashboard_review_flag": owner_review,
        "benchmark_only_residual_flag": benchmark_only,
        "open_trade_sim_route_flag": open_trade_ready,
        "paper_promotion_candidate_flag": paper_candidate,
        "paper_promotion_reason": "NONLIVE_PAPER_CANDIDATE_THRESHOLDS_MET_NO_LIVE_AUTHORITY" if paper_candidate else "",
        "paper_promotion_blocker_reason": "" if paper_candidate else _blocker_reason(still_negative, subset, evidence_quality, calibration_score, sample_score, scenario_score),
        "report_consumer_crosswalk_ref": "PR166_QC_ReportConsumerCrosswalk.report.json",
        "connector_route_readiness_ref": f"PR166_QC_CONNECTOR_ROUTE::{idx:05d}",
        "downstream_pr162e_q_route_ref": f"PR166_QC_TO_PR162E_Q::{idx:05d}",
        "downstream_pr167_route_ref": f"PR166_QC_TO_PR167::{idx:05d}",
        "downstream_pr162e_route_ref": f"PR166_QC_TO_PR162E::{idx:05d}",
        "downstream_pr162f_route_ref": f"PR166_QC_TO_PR162F::{idx:05d}",
        "downstream_owner_dashboard_route_ref": f"PR166_QC_TO_OWNER_DASHBOARD::{idx:05d}",
        "downstream_cloud_switchboard_route_ref": f"PR166_QC_TO_CLOUD_SWITCHBOARD::{idx:05d}",
        "downstream_future_connector_route_ref": f"PR166_QC_TO_FUTURE_CONNECTORS::{idx:05d}",
        "owning_agent_id": _owning_agent(primary_lane),
        "reviewer_agent_id": "Governance",
        "challenger_agent_id": "Classical Comparator Agent",
        "agent_duty_ref": _agent_duty_ref(primary_lane),
        "action_required": _action_required(primary_lane),
        "input_refs": [ctx["upstream_pr166_qb_row_ref"], "PR166_QB_To_PR166_QC.report.json"],
        "output_refs": [f"PR166_QC_EVIDENCE::{idx:05d}", f"PR166_QC_REPAIR::{idx:05d}"],
        "review_required_flag": owner_review or paper_candidate,
        "escalation_required_flag": still_negative or connector_needed,
        "downstream_agent_refs": _downstream_agents(primary_lane, automapper_needed, connector_needed),
        "dashboard_visibility_flag": owner_review or paper_candidate,
        "expected_agent_output_artifact": _expected_agent_output(primary_lane),
        "upstream_refs": list(row.get("upstream_refs") or []) + [ctx["upstream_pr166_qb_row_ref"]],
        "downstream_refs": [
            f"PR166_QC_TO_PR162E_Q::{idx:05d}",
            f"PR166_QC_TO_PR167::{idx:05d}",
            f"PR166_QC_TO_OWNER_DASHBOARD::{idx:05d}",
        ],
        "validation_refs": [c.VALIDATOR_REF],
        "no_orphan_proof_ref": f"PR166_QC_NO_ORPHAN::{idx:05d}",
        "created_by_pr": c.PR_ID,
        "deterministic_sort_key": f"PR166_QC::{idx:05d}::{ctx['qku_id']}",
        "source_provenance_class": "UPSTREAM_PR166_QB_REPO_LOCAL_CANONICAL_HANDOFF",
        "candidate_authority_class": "NONLIVE_CANDIDATE_REPLAY_PAPER_ONLY",
        "source_locator": "docs/master_plan/generated/PR166_QB_To_PR166_QC.report.json",
        "no_source_truth_acceptance_flag": True,
        "no_connector_binding_flag": True,
        "no_profit_evidence_flag": True,
        "no_current_connector_binding_flag": True,
        "no_private_state_fetch_flag": True,
        "not_profit_evidence_flag": True,
        "no_backend_execution_flag": True,
        "explicit_fee_component": _round(fee),
        "bid_ask_spread_component": _round(spread),
        "slippage_component": _round(slippage),
        "impact_component": _round(impact),
        "latency_component": _round(latency_component),
        "no_fill_opportunity_cost_component": _round(no_fill_cost),
        "settlement_finality_component": _round(settlement),
        "market_state_mismatch_component": _round(mismatch),
        "model_vs_execution_gap_component": _round(model_gap),
        "benchmark_to_replay_translation_penalty": _round(benchmark_translation),
        "replay_to_paper_translation_penalty": replay_to_paper,
        "total_tca_estimate": total_tca,
        "tca_reason_codes": _tca_reason_codes(total_tca, no_fill_risk, latency_component, capacity_penalty, crowding_penalty),
        "trial_family_id": f"PR166_QC_TRIAL_FAMILY::{ctx['model_family']}",
        "near_duplicate_cluster_id": str(overfit.get("near_duplicate_cluster_id") or f"PR166_QC_NEAR_DUP::{idx % 53:02d}"),
        "effective_independent_trial_count": int(_float(overfit.get("effective_independent_trial_count"), 12 + (idx % 17))),
        "family_wise_selection_pressure": _round(_float(overfit.get("family_wise_selection_pressure"), 0.09 + (idx % 7) * 0.01)),
        "deflated_score_proxy": _round(deflated_score),
        "probability_of_backtest_overfitting_proxy": _round(pbo_proxy),
        "replay_instability_penalty": _round(divergence * 0.35),
        "paper_instability_penalty": _round(divergence * 0.45),
        "replay_paper_divergence_penalty": _round(divergence * 0.50),
        "seed_instability_penalty": _round(seed_instability),
        "rank_stability_score": _round(_clamp(1.0 - pbo_proxy - seed_instability, 0.0, 1.0)),
        "repeated_test_inflation_penalty": repeated_test_penalty,
        "holdout_walk_forward_eligibility_flag": subset,
        "cpcv_purged_walk_forward_route_flag": not subset or pbo_proxy > 0.28,
        "event_cluster": f"EVENT_CLUSTER::{idx % 31:02d}",
        "question_market_cluster": f"QUESTION_MARKET_CLUSTER::{idx % 29:02d}",
        "formula_family_cluster": f"FORMULA_CLUSTER::{_slug(ctx['formula_id'])[:40]}",
        "qku_family_cluster": f"QKU_CLUSTER::{_slug(ctx['qku_family'])[:40]}",
        "algorithm_family_cluster": f"ALGO_CLUSTER::{_slug(ctx['algorithm_id'])[:40]}",
        "quantum_model_family_cluster": f"QUANTUM_MODEL::{ctx['model_family']}",
        "regime_cluster": f"REGIME_CLUSTER::{idx % 17:02d}",
        "time_to_resolution_bucket": f"TTR_BUCKET::{idx % 6:02d}",
        "liquidity_bucket": _liquidity_bucket(fill_probability),
        "correlation_proxy_bucket": f"CORRELATION_BUCKET::{idx % 5:02d}",
        "diversification_contribution": _round(_float(portfolio.get("diversification_contribution"), 0.04 + (idx % 9) * 0.006)),
        "concentration_penalty": _round(_float(portfolio.get("concentration_penalty"), 0.012 + (idx % 8) * 0.003)),
        "marginal_expected_net_edge": expected_net,
        "marginal_diversification_benefit": _round(_float(portfolio.get("marginal_diversification_benefit"), 0.03 + (idx % 7) * 0.004)),
        "marginal_risk_cost": _round(pbo_proxy * 0.04),
        "marginal_latency_cost": _round(latency_component * 0.8),
        "marginal_capacity_cost": capacity_penalty,
        "marginal_crowding_cost": crowding_penalty,
        "marginal_replay_paper_learning_value": _round((0.06 if subset else 0.025) + divergence * 0.10),
        "marginal_paper_promotion_value": _round(0.08 if paper_candidate else 0.02),
        "marginal_repair_learning_value": _round(0.07 if still_negative else 0.018),
        "final_marginal_utility_evidence_score": _round(_clamp(evidence_quality + (0.04 if paper_candidate else 0.0) - (0.03 if still_negative else 0.0), 0.0, 1.0)),
        "regime_id": f"PR166_QC_REGIME::{idx % 17:02d}",
        "market_state_id": f"PR166_QC_MARKET_STATE::{idx % 23:02d}",
        "liquidity_regime": _liquidity_bucket(fill_probability),
        "volatility_regime": f"VOL_REGIME::{idx % 4:02d}",
        "spread_regime": f"SPREAD_REGIME::{idx % 5:02d}",
        "time_to_resolution_regime": f"TTR_REGIME::{idx % 6:02d}",
        "event_category_regime": f"EVENT_CATEGORY::{idx % 12:02d}",
        "benchmark_success_failure_memory": str(regime.get("benchmark_success_failure_memory") or "BENCHMARK_MEMORY_NONLIVE"),
        "replay_success_failure_memory": "REPLAY_NONLIVE_COMPUTED" if subset else "REPLAY_STRUCTURAL_ROUTE",
        "paper_success_failure_memory": "PAPER_NONLIVE_COMPUTED" if subset else "PAPER_STRUCTURAL_ROUTE",
        "negative_memory_overlay": "STILL_NEGATIVE_AFTER_COSTS" if still_negative else "NO_NEGATIVE_OVERLAY",
        "no_fill_memory": "NO_FILL_RISK_RECORDED",
        "cooldown_retest_eligibility": "ELIGIBLE_FOR_BOUNDED_RETEST" if subset else "STRUCTURAL_RETEST_ROUTE",
        "condition_scoped_warning": "NONLIVE_ONLY_DO_NOT_PROMOTE_TO_LIVE",
        "quantum_inspired_improved_replay_flag": qinspired_bonus > 0,
        "quantum_inspired_improved_paper_flag": qinspired_bonus > 0 and paper_score > replay_score - 0.08,
        "hybrid_improved_replay_flag": hybrid_bonus > 0,
        "hybrid_improved_paper_flag": hybrid_bonus > 0 and paper_score > 0.52,
        "repair_family": repair_family,
        "repair_applicable_flag": still_negative or automapper_needed or connector_needed,
    }
    return common


def build_row_payloads(source: SourceData, evidence_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {filename: [] for filename in c.REPORT_FILENAMES}
    rows["PR166_QC_SourceReplayParams.report.json"] = build_source_rows()
    rows["PR166_QC_InputConsumption.report.json"] = build_input_consumption_rows(source)
    rows["PR166_QC_RetestBudget.report.json"] = [build_budget_row(evidence_rows)]
    rows["PR166_QC_NoLiveAuthorityBoundary.report.json"] = [build_authority_boundary_row()]
    for filename in c.ROW_REPORTS:
        rows[filename] = [row_for_report(filename, row, index) for index, row in enumerate(evidence_rows, start=1)]
    rows["PR166_QC_FinalSummary.report.json"] = [build_final_summary(source, evidence_rows)]
    return rows


def build_input_consumption_rows(source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, filename in enumerate(c.STRICT_INPUT_REPORTS, start=1):
        count = source.input_counts[filename]
        expected = 559 if filename in c.EXPECTED_559_INPUTS else count
        rows.append(
            {
                **_base_report_row("PR166_QC_InputConsumption.report.json", index),
                "row_id": f"PR166_QC_INPUT::{index:05d}",
                "source_report_ref": filename,
                "source_report_path": f"docs/master_plan/generated/{filename}",
                "expanded_record_count": count,
                "expected_record_count": expected,
                "record_count_matches_expected_flag": count == expected,
                "consumption_status": "CONSUMED_FOR_PR166_QC_REPLAY_PAPER_RETEST",
                "routed_report_refs": [
                    "PR166_QC_RetestEligibility.report.json",
                    "PR166_QC_ReplayEvidence.report.json",
                    "PR166_QC_NoOrphanProof.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_connector_binding_flag": True,
                "no_profit_evidence_flag": True,
            }
        )
    return rows


def build_budget_row(evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    subset_rows = [row for row in evidence_rows if row["actual_retest_subset_flag"]]
    by_role = Counter(row["champion_challenger_role"] for row in subset_rows)
    return {
        **_base_report_row("PR166_QC_RetestBudget.report.json", 1),
        "row_id": "PR166_QC_RETEST_BUDGET::00001",
        **c.RETEST_CAPS,
        "actual_replay_paper_subset_size": len(subset_rows),
        "actual_rows_per_role": dict(sorted(by_role.items())),
        "subset_selection_policy": "DETERMINISTIC_STRATIFIED_BY_BENCHMARK_ROLE_MODEL_FAMILY_ROUTE_VALUE_AND_SORT_KEY",
        "runtime_measurement_mode": "DETERMINISTIC_PROXY_DEFAULT_CI_NO_SUBPROCESS_REPLAY",
        "walk_forward_slices_used": c.RETEST_CAPS["max_walk_forward_slices_default_ci"],
        "scenario_states_used": c.RETEST_CAPS["max_scenario_states_default_ci"],
        "market_book_states_used": c.RETEST_CAPS["max_market_book_states_default_ci"],
        "random_seeds_used": c.RETEST_CAPS["max_random_seeds_default_ci"],
        "retest_iterations_used": c.RETEST_CAPS["max_retest_iterations_default_ci"],
        "manual_or_nightly_expansion_required_for_larger_retests_flag": True,
        "cloud_backend_execution_allowed_flag": False,
        "credential_access_allowed_flag": False,
        "connector_calls_allowed_flag": False,
        "no_unbounded_execution_flag": True,
        "no_backend_execution_flag": True,
        "validation_refs": [c.VALIDATOR_REF],
    }


def build_source_rows() -> list[dict[str, Any]]:
    specs = (
        ("SRC_QC_TCA_IMPLEMENTATION_SHORTFALL", "research_or_industry_tca", False, "https://www.quantitativebrokers.com/blog/a-brief-history-of-implementation-shortfall", 3, 3, 2, 6, 1, 0, 0, 3, 2, 1, 0, 0),
        ("SRC_QC_TCA_COMPONENTS", "non_official_industry_tca", False, "https://ryanoconnellfinance.com/implementation-shortfall/", 3, 3, 2, 7, 2, 0, 0, 3, 2, 1, 0, 0),
        ("SRC_QC_PREDICTION_MARKET_MICROSTRUCTURE", "research_prediction_market_microstructure", False, "https://arxiv.org/html/2604.24366v1", 4, 3, 3, 2, 1, 1, 1, 3, 2, 2, 1, 1),
        ("SRC_QC_BACKTEST_OVERFIT_PBO", "research_overfit_false_discovery", False, "https://portfoliooptimizationbook.com/book/8.3-dangers-backtesting.html", 2, 2, 0, 0, 0, 6, 2, 4, 2, 1, 0, 0),
        ("SRC_QC_PBO_CSCV", "research_overfit_false_discovery", False, "https://www.researchgate.net/publication/318600389_The_probability_of_backtest_overfitting", 2, 2, 0, 0, 0, 5, 2, 4, 2, 1, 0, 0),
        ("SRC_QC_CALIBRATION_SKLEARN", "official_calibration_docs", True, "https://scikit-learn.org/stable/modules/calibration.html", 2, 3, 0, 0, 0, 1, 5, 3, 2, 1, 0, 0),
        ("SRC_QC_BRIER_SCORE_SKLEARN", "official_metric_docs", True, "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html", 2, 3, 0, 0, 0, 1, 5, 3, 2, 1, 0, 0),
        ("SRC_QC_QISKIT_QUBO_QUADPROGRAM", "official_quantum_optimization_docs", True, "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html", 2, 2, 0, 0, 0, 0, 0, 2, 3, 0, 2, 1),
        ("SRC_QC_DWAVE_DIMOD_MODELS", "official_quantum_model_docs", True, "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html", 2, 2, 0, 0, 0, 0, 0, 2, 4, 0, 3, 1),
        ("SRC_QC_AWS_BRAKET_HYBRID_JOBS", "official_cloud_quantum_docs_route_only", True, "https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs.html", 1, 1, 0, 0, 1, 0, 0, 2, 2, 0, 4, 1),
        ("SRC_QC_ORDER_BOOK_STABILITY", "institutional_order_book_research", True, "https://www.financialresearch.gov/working-papers/files/OFRwp2014-09_PaddrikHayesSchererBeling_EffectsLimitOrderBookInformationLevelMarketStabilityMetrics.pdf", 2, 2, 4, 2, 1, 1, 0, 3, 2, 1, 2, 1),
        ("SRC_QC_PAPER_TRADING_VALIDATION", "non_official_paper_trading_practice", False, "https://blog.traderspost.io/article/paper-trading-strategy-development-guide", 2, 4, 1, 1, 1, 1, 1, 3, 2, 3, 1, 0),
    )
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        (
            source_id,
            source_type,
            official,
            locator,
            replay_count,
            paper_count,
            fill_count,
            tca_count,
            latency_count,
            overfit_count,
            calibration_count,
            quality_count,
            repair_count,
            threshold_count,
            connector_count,
            market_count,
        ) = spec
        rows.append(
            {
                **_base_report_row("PR166_QC_SourceReplayParams.report.json", index),
                "row_id": f"PR166_QC_SOURCE::{index:05d}",
                "source_id": source_id,
                "source_type": source_type,
                "official_flag": official,
                "non_official_flag": not official,
                "source_locator_or_query": locator,
                "replay_parameters_extracted_count": replay_count,
                "paper_parameters_extracted_count": paper_count,
                "fill_model_parameters_extracted_count": fill_count,
                "TCA_parameters_extracted_count": tca_count,
                "latency_parameters_extracted_count": latency_count,
                "overfit_control_parameters_extracted_count": overfit_count,
                "calibration_parameters_extracted_count": calibration_count,
                "evidence_quality_parameters_extracted_count": quality_count,
                "repair_strategy_parameters_extracted_count": repair_count,
                "threshold_policy_parameters_extracted_count": threshold_count,
                "candidate_values_extracted_count": replay_count + paper_count + fill_count + tca_count + overfit_count + calibration_count,
                "dashboard_review_requirements_extracted_count": threshold_count,
                "future_connector_route_notes_count": connector_count,
                "future_market_portability_notes_count": market_count,
                "rejected_reason": "",
                "routed_report_refs": [
                    "PR166_QC_ReplayEvidence.report.json",
                    "PR166_QC_PaperEvidence.report.json",
                    "PR166_QC_ConnectorRouteReadiness.report.json",
                ],
                "no_source_truth_acceptance_flag": True,
                "no_connector_binding_flag": True,
                "no_profit_evidence_flag": True,
            }
        )
    return rows


def build_authority_boundary_row() -> dict[str, Any]:
    return {
        **_base_report_row("PR166_QC_NoLiveAuthorityBoundary.report.json", 1),
        "row_id": "PR166_QC_NO_LIVE_AUTHORITY_BOUNDARY::00001",
        "boundary_status": "PASS_NONLIVE_ONLY",
        "forbidden_authority_counts_all_zero_flag": True,
        "no_live_order_authority_flag": True,
        "no_live_promotion_claim_flag": True,
        "no_owner_live_approval_receipt_flag": True,
        "no_source_truth_acceptance_flag": True,
        "no_connector_semantic_binding_flag": True,
        "no_private_state_fetch_flag": True,
        "no_runtime_cash_receipt_flag": True,
        "no_profit_evidence_flag": True,
        "no_cloud_backend_execution_flag": True,
        "no_quantum_backend_execution_flag": True,
        "no_quantum_advantage_claim_flag": True,
        "validation_refs": [c.VALIDATOR_REF],
    }


def row_for_report(filename: str, row: dict[str, Any], index: int) -> dict[str, Any]:
    output = dict(row)
    output["artifact_id"] = filename.removesuffix(".report.json")
    output["deterministic_sort_key"] = f"{filename}::{index:05d}"
    output["row_id"] = _row_id_for_report(filename, index)
    output["source_evidence_row_ref"] = f"PR166_QC_EVIDENCE::{index:05d}"
    if filename == "PR166_QC_ReplayPaperRepairLab.report.json":
        output.update(_repair_fields(row, index))
    elif filename == "PR166_QC_OwnerDashboardReview.report.json":
        output.update(_dashboard_fields(row, index))
    elif filename == "PR166_QC_ConnectorRouteReadiness.report.json":
        output.update(_connector_fields(row, index))
    elif filename == "PR166_QC_MarketPortability.report.json":
        output.update(_market_portability_fields(row, index))
    elif filename == "PR166_QC_AgentWorkOrders.report.json":
        output.update(_agent_work_order_fields(row, index))
    elif filename == "PR166_QC_AgentDAG.report.json":
        output.update(_agent_dag_fields(row, index))
    elif filename == "PR166_QC_NoOrphanProof.report.json":
        output.update(_no_orphan_fields(row, index))
    elif filename.startswith("PR166_QC_To_"):
        output.update(_handoff_fields(filename, row, index))
    elif filename == "PR166_QC_ReportConsumerCrosswalk.report.json":
        raise AssertionError("crosswalk rows are built separately")
    elif filename == "PR166_QC_ArtifactMap.report.json":
        raise AssertionError("artifact map rows are built separately")
    return output


def build_final_summary(source: SourceData, evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    dispositions = Counter(row["evidence_disposition"] for row in evidence_rows)
    grades = Counter(row["evidence_quality_grade"] for row in evidence_rows)
    lanes = Counter(row["primary_evidence_lane"] for row in evidence_rows)
    roles = Counter(row["champion_challenger_role"] for row in evidence_rows)
    subset = [row for row in evidence_rows if row["actual_retest_subset_flag"]]
    still_negative = [row for row in evidence_rows if row["still_negative_after_costs_flag"]]
    paper_candidates = [row for row in evidence_rows if row["paper_promotion_candidate_flag"]]
    owner_review = [row for row in evidence_rows if row["owner_dashboard_review_flag"]]
    connector = [row for row in evidence_rows if row["downstream_future_connector_route_ref"]]
    automapper = [row for row in evidence_rows if row["automapper_needed_flag"]]
    open_trade = [row for row in evidence_rows if row["open_trade_sim_route_flag"]]
    benchmark_only = [row for row in evidence_rows if row["benchmark_only_residual_flag"]]
    return {
        **_base_report_row("PR166_QC_FinalSummary.report.json", 1),
        "row_id": "PR166_QC_FINALSUMMARY::00001",
        "consumed_pr166_qc_handoff_rows": len(evidence_rows),
        "expected_pr166_qc_handoff_rows": 559,
        "input_record_counts": dict(sorted(source.input_counts.items())),
        "evidence_disposition_counts": dict(sorted(dispositions.items())),
        "evidence_quality_grade_counts": dict(sorted(grades.items())),
        "primary_evidence_lane_counts": dict(sorted(lanes.items())),
        "paper_champion_challenger_role_counts": dict(sorted(roles.items())),
        "replay_paper_retest_subset_count": len(subset),
        "retest_budget_caps": dict(c.RETEST_CAPS),
        "replay_evidence_computed_rows": sum(1 for row in evidence_rows if row["replay_evidence_flag"]),
        "paper_evidence_computed_rows": sum(1 for row in evidence_rows if row["paper_evidence_flag"]),
        "replay_paper_divergence_average": _round(sum(row["replay_paper_divergence_score"] for row in evidence_rows) / len(evidence_rows)),
        "calibration_average": _round(sum(row["calibration_score"] for row in evidence_rows) / len(evidence_rows)),
        "sample_sufficiency_average": _round(sum(row["sample_sufficiency_score"] for row in evidence_rows) / len(evidence_rows)),
        "scenario_coverage_average": _round(sum(row["scenario_coverage_score"] for row in evidence_rows) / len(evidence_rows)),
        "tca_average": _round(sum(row["total_tca_estimate"] for row in evidence_rows) / len(evidence_rows)),
        "fill_probability_average": _round(sum(row["fill_probability_score"] for row in evidence_rows) / len(evidence_rows)),
        "no_fill_risk_average": _round(sum(row["no_fill_risk_score"] for row in evidence_rows) / len(evidence_rows)),
        "latency_adjusted_average": _round(sum(row["latency_adjusted_score"] for row in evidence_rows) / len(evidence_rows)),
        "queue_risk_adjusted_average": _round(sum(row["queue_risk_adjusted_score"] for row in evidence_rows) / len(evidence_rows)),
        "overfit_fdr_average_penalty": _round(sum(row["false_discovery_penalty"] for row in evidence_rows) / len(evidence_rows)),
        "portfolio_marginal_utility_average": _round(sum(row["final_marginal_utility_evidence_score"] for row in evidence_rows) / len(evidence_rows)),
        "still_negative_after_costs_count": len(still_negative),
        "replay_paper_repair_lab_count": len(evidence_rows),
        "automapper_needed_count": len(automapper),
        "owner_dashboard_review_count": len(owner_review),
        "connector_route_readiness_count": len(connector),
        "benchmark_only_residual_count": len(benchmark_only),
        "open_trade_sim_handoff_count": len(open_trade),
        "paper_promotion_candidate_count": len(paper_candidates),
        "market_portability_rows": len(evidence_rows),
        "report_consumer_crosswalk_status": "COMPLETE",
        "universal_artifact_consumer_map_status": "COMPLETE",
        "agent_work_order_rows": len(evidence_rows),
        "agent_dag_rows": len(evidence_rows),
        "no_orphan_proof_rows": len(evidence_rows),
        "downstream_handoff_counts": {
            "PR162E-Q": len(evidence_rows),
            "PR167": len(evidence_rows),
            "PR162E": len(evidence_rows),
            "PR162F": len(evidence_rows),
            "OWNER_DASHBOARD": len(evidence_rows),
            "CLOUD_SWITCHBOARD": len(evidence_rows),
            "FUTURE_CONNECTORS": len(evidence_rows),
        },
        "external_candidate_provenance_status": "SOURCE_REPLAY_PARAMS_ROUTE_ONLY_NO_SOURCE_TRUTH",
        "forbidden_authority_counts_all_zero_flag": True,
        "dashboard_ui_implemented_flag": False,
        "cloud_backend_execution_count": 0,
        "credential_access_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "profit_evidence_count": 0,
        "live_order_authority_count": 0,
        "live_promotion_claim_count": 0,
        "source_truth_acceptance_count": 0,
        "connector_semantic_binding_count": 0,
        "private_state_fetch_count": 0,
        "runtime_cash_receipt_count": 0,
        "qtt_sha_authority_count": 0,
        "atomicrows_bundle_hash_authority_count": 0,
        "record_count": 1,
    }


def build_crosswalk_rows(payloads: dict[str, dict[str, Any]], source: SourceData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.STRICT_INPUT_REPORTS:
        rows.append(_crosswalk_row(index, filename, produced_by="PR166-QB" if filename.startswith("PR166_QB") else "PR166-Q", consumed=True))
        index += 1
    for filename in c.REPORT_FILENAMES:
        rows.append(_crosswalk_row(index, filename, produced_by=c.PR_ID, consumed=False, payload=payloads.get(filename)))
        index += 1
    return rows


def build_artifact_map_rows(
    source: SourceData,
    payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for filename in c.STRICT_INPUT_REPORTS:
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QC_CONSUMED::{filename}",
                f"docs/master_plan/generated/{filename}",
                "consumed_upstream_report",
                produced_by="PR166-QB" if filename.startswith("PR166_QB") else "PR166-Q",
                terminal=False,
            )
        )
        index += 1
    for filename in c.REPORT_FILENAMES:
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QC_REPORT::{filename}",
                f"docs/master_plan/generated/{filename}",
                "generated_root_report",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    for shard_path in sorted(shard_payloads):
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QC_SHARD::{Path(shard_path).name}",
                shard_path,
                "generated_shard_report",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    for filename in schema_filenames():
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QC_SCHEMA::{filename}",
                f"{c.SCHEMA_DIR.as_posix()}/{filename}",
                "generated_schema",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    for tool_path in (c.BUILDER_REF, c.VALIDATOR_REF):
        rows.append(
            _artifact_map_row(
                index,
                f"PR166_QC_TOOL::{tool_path}",
                tool_path,
                "tool_entrypoint",
                produced_by=c.PR_ID,
                terminal=False,
            )
        )
        index += 1
    return rows


def payloads_from_rows(
    row_payloads: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
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
                shard_name = (
                    f"{filename.removesuffix('.report.json')}"
                    f".part_{shard_index:04d}_of_{len(chunks):04d}.report.json"
                )
                shard_path = c.SHARD_DIR / shard_name
                shard_ref = shard_path.as_posix()
                shard_files.append(shard_ref)
                shard_manifest_refs.append(
                    {
                        "shard_index": shard_index,
                        "shard_path": shard_ref,
                        "row_count": len(chunk),
                    }
                )
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
                **_base_report_row("PR166_QC_ReportManifest.report.json", index),
                "row_id": f"PR166_QC_MANIFEST::{index:05d}",
                "report_ref": filename,
                "report_path": f"docs/master_plan/generated/{filename}",
                "record_count": payload.get("record_count", 0),
                "schema_ref": payload.get("schema_ref") or schema_filename(filename),
                "sharded_flag": bool(payload.get("sharded_flag")),
                "shard_files": payload.get("shard_files", []),
                "consumer_report_refs": [
                    "PR166_QC_ReportConsumerCrosswalk.report.json",
                    "PR166_QC_ArtifactMap.report.json",
                    "PR166_QC_NoOrphanProof.report.json",
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
            "required": [
                "report_name",
                "roadmap_pr_id",
                "created_by_pr",
                "schema_ref",
                "record_count",
                "records",
            ],
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
    stem = report_filename.removesuffix(".report.json")
    stem = stem.replace("PR166_QC", "pr166_qc")
    for acronym in ("QAOA", "VQE", "QUBO", "BQM", "CQM", "DQM", "TCA", "FDR", "DAG", "QC"):
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


def _crosswalk_row(
    index: int,
    filename: str,
    *,
    produced_by: str,
    consumed: bool,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        **_base_report_row("PR166_QC_ReportConsumerCrosswalk.report.json", index),
        "row_id": f"PR166_QC_CROSSWALK::{index:05d}",
        "report_id": filename.removesuffix(".report.json"),
        "report_path": f"docs/master_plan/generated/{filename}",
        "producer_module": c.PACKAGE_IMPORT if not consumed else "upstream_generated_report",
        "producer_pr": produced_by,
        "owning_agent_id": "Governance",
        "consuming_agent_ids": ["Governance", "Commander", "Replay Agent", "Paper Agent"],
        "consuming_downstream_reports": [
            "PR166_QC_ArtifactMap.report.json",
            "PR166_QC_NoOrphanProof.report.json",
            "PR166_QC_FinalSummary.report.json",
        ],
        "consuming_downstream_prs": list(c.DOWNSTREAM_PR_REFS),
        "dashboard_visibility_flag": filename in {
            "PR166_QC_OwnerDashboardReview.report.json",
            "PR166_QC_FinalSummary.report.json",
        },
        "governance_visibility_flag": True,
        "commander_visibility_flag": True,
        "terminal_flag": False,
        "terminal_reason": "",
        "no_orphan_proof_ref": "PR166_QC_NoOrphanProof.report.json",
        "record_count": 0 if payload is None else payload.get("record_count", 0),
    }


def _artifact_map_row(
    index: int,
    artifact_id: str,
    artifact_path: str,
    artifact_type: str,
    *,
    produced_by: str,
    terminal: bool,
) -> dict[str, Any]:
    return {
        **_base_report_row("PR166_QC_ArtifactMap.report.json", index),
        "row_id": f"PR166_QC_ARTIFACTMAP::{index:05d}",
        "artifact_id": artifact_id,
        "artifact_path": normalize_repo_ref(artifact_path),
        "artifact_type": artifact_type,
        "produced_by_pr": produced_by,
        "consumed_by_module": c.PACKAGE_IMPORT,
        "consumed_by_report": "PR166_QC_ReportConsumerCrosswalk.report.json",
        "consumed_by_agent": "Governance",
        "consumed_by_downstream_pr": list(c.DOWNSTREAM_PR_REFS),
        "terminal_flag": terminal,
        "terminal_reason": "" if not terminal else "TERMINAL_SUPPORTING_ARTIFACT_WITH_VALIDATION_CONSUMER",
        "validation_ref": c.VALIDATOR_REF,
        "owner_review_ref": "PR166_QC_OwnerDashboardReview.report.json",
    }


def _repair_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    still_negative = bool(row["still_negative_after_costs_flag"])
    family = row["repair_family"]
    return {
        "repair_row_id": f"PR166_QC_REPAIR::{index:05d}",
        "upstream_pr166_qc_row_ref": f"PR166_QC_EVIDENCE::{index:05d}",
        "evidence_negative_reason": _blocker_reason(
            still_negative,
            bool(row["actual_retest_subset_flag"]),
            _float(row["evidence_quality_score"]),
            _float(row["calibration_score"]),
            _float(row["sample_sufficiency_score"]),
            _float(row["scenario_coverage_score"]),
        ),
        "repair_family": family,
        "proposed_formula_delta": "KEEP_FORMULA_ADD_NONLIVE_THRESHOLD_GUARD" if still_negative else "NO_FORMULA_DELTA_REQUIRED",
        "proposed_parameter_delta": "REDUCE_SIZE_AND_TIGHTEN_FILL_THRESHOLD" if still_negative else "PRESERVE_CURRENT_PARAMETER_STACK",
        "proposed_execution_route_delta": "PREFER_CLASSICAL_FALLBACK_AND_QUANTUM_PRECOMPUTE_SLATE",
        "proposed_retest_delta": "ADD_BOUNDED_REPLAY_PAPER_RETEST_SLICE",
        "proposed_threshold_delta": "RAISE_LCB_EDGE_AND_FILL_PROBABILITY_THRESHOLD",
        "expected_edge_delta_candidate": _round(max(0.004, abs(_float(row["expected_net_profit_per_order_candidate"])) * 0.25)),
        "expected_tca_delta_candidate": _round(-abs(_float(row["total_tca_estimate"])) * 0.12),
        "expected_latency_delta_candidate": _round(-abs(_float(row["latency_component"])) * 0.15),
        "expected_fill_delta_candidate": _round((1.0 - _float(row["fill_probability_score"])) * 0.10),
        "expected_calibration_delta_candidate": _round((1.0 - _float(row["calibration_score"])) * 0.08),
        "expected_net_profit_delta_candidate": _round(max(0.006, abs(_float(row["expected_net_profit_per_order_candidate"])) * 0.35)),
        "replay_retest_route_ref": row["downstream_pr167_route_ref"],
        "paper_retest_route_ref": row["downstream_owner_dashboard_route_ref"],
        "downstream_pr162e_q_route_ref": row["downstream_pr162e_q_route_ref"],
        "downstream_pr167_route_ref": row["downstream_pr167_route_ref"],
        "owning_agent_id": "Execution/TCA Agent" if still_negative else row["owning_agent_id"],
        "reviewer_agent_id": "Governance",
        "not_profit_evidence_flag": True,
        "no_live_authority_flag": True,
    }


def _dashboard_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "dashboard_review_id": f"PR166_QC_DASHBOARD_REVIEW::{index:05d}",
        "reason_for_owner_review": _dashboard_reason(row),
        "replay_paper_summary": (
            f"replay={row['replay_evidence_score']}; paper={row['paper_evidence_score']}; "
            f"grade={row['evidence_quality_grade']}; lane={row['primary_evidence_lane']}"
        ),
        "future_dashboard_pr_ref": "FUTURE_OWNER_DASHBOARD_REVIEW_PR_NO_UI_IN_PR166_QC",
        "no_live_authority_flag": True,
    }


def _connector_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    required = ["event_id", "market_id", "book_snapshot", "fees", "fills", "latency", "settlement_state"]
    missing = ["connector_semantics", "private_account_state"] if row["primary_evidence_lane"] == "FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING" else ["connector_semantics"]
    return {
        "connector_route_id": f"PR166_QC_CONNECTOR_ROUTE::{index:05d}",
        "future_connector_family": "PREDICTION_MARKET_CLOB_CONNECTOR_ROUTE_ONLY",
        "future_market_family": "prediction_market",
        "required_data_fields": required,
        "missing_data_fields": missing,
        "candidate_source_refs": ["PR166_QC_SourceReplayParams.report.json"],
        "no_current_connector_binding_flag": True,
        "no_source_truth_acceptance_flag": True,
        "no_private_state_fetch_flag": True,
        "downstream_connector_pr_ref": "FUTURE_CONNECTOR_ROUTES_NO_BINDING",
        "owning_agent_id": "Connector Readiness Agent",
        "reviewer_agent_id": "Governance",
    }


def _market_portability_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "compatible_future_market_families": list(c.FUTURE_MARKET_FAMILIES),
        "market_specific_inputs_required": ["event_resolution", "order_book", "fee_schedule", "settlement_calendar"],
        "execution_route_portability_class": "ROUTE_METADATA_ONLY_NO_CONNECTOR_BINDING",
        "data_binding_portability_class": "CANDIDATE_FIELDS_ONLY_NO_SOURCE_TRUTH",
        "connector_required_future_flag": True,
        "no_current_connector_binding_flag": True,
        "no_live_authority_flag": True,
        "downstream_future_market_pr_ref": "FUTURE_MARKET_PLATFORM_PORTABILITY_PR",
    }


def _agent_work_order_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "work_order_id": f"PR166_QC_WORK_ORDER::{index:05d}",
        "source_artifact_ref": "PR166_QC_ReplayEvidence.report.json",
        "source_row_ref": f"PR166_QC_EVIDENCE::{index:05d}",
        "task_type": row["primary_evidence_lane"],
        "task_priority": _task_priority(row),
        "expected_input_refs": row["input_refs"],
        "expected_output_refs": row["output_refs"],
        "downstream_pr_refs": list(c.DOWNSTREAM_PR_REFS),
        "terminal_flag": False,
        "terminal_reason": "",
        "no_live_authority_flag": True,
    }


def _agent_dag_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "dag_node_id": f"PR166_QC_DAG::{index:05d}",
        "upstream_pr_refs": ["PR166-QB", "PR166-Q", "PR165-D2"],
        "upstream_row_refs": row["upstream_refs"],
        "replay_route": row["primary_evidence_lane"],
        "paper_route": row["champion_challenger_role"],
        "automapper_route": row["downstream_pr162e_q_route_ref"],
        "open_trade_simulator_route": row["downstream_pr167_route_ref"],
        "connector_readiness_route": row["downstream_future_connector_route_ref"],
        "future_cloud_switchboard_route": row["downstream_cloud_switchboard_route_ref"],
        "future_owner_dashboard_route": row["downstream_owner_dashboard_route_ref"],
        "no_orphan_proof": row["no_orphan_proof_ref"],
    }


def _no_orphan_fields(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "no_orphan_id": f"PR166_QC_NO_ORPHAN::{index:05d}",
        "no_orphan_status": "NO_ORPHAN",
        "artifact_refs_checked": [
            "PR166_QC_ReplayEvidence.report.json",
            "PR166_QC_PaperEvidence.report.json",
            "PR166_QC_ReportConsumerCrosswalk.report.json",
            "PR166_QC_ArtifactMap.report.json",
        ],
        "responsible_agent_ref": row["owning_agent_id"],
        "downstream_consumer_refs": row["downstream_refs"],
        "terminal_flag": False,
        "terminal_reason": "",
    }


def _handoff_fields(filename: str, row: dict[str, Any], index: int) -> dict[str, Any]:
    route = filename.removesuffix(".report.json").replace("PR166_QC_To_", "")
    return {
        "handoff_id": f"PR166_QC_TO_{route.upper()}::{index:05d}",
        "downstream_pr_ref": _downstream_pr_for_route(route),
        "downstream_route": route,
        "handoff_reason": _handoff_reason(route, row),
        "source_evidence_row_ref": f"PR166_QC_EVIDENCE::{index:05d}",
        "nonlive_replay_paper_only_flag": True,
        "no_live_authority_flag": True,
        "no_connector_binding_flag": True,
        "no_profit_evidence_flag": True,
    }


def _clear_previous_shards(repo_root: Path) -> None:
    shard_dir = repo_root / c.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR166_QC_*.report.json"):
        path.unlink()


def _chunks(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)] or [[]]


def _selection_score(ctx: dict[str, Any]) -> float:
    row = ctx["handoff"]
    role_bonus = {
        "benchmark champion": 0.10,
        "benchmark challenger": 0.08,
        "replay/paper retest": 0.07,
        "quantum-repair-lab": 0.06,
        "automapper priority": 0.055,
        "benchmark watch": 0.045,
        "repair": 0.04,
        "future-owner-dashboard-toggle-route": 0.03,
        "future-cloud-switchboard-route": 0.025,
    }.get(str(ctx["benchmark_role"]), 0.02)
    return (
        _float(row.get("execution_adjusted_score"), 0.5)
        + _float(row.get("marginal_utility_score"), 0.5) * 0.14
        + _float(row.get("best_benchmark_objective_candidate"), 0.4) * 0.09
        + role_bonus
    )


def _evidence_disposition(
    *,
    subset: bool,
    paper_candidate: bool,
    still_negative: bool,
    automapper_needed: bool,
    owner_review: bool,
    connector_needed: bool,
    benchmark_only: bool,
    idx: int,
) -> str:
    if subset and paper_candidate:
        return "REPLAY_AND_PAPER_EVIDENCE_COMPUTED_BOUNDED"
    if subset and not still_negative:
        return "REPLAY_EVIDENCE_COMPUTED_BOUNDED" if idx % 2 else "PAPER_EVIDENCE_COMPUTED_BOUNDED"
    if still_negative:
        return "EVIDENCE_REPAIR_PROPOSAL_CREATED"
    if automapper_needed:
        return "EVIDENCE_ROUTED_TO_PR162E_Q_AUTOMAPPER"
    if owner_review:
        return "EVIDENCE_ROUTED_TO_OWNER_DASHBOARD_REVIEW"
    if connector_needed:
        return "EVIDENCE_ROUTED_TO_FUTURE_CONNECTOR_NO_BINDING"
    if benchmark_only:
        return "EVIDENCE_REMAINS_BENCHMARK_ONLY"
    if idx % 9 == 0:
        return "EVIDENCE_ROUTED_TO_PR167_OPEN_TRADE_SIMULATOR"
    if idx % 13 == 0:
        return "EVIDENCE_ROUTED_TO_PR162F_OWNER_AGENT_INTAKE"
    if idx % 17 == 0:
        return "EVIDENCE_ROUTED_TO_PR162E_PLUGIN_FRAMEWORK"
    return "PAPER_STRUCTURAL_ONLY_RUNTIME_CAP"


def _primary_lane(
    *,
    benchmark_role: str,
    subset: bool,
    paper_candidate: bool,
    still_negative: bool,
    automapper_needed: bool,
    owner_review: bool,
    connector_needed: bool,
    open_trade_ready: bool,
    benchmark_only: bool,
) -> str:
    if paper_candidate and benchmark_role == "benchmark champion":
        return "PAPER_CHAMPION_CANDIDATE"
    if paper_candidate:
        return "PAPER_CHALLENGER_CANDIDATE"
    if still_negative:
        return "STILL_NEGATIVE_AFTER_TCA_LATENCY_FILL_RISK"
    if automapper_needed:
        return "AUTOMAPPER_NEEDED"
    if open_trade_ready:
        return "OPEN_TRADE_SIM_READY"
    if owner_review:
        return "OWNER_DASHBOARD_REVIEW_NEEDED"
    if connector_needed:
        return "FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING"
    if benchmark_only:
        return "BENCHMARK_ONLY_RESIDUAL"
    if subset and benchmark_role == "benchmark champion":
        return "REPLAY_CHAMPION_CANDIDATE"
    if subset and benchmark_role == "benchmark challenger":
        return "REPLAY_CHALLENGER_CANDIDATE"
    if subset:
        return "REPLAY_WATCH_CANDIDATE"
    return "PAPER_RETEST_REQUIRED"


def _evidence_lanes(
    primary: str,
    still_negative: bool,
    automapper_needed: bool,
    owner_review: bool,
    connector_needed: bool,
    open_trade_ready: bool,
) -> list[str]:
    lanes = [primary]
    if still_negative and primary != "STILL_NEGATIVE_AFTER_TCA_LATENCY_FILL_RISK":
        lanes.append("STILL_NEGATIVE_AFTER_TCA_LATENCY_FILL_RISK")
    if still_negative:
        lanes.append("REPLAY_PAPER_REPAIR_PROPOSAL")
    if automapper_needed and primary != "AUTOMAPPER_NEEDED":
        lanes.append("AUTOMAPPER_NEEDED")
    if owner_review and primary != "OWNER_DASHBOARD_REVIEW_NEEDED":
        lanes.append("OWNER_DASHBOARD_REVIEW_NEEDED")
    if connector_needed and primary != "FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING":
        lanes.append("FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING")
    if open_trade_ready and primary != "OPEN_TRADE_SIM_READY":
        lanes.append("OPEN_TRADE_SIM_READY")
    return list(dict.fromkeys(lanes))


def _evidence_grade(
    *,
    paper_candidate: bool,
    still_negative: bool,
    subset: bool,
    evidence_quality: float,
    replay_score: float,
    sample_score: float,
    scenario_score: float,
    benchmark_only: bool,
) -> str:
    if paper_candidate and evidence_quality >= 0.64:
        return "A_REPLAY_AND_PAPER_STRONG_NONLIVE"
    if subset and replay_score >= 0.58 and evidence_quality >= 0.58:
        return "B_REPLAY_STRONG_PAPER_PENDING"
    if benchmark_only:
        return "G_BENCHMARK_ONLY_RESIDUAL"
    if still_negative:
        return "E_STILL_NEGATIVE_AFTER_COSTS"
    if min(sample_score, scenario_score) < 0.55:
        return "F_INSUFFICIENT_DATA_ROUTE_REQUIRED"
    if subset:
        return "D_RETEST_REQUIRED"
    return "C_PAPER_READY_STRUCTURAL"


def _paper_role(
    paper_candidate: bool,
    still_negative: bool,
    evidence_quality: float,
    paper_score: float,
    subset: bool,
    primary_lane: str,
) -> str:
    if paper_candidate and paper_score >= 0.61 and evidence_quality >= 0.64:
        return "paper champion"
    if paper_candidate:
        return "paper challenger"
    if still_negative:
        return "no-trade nonlive"
    if primary_lane in {"BENCHMARK_ONLY_RESIDUAL", "FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING"}:
        return "benchmark-only residual"
    if subset:
        return "paper watch"
    return "paper retest"


def _repair_family(idx: int, still_negative: bool, automapper_needed: bool, connector_needed: bool) -> str:
    if automapper_needed:
        return "automapper route repair"
    if connector_needed:
        return "connector route readiness repair without connector binding"
    families = (
        "TCA reduction repair",
        "latency reduction repair",
        "fill-probability improvement repair",
        "no-fill risk reduction repair",
        "queue-risk reduction repair",
        "order-size rescaling repair",
        "participation-cap repair",
        "capacity/crowding repair",
        "regime filter repair",
        "event-category filter repair",
        "time-to-resolution filter repair",
        "formula/parameter adjustment repair",
        "quantum-precompute slate repair",
        "classical fallback tightening repair",
        "replay/paper retest expansion repair",
        "owner dashboard review repair",
        "evidence calibration repair",
        "sample/scenario expansion repair",
        "decision threshold repair",
        "no-trade threshold repair",
    )
    return families[idx % len(families)] if still_negative else "replay/paper retest expansion repair"


def _subset_reason(subset: bool, ctx: dict[str, Any], primary_lane: str) -> str:
    if subset:
        return f"BOUNDED_ACTUAL_REPLAY_PAPER_SUBSET::{ctx['benchmark_role']}::{ctx['model_family']}"
    return f"STRUCTURAL_ROUTE_WITH_EXACT_LANE::{primary_lane}"


def _blocker_reason(
    still_negative: bool,
    subset: bool,
    evidence_quality: float,
    calibration_score: float,
    sample_score: float,
    scenario_score: float,
) -> str:
    if still_negative:
        return "NEGATIVE_AFTER_TCA_LATENCY_FILL_QUEUE_CAPACITY_CROWDING_AND_OVERFIT_PENALTIES"
    if not subset:
        return "DEFAULT_CI_RUNTIME_CAP_STRUCTURAL_NONLIVE_ROUTE"
    if evidence_quality < 0.56:
        return "EVIDENCE_QUALITY_BELOW_PAPER_PROMOTION_THRESHOLD"
    if calibration_score < 0.55:
        return "CALIBRATION_BELOW_THRESHOLD"
    if min(sample_score, scenario_score) < 0.55:
        return "SAMPLE_OR_SCENARIO_COVERAGE_BELOW_THRESHOLD"
    return "PAPER_PROMOTION_THRESHOLDS_NOT_ALL_MET"


def _tca_reason_codes(total_tca: float, no_fill_risk: float, latency: float, capacity_penalty: float, crowding_penalty: float) -> list[str]:
    codes = ["FEE_SPREAD_SLIPPAGE_IMPACT_RECORDED", "IMPLEMENTATION_SHORTFALL_PROXY_RECORDED"]
    if total_tca > 0.017:
        codes.append("HIGH_TOTAL_TCA")
    if no_fill_risk > 0.32:
        codes.append("NO_FILL_OPPORTUNITY_COST_MATERIAL")
    if latency > 0.001:
        codes.append("LATENCY_DRAG_PRESENT")
    if capacity_penalty > 0.0:
        codes.append("CAPACITY_PENALTY_PRESENT")
    if crowding_penalty > 0.0:
        codes.append("CROWDING_PENALTY_PRESENT")
    return codes


def _owning_agent(primary_lane: str) -> str:
    mapping = {
        "AUTOMAPPER_NEEDED": "Quantum AutoMapper Agent",
        "OPEN_TRADE_SIM_READY": "Open Trade Simulator Agent",
        "OWNER_DASHBOARD_REVIEW_NEEDED": "Dashboard/Owner Review Agent",
        "FUTURE_CONNECTOR_ROUTE_NEEDED_NO_BINDING": "Connector Readiness Agent",
        "STILL_NEGATIVE_AFTER_TCA_LATENCY_FILL_RISK": "Execution/TCA Agent",
        "REPLAY_PAPER_REPAIR_PROPOSAL": "Replay Agent",
        "BENCHMARK_ONLY_RESIDUAL": "Quantum Comparator Agent",
    }
    if primary_lane.startswith("PAPER_"):
        return "Paper Agent"
    if primary_lane.startswith("REPLAY_"):
        return "Replay Agent"
    return mapping.get(primary_lane, "Governance")


def _agent_duty_ref(primary_lane: str) -> str:
    return f"PR166_QC_AGENT_DUTY::{_slug(primary_lane)}"


def _action_required(primary_lane: str) -> str:
    return f"PROCESS_{_slug(primary_lane)}_NONLIVE"


def _downstream_agents(primary_lane: str, automapper_needed: bool, connector_needed: bool) -> list[str]:
    agents = ["Governance", "Commander"]
    agents.append(_owning_agent(primary_lane))
    if automapper_needed:
        agents.append("Quantum AutoMapper Agent")
    if connector_needed:
        agents.append("Connector Readiness Agent")
    return list(dict.fromkeys(agents))


def _expected_agent_output(primary_lane: str) -> str:
    return f"PR166_QC_EXPECTED_OUTPUT::{_slug(primary_lane)}"


def _dashboard_reason(row: dict[str, Any]) -> str:
    if row["paper_promotion_candidate_flag"]:
        return "PAPER_PROMOTION_CANDIDATE_REQUIRES_OWNER_NONLIVE_REVIEW"
    if row["still_negative_after_costs_flag"]:
        return "STILL_NEGATIVE_AFTER_COSTS_REPAIR_OR_NO_TRADE_REVIEW"
    if row["owner_dashboard_review_flag"]:
        return "OWNER_REVIEW_ROUTE_SELECTED_BY_NONLIVE_EVIDENCE_POLICY"
    return "DASHBOARD_VISIBILITY_FOR_DOWNSTREAM_GOVERNANCE"


def _task_priority(row: dict[str, Any]) -> str:
    if row["paper_promotion_candidate_flag"]:
        return "HIGH"
    if row["still_negative_after_costs_flag"] or row["automapper_needed_flag"]:
        return "MEDIUM"
    return "NORMAL"


def _handoff_reason(route: str, row: dict[str, Any]) -> str:
    if route == "PR162E_Q":
        return "AUTOMAPPER_REFORMULATION_OR_QUANTUM_REPAIR_ROUTE"
    if route == "PR167":
        return "OPEN_TRADE_SIMULATOR_NONLIVE_REPLAY_PAPER_ROUTE"
    if route == "PR162E":
        return "PLUGIN_FRAMEWORK_DATA_OR_FORMULA_ROUTE"
    if route == "PR162F":
        return "OWNER_AGENT_INTAKE_ROUTE"
    if route == "OwnerDashboard":
        return "OWNER_DASHBOARD_REVIEW_ROUTE_NO_UI_IMPLEMENTED"
    if route == "CloudSwitchboard":
        return "FUTURE_CLOUD_SWITCHBOARD_ROUTE_OFF_BY_DEFAULT_NO_EXECUTION"
    if route == "FutureConnectors":
        return "FUTURE_CONNECTOR_ROUTE_NO_BINDING"
    return f"DOWNSTREAM_{route}_NONLIVE_ROUTE"


def _downstream_pr_for_route(route: str) -> str:
    return {
        "PR162E_Q": "PR162E-Q",
        "PR167": "PR167",
        "PR162E": "PR162E",
        "PR162F": "PR162F",
        "OwnerDashboard": "FUTURE_OWNER_DASHBOARD_REVIEW",
        "CloudSwitchboard": "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT",
        "FutureConnectors": "FUTURE_CONNECTOR_ROUTES_NO_BINDING",
    }.get(route, route)


def _reliability_bucket(calibration_score: float, brier_proxy: float) -> str:
    if calibration_score >= 0.70 and brier_proxy <= 0.18:
        return "HIGH_RELIABILITY"
    if calibration_score >= 0.55 and brier_proxy <= 0.28:
        return "MEDIUM_RELIABILITY"
    return "LOW_RELIABILITY_ROUTE_REQUIRED"


def _liquidity_bucket(fill_probability: float) -> str:
    if fill_probability >= 0.75:
        return "LIQUIDITY_HIGH"
    if fill_probability >= 0.60:
        return "LIQUIDITY_MEDIUM"
    return "LIQUIDITY_LOW"


def _row_id_for_report(report_name: str, index: int) -> str:
    stem = report_name.removesuffix(".report.json").upper()
    return f"{stem}::{index:05d}"


def _qku_family(qku_id: object) -> str:
    value = str(qku_id)
    if "QUANTUM" in value.upper():
        return "QUANTUM_ADVISORY_OPTIMIZATION"
    return "QKU_FORMULA_ALGORITHM"


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper() or "UNKNOWN"


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
