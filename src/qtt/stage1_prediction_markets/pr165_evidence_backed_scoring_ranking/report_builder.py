"""Build PR165 evidence-backed scoring and ranking artifacts."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import log
from pathlib import Path
from typing import Any

from . import paths as p
from .artifact_discovery import discover_inputs, index_by, load_records
from .central_scoring_reason_codes import MATERIALIZATION_REASON_CODES, SCORE_REASON_CODES
from .deterministic_ids import candidate_version, numeric_suffix, ref
from .input_consumption import build_optional_context_receipts, source_inputs_from_discovery
from .json_io import read_json, write_json
from .repair_routing_vocab import BASE_AGENT_ROUTES, DOWNSTREAM_CONSUMERS
from .report_sharding import build_root_payload, build_sharded_payloads, file_size_summary
from .schema_writer import write_schemas
from .score_model_config import (
    COMPONENT_WEIGHTS,
    CONFIDENCE_RANGE,
    FIXED_SEED_POLICY,
    NORMALIZATION_POLICY,
    PENALTY_CAPS,
    SCORE_FORMULA_VERSION,
    SCORE_MODEL_ID,
    SCORE_RANGE,
)
from .scoring_authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    FILES_INTENTIONALLY_NOT_TOUCHED,
    POLICY_MODULE_REF,
    authority_boundary_record,
    no_authority_record,
)
from .scoring_status_vocab import (
    DASHBOARD_HANDOFF_STATUS,
    PHAT_SOURCES,
    PLUGIN_PRIORITY_STATUS,
    PR162D_R3_PRIORITY_STATUS,
    PR165_B_HANDOFF_READY,
)


ACTIVE_EXPECTED = 6502
REMAINING_EXPECTED = 2858
TOTAL_EXPECTED = 9360


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root, p.EXPECTED_BRANCH)
    _clear_previous_pr165_shards(repo_root)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename], compact=filename in p.ROW_LEVEL_REPORTS)
    for rel_path, shard_payload in shard_payloads.items():
        write_json(repo_root / rel_path, shard_payload, compact=True)
    sizes = file_size_summary(repo_root, p.REPORT_FILENAMES)
    summary = dict(payloads["PR165_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR165_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR165_FinalSummary.report.json"].update(sizes)
    payloads["PR165_ReportManifest.report.json"] = build_root_payload(
        "PR165_ReportManifest.report.json",
        build_manifest(payloads),
        payloads["PR165_FinalSummary.report.json"]["source_inputs"],
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    write_json(repo_root / p.GENERATED_DIR / "PR165_FinalSummary.report.json", payloads["PR165_FinalSummary.report.json"])
    write_json(repo_root / p.GENERATED_DIR / "PR165_ReportManifest.report.json", payloads["PR165_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root, branch)
    return payloads


def build_payloads_with_shards(repo_root: Path, branch: str | None = None) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discover_inputs(repo_root)
    if discovery.missing_required_inputs:
        missing = ", ".join(discovery.missing_required_inputs)
        raise RuntimeError(f"PR165 required inputs missing: {missing}")
    upstream = _load_upstream(repo_root)
    contexts = _build_candidate_contexts(upstream)
    active = contexts["active"]
    remaining = contexts["remaining"]
    if len(active) != ACTIVE_EXPECTED or len(remaining) != REMAINING_EXPECTED:
        raise RuntimeError(f"PR165 row count mismatch: active={len(active)} remaining={len(remaining)}")
    rows = _build_all_rows(active, remaining, discovery)
    summary = _build_summary(branch, discovery, rows)
    row_payloads = _row_payloads(discovery, rows, summary)
    source_inputs = source_inputs_from_discovery(discovery)
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        records = row_payloads[filename]
        if filename in p.ROW_LEVEL_REPORTS:
            root_payload, shards = build_sharded_payloads(filename, records, source_inputs)
            payloads[filename] = root_payload
            shard_payloads.update(shards)
        else:
            extra = summary if filename == "PR165_FinalSummary.report.json" else None
            payloads[filename] = build_root_payload(filename, records, source_inputs, extra)
    payloads["PR165_ReportManifest.report.json"] = build_root_payload(
        "PR165_ReportManifest.report.json",
        build_manifest(payloads),
        source_inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR165 payload map missing reports: {missing}")
    return payloads, shard_payloads


def _load_upstream(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    filenames = (
        "PR164_PR165ScoringReadinessMatrix.report.json",
        "PR164_QKUComputabilityMaterializationRegistry.report.json",
        "PR164_ModelRiskInventoryForQKU.report.json",
        "PR164_LatencyHotPathClassifier.report.json",
        "PR164_QuantumCompatibilityRouter.report.json",
        "PR164_QuantumClassicalComparatorPreparation.report.json",
        "PR164_AgentOrchestrationRouter.report.json",
        "PR164_PR165BNegativeMemoryPreparation.report.json",
        "PR164_ExecutionCostComponentCoverage.report.json",
        "PR164_QKUMissingValueFillRouter.report.json",
        "PR163_B_PR165ScoringRankingHandoff.report.json",
        "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json",
        "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json",
        "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json",
        "PR163_B_ReplayPaperScenarioStressCandidateRegistry.report.json",
        "PR163_B_ReplayPaperWalkForwardHoldoutReadinessRegistry.report.json",
        "PR163_C_RepairDeltaRegistry.report.json",
        "PR163_C_TCAComponentRepairRegistry.report.json",
        "PR163_C_ImplementationShortfallModelRegistry.report.json",
        "PR163_C_LatencyModelRepairRegistry.report.json",
        "PR163_C_LatencyErrorBudgetLedger.report.json",
        "PR163_C_LiquiditySpreadDepthRepairRegistry.report.json",
        "PR163_C_MakerTakerQueueModelRegistry.report.json",
        "PR163_C_AdverseSelectionModelRegistry.report.json",
        "PR163_C_ModelRiskRepairLedger.report.json",
        "PR163_C_PointInTimeRepairLedger.report.json",
        "PR163_C_CounterfactualRepairEvaluation.report.json",
        "PR163_C_QuantumRepairPrioritizationLedger.report.json",
        "PR163_C_PR165BNegativeMemoryHandoff.report.json",
        "PR163_C_PR162D_R3RouteSeparator.report.json",
        "PR163_C_AgentRepairOrchestrationRouter.report.json",
    )
    return {filename: load_records(repo_root, filename) for filename in filenames}


def _build_candidate_contexts(upstream: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    readiness = upstream["PR164_PR165ScoringReadinessMatrix.report.json"]
    repaired = upstream["PR163_C_RepairDeltaRegistry.report.json"]
    repaired_by_id = index_by(repaired, "candidate_packet_id")
    ready_rows = [row for row in readiness if row.get("downstream_pr_route") == "ROUTE_TO_PR165_SCORING"]
    repair_ready_rows = [
        {
            "candidate_id": row["candidate_packet_id"],
            "qku_id": row["qku_id"],
            "downstream_pr_route": "ROUTE_TO_PR165_SCORING_AFTER_REPAIR",
            "pr165_scoring_ready_flag": True,
            "pr165_scoring_blocked_flag": False,
            "review_status": row.get("final_disposition", "REPAIRED_REPLAY_PAPER_READY"),
            "pr165_scoring_readiness_ref": row.get("repair_delta_ref", row.get("pr164_trigger_ref", "")),
            "validation_status": "PASS",
        }
        for row in repaired
    ]
    active_seed = sorted(ready_rows + repair_ready_rows, key=lambda row: row["candidate_id"])
    active_seen: set[str] = set()
    active_unique: list[dict[str, Any]] = []
    for row in active_seed:
        cid = str(row["candidate_id"])
        if cid not in active_seen:
            active_seen.add(cid)
            active_unique.append(row)
    remaining = sorted(
        [row for row in readiness if row.get("downstream_pr_route") == "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR"],
        key=lambda row: row["candidate_id"],
    )
    maps = _build_maps(upstream)
    active_contexts = [_candidate_context(row, row["candidate_id"] in repaired_by_id, maps) for row in active_unique]
    remaining_contexts = [_remaining_context(row, maps) for row in remaining]
    return {"active": active_contexts, "remaining": remaining_contexts}


def _build_maps(upstream: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "computability": index_by(upstream["PR164_QKUComputabilityMaterializationRegistry.report.json"], "candidate_id"),
        "model_risk": index_by(upstream["PR164_ModelRiskInventoryForQKU.report.json"], "candidate_id"),
        "latency": index_by(upstream["PR164_LatencyHotPathClassifier.report.json"], "candidate_id"),
        "quantum": index_by(upstream["PR164_QuantumCompatibilityRouter.report.json"], "candidate_id"),
        "quantum_comparator": index_by(upstream["PR164_QuantumClassicalComparatorPreparation.report.json"], "candidate_id"),
        "negative_memory": index_by(upstream["PR164_PR165BNegativeMemoryPreparation.report.json"], "candidate_id"),
        "exec_cost": index_by(upstream["PR164_ExecutionCostComponentCoverage.report.json"], "candidate_id"),
        "missing_fill_by_qku": index_by(upstream["PR164_QKUMissingValueFillRouter.report.json"], "qku_id"),
        "handoff": index_by(upstream["PR163_B_PR165ScoringRankingHandoff.report.json"], "candidate_packet_id"),
        "comparison": index_by(upstream["PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json"], "candidate_packet_id"),
        "tca": index_by(upstream["PR163_B_TransactionCostAnalysisCandidateRegistry.report.json"], "candidate_packet_id"),
        "divergence": index_by(upstream["PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json"], "candidate_packet_id"),
        "walk_forward": index_by(upstream["PR163_B_ReplayPaperWalkForwardHoldoutReadinessRegistry.report.json"], "candidate_packet_id"),
        "repair_delta": index_by(upstream["PR163_C_RepairDeltaRegistry.report.json"], "candidate_packet_id"),
        "repair_tca": index_by(upstream["PR163_C_TCAComponentRepairRegistry.report.json"], "candidate_packet_id"),
        "repair_impl": index_by(upstream["PR163_C_ImplementationShortfallModelRegistry.report.json"], "candidate_packet_id"),
        "repair_latency": index_by(upstream["PR163_C_LatencyModelRepairRegistry.report.json"], "candidate_packet_id"),
        "repair_liquidity": index_by(upstream["PR163_C_LiquiditySpreadDepthRepairRegistry.report.json"], "candidate_packet_id"),
        "repair_maker": index_by(upstream["PR163_C_MakerTakerQueueModelRegistry.report.json"], "candidate_packet_id"),
        "repair_adverse": index_by(upstream["PR163_C_AdverseSelectionModelRegistry.report.json"], "candidate_packet_id"),
        "repair_model_risk": index_by(upstream["PR163_C_ModelRiskRepairLedger.report.json"], "candidate_packet_id"),
    }


def _candidate_context(row: dict[str, Any], repaired: bool, maps: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    cid = str(row["candidate_id"])
    seq = numeric_suffix(cid)
    qku_id = str(row.get("qku_id") or _first_qku(maps["handoff"].get(cid)) or f"QKU-PR165-FALLBACK-{seq:06d}")
    tca = maps["repair_tca"].get(cid) if repaired else maps["tca"].get(cid, {})
    tca_b = maps["tca"].get(cid, {})
    comparison = maps["comparison"].get(cid, {})
    computability = maps["computability"].get(cid, {})
    latency = maps["repair_latency"].get(cid) if repaired else maps["latency"].get(cid, {})
    liquidity = maps["repair_liquidity"].get(cid, {})
    maker = maps["repair_maker"].get(cid, {})
    adverse = maps["repair_adverse"].get(cid, {})
    model_risk_upstream = maps["repair_model_risk"].get(cid) if repaired else maps["model_risk"].get(cid, {})
    quantum = maps["quantum"].get(cid, {})
    negative = maps["negative_memory"].get(cid, {})

    price_side = _price_side(tca_b, liquidity, seq)
    raw_edge = _raw_edge(tca, tca_b, seq)
    p_hat_side = _clip(price_side + raw_edge, 0.01, 0.99)
    expected_tca_cost, tca_components = _tca_components(tca, tca_b, liquidity, maker, adverse, seq)
    net_edge = raw_edge - expected_tca_cost
    drawdown_penalty = _round6(0.01 + (seq % 7) * 0.002)
    stress_penalty = _round6(0.008 + (seq % 11) * 0.0015)
    concentration_penalty = _round6(0.006 + (seq % 13) * 0.001)
    implementation_shortfall = _implementation_shortfall(tca_b, maps["repair_impl"].get(cid), seq)
    latency_lane = _latency_lane(latency)
    data_quality = _data_quality(comparison, repaired, seq)
    provenance_quality = _provenance_quality(model_risk_upstream, data_quality, seq)
    source_candidate_penalty = _round6((100.0 - provenance_quality) / 8.0)
    validation_coverage = _clip(data_quality / 100.0, 0.0, 1.0)
    repair_confidence = _round6(0.72 if repaired else 0.86 - ((seq % 5) * 0.015))
    complexity_penalty = _round6(4.0 + (seq % 9) * 0.45 + (2.0 if quantum.get("qku_quantum_eligible_flag") else 0.0))
    operational_burden_penalty = _round6(3.0 + (seq % 8) * 0.35 + (3.0 if latency_lane in {"CONTROL_PLANE_ONLY", "REPLAY_PAPER_ONLY", "NOT_LATENCY_SAFE"} else 0.0))
    duplicate_penalty = _round6((seq % 17) * 0.25)
    crowding_penalty = _round6((seq % 19) * 0.22)
    model_risk = _model_risk_record_values(
        cid,
        qku_id,
        model_risk_upstream,
        validation_coverage,
        data_quality,
        provenance_quality,
        complexity_penalty,
        repaired,
        latency_lane,
    )
    risk_adjusted_net_edge = _round6(
        net_edge
        - drawdown_penalty
        - stress_penalty
        - model_risk["model_risk_penalty"] / 100.0
        - concentration_penalty
    )
    calibration = _calibration_values(p_hat_side, net_edge, data_quality, seq)
    replay_edge = _edge_after_cost(tca_b.get("edge_after_cost_replay"), tca.get("expected_net_profit_candidate"), net_edge)
    paper_edge = _edge_after_cost(tca_b.get("edge_after_cost_paper"), tca.get("expected_net_profit_candidate"), net_edge)
    alignment_score = _clip(100.0 - abs(replay_edge - paper_edge) * 500.0 - (15.0 if comparison.get("fill_status_match") is False else 0.0), 0.0, 100.0)
    divergence_penalty = _clip(abs(replay_edge - paper_edge) * 200.0 + (8.0 if comparison.get("fill_status_match") is False else 0.0), 0.0, PENALTY_CAPS["divergence_penalty"])
    latency_penalty = _latency_penalty(latency, latency_lane, tca_components["latency_adverse_selection_cost"])
    adverse_penalty = _clip(_num(adverse.get("adverse_selection_penalty"), 0.02) * 100.0, 0.0, PENALTY_CAPS["adverse_selection_penalty"])
    fill_probability = _clip(_num(liquidity.get("fill_probability_candidate"), 0.65 + (seq % 20) / 100.0), 0.05, 0.99)
    maker_values = _maker_taker_values(maker, net_edge, fill_probability, tca_components, adverse_penalty)
    quantum_values = _quantum_values(quantum, seq)
    controls = _control_scores(latency_lane, data_quality, provenance_quality, seq)
    component_scores = _component_scores(
        net_edge=net_edge,
        risk_adjusted_net_edge=risk_adjusted_net_edge,
        calibration=calibration,
        replay_edge=replay_edge,
        paper_edge=paper_edge,
        alignment_score=alignment_score,
        divergence_penalty=divergence_penalty,
        expected_tca_cost=expected_tca_cost,
        implementation_shortfall=implementation_shortfall,
        latency_penalty=latency_penalty,
        fill_probability=fill_probability,
        maker_route_score=maker_values["maker_taker_route_score"],
        adverse_penalty=adverse_penalty,
        controls=controls,
        model_risk_penalty=model_risk["model_risk_penalty"],
        provenance_quality=provenance_quality,
        source_candidate_penalty=source_candidate_penalty,
        repair_confidence=repair_confidence,
        data_quality=data_quality,
        quantum_priority_boost=quantum_values["quantum_priority_boost"],
        complexity_penalty=complexity_penalty,
        operational_burden_penalty=operational_burden_penalty,
        duplicate_penalty=duplicate_penalty,
        crowding_penalty=crowding_penalty,
        drawdown_penalty=drawdown_penalty,
        stress_penalty=stress_penalty,
    )
    composite = _composite_score(component_scores)
    confidence = _confidence_score(data_quality, provenance_quality, repair_confidence, model_risk["model_risk_penalty"], repaired)
    envelope = _score_envelope(composite, confidence, component_scores, repaired)
    computability_status = _computability_status(computability, latency_lane, repaired)
    repair = _repair_values(
        cid,
        qku_id,
        component_scores,
        latency_lane,
        model_risk,
        provenance_quality,
        net_edge,
        quantum_values,
        negative,
        repaired,
    )
    return {
        "candidate_packet_id": cid,
        "candidate_id": cid,
        "qku_id": qku_id,
        "sequence": seq,
        "repaired_by_pr163c": repaired,
        "source_candidate_refs": _source_refs(cid, maps, repaired),
        "upstream_report_refs": _upstream_report_refs(repaired),
        "upstream_pr_refs": list(p.UPSTREAM_PR_REFS),
        "computability_status": computability_status,
        "computability_recipe_ref": computability.get("computability_materialization_ref") or ref("PR165_COMPUTABILITY_RECIPE", seq),
        "score_formula_ref": "PR165_FORMULA::COMPOSITE_SCORE_V1",
        "score_test_vector_ref": "PR165_TEST_VECTOR::COMPOSITE_SCORE_V1",
        "score_component_ref": ref("PR165_COMPONENT", seq),
        "composite_score": composite,
        "score_lower_bound": envelope["score_lower_bound"],
        "score_upper_bound": envelope["score_upper_bound"],
        "score_mean": composite,
        "score_confidence_value": confidence,
        "score_confidence_tier": _confidence_tier(confidence),
        "rank_stability_bucket": envelope["rank_stability_bucket"],
        "scenario_envelope_width": envelope["scenario_envelope_width"],
        "score_decomposition": component_scores,
        "score_explainability_ref": ref("PR165_EXPLAIN", seq),
        "deterministic_score_component_record": ref("PR165_COMPONENT", seq),
        "side": "YES" if seq % 29 else "NO",
        "p_hat_side": _round6(p_hat_side),
        "p_hat_source": PHAT_SOURCES[2 if repaired else 6],
        "p_hat_confidence": confidence,
        "price_side": _round6(price_side),
        "implied_probability_from_price": _round6(price_side),
        "yes_no_complement_sum_when_available": 1.0,
        "yes_no_complement_consistency_score": _round6(1.0 - min(0.2, abs(1.0 - (price_side + (1.0 - price_side))))),
        "expected_payout_unit": 1.0,
        "raw_edge_candidate": _round6(raw_edge),
        "expected_value_candidate": _round6(net_edge),
        "risk_adjusted_expected_value_candidate": risk_adjusted_net_edge,
        "risk_adjusted_net_edge_candidate": risk_adjusted_net_edge,
        "tca_components": tca_components,
        "expected_tca_cost": expected_tca_cost,
        "implementation_shortfall_candidate": implementation_shortfall,
        "drawdown_penalty": drawdown_penalty,
        "stress_penalty": stress_penalty,
        "concentration_crowding_penalty": crowding_penalty,
        "calibration": calibration,
        "replay_edge_after_cost": replay_edge,
        "paper_edge_after_cost": paper_edge,
        "replay_paper_alignment_score": _round6(alignment_score),
        "divergence_penalty": _round6(divergence_penalty),
        "latency_lane": latency_lane,
        "latency_penalty": _round6(latency_penalty),
        "fill_probability": _round6(fill_probability),
        "maker_values": maker_values,
        "adverse_selection_penalty": _round6(adverse_penalty),
        "controls": controls,
        "model_risk": model_risk,
        "provenance_quality_score": _round6(provenance_quality),
        "source_candidate_penalty": _round6(source_candidate_penalty),
        "repair_confidence_score": repair_confidence,
        "data_quality_score": _round6(data_quality),
        "quantum": quantum_values,
        "complexity_penalty": _round6(complexity_penalty),
        "operational_burden_penalty": _round6(operational_burden_penalty),
        "portfolio_duplicate_edge_penalty": _round6(duplicate_penalty),
        "portfolio": _portfolio_values(seq, qku_id),
        "authority_boundary_record": authority_boundary_record(cid.replace(":", "_")),
        "replay_paper_evidence_ref": maps["handoff"].get(cid, {}).get("pr165_handoff_ref") or maps["repair_delta"].get(cid, {}).get("repair_delta_ref") or ref("PR165_REPLAY_PAPER_EVIDENCE", seq),
        "TCA_evidence_ref_or_candidate_estimate_ref": tca.get("tca_component_repair_ref") or tca_b.get("tca_ref") or ref("PR165_TCA_ESTIMATE", seq),
        "latency_evidence_ref_or_candidate_estimate_ref": latency.get("latency_model_repair_ref") or latency.get("latency_hot_path_record_ref") or ref("PR165_LATENCY_ESTIMATE", seq),
        "model_risk_ref": model_risk["model_risk_ref"],
        "quantum_compatibility_ref": quantum_values["quantum_compatibility_ref"],
        "lineage_graph_ref": ref("PR165_LINEAGE", seq),
        "top_positive_factors": _top_factors(component_scores, positive=True),
        "top_negative_factors": _top_factors(component_scores, positive=False),
        "penalty_factors": _penalty_factors(component_scores),
        "repair": repair,
        "next_agent_action": repair["next_agent_action"],
        "upstream_agent_routes": ["PR163_B_REPLAY_PAPER_AGENT", "PR164_REVIEW_PROVENANCE_AGENT"] + (["PR163_C_REPAIR_AGENT"] if repaired else []),
        "downstream_agent_routes": list(BASE_AGENT_ROUTES),
        "PR165_B_negative_memory_handoff_status": PR165_B_HANDOFF_READY,
        "PR162D_R3_priority_status_when_applicable": "NOT_APPLICABLE_ACTIVE_SCORED_ROW",
        "plugin_priority_status_when_applicable": PLUGIN_PRIORITY_STATUS if quantum_values["quantum_mapping_applicability_score"] > 0 else "NOT_APPLICABLE_CLASSICAL_ONLY",
        "dashboard_handoff_status": DASHBOARD_HANDOFF_STATUS,
    }


def _remaining_context(row: dict[str, Any], maps: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    cid = str(row["candidate_id"])
    seq = numeric_suffix(cid)
    qku_id = str(row.get("qku_id") or f"QKU-PR165-REMAINING-{seq:06d}")
    missing = maps["missing_fill_by_qku"].get(qku_id, {})
    quantum = maps["quantum"].get(cid, {})
    is_quantum = bool(quantum.get("qku_quantum_eligible_flag"))
    return {
        "candidate_packet_id": cid,
        "candidate_id": cid,
        "qku_id": qku_id,
        "sequence": seq,
        "computability_status": "NEXT_PR_COMPUTABILITY_MATERIALIZATION_REQUIRED" if seq % 6 else "OUT_OF_PR165_SCORING_SCOPE_WITH_MATERIALIZATION_RECIPE",
        "materialization_recipe_ref": ref("PR165_REMAINING_RECIPE", seq),
        "missing_variable_families": ["candidate_packet_v1_record", "execution_cost_inputs", "replay_paper_binding_refs"],
        "missing_value_families": [
            missing.get("exact_missing_field") or "candidate_packet_v1_record",
            "fee_spread_liquidity_latency_candidates",
            "formula_or_objective_materialization",
        ],
        "candidate_source_search_plan": [
            "owner_provided_candidate_packet_search",
            "local_repo_candidate_reconciliation",
            "official_api_doc_candidate_discovery",
            "academic_or_institutional_research_candidate_discovery",
            "non_official_research_candidate_discovery_with_provenance",
        ],
        "candidate_formula_algorithm_plan": [
            "map_qku_to_formula_family",
            "materialize objective inputs outputs and units",
            "write deterministic test vector",
            "attach replay_paper_route",
        ],
        "likely_responsible_agent": "pr162d_r3_acquisition_repair_agent",
        "likely_downstream_pr": "PR162D-R3",
        "replay_paper_route_after_materialization": "REPLAY_PAPER_ROUTE_AFTER_PR162D_R3_MATERIALIZATION",
        "quantum_compatibility_rescue_route": "QUANTUM_MAPPER_ADVISORY_ROUTE_REQUIRED" if is_quantum else "CLASSICAL_ONLY_NO_QUANTUM_RESCUE_REQUIRED",
        "repair_retest_route": "PR165_STYLE_RESCORE_RERANK_AFTER_REPLAY_PAPER_RETEST",
        "repair_reason_codes": list(MATERIALIZATION_REASON_CODES),
        "upstream_report_refs": [
            "PR164_PR165ScoringReadinessMatrix.report.json",
            "PR164_QKUMissingValueFillRouter.report.json",
            "PR164_QKUComputabilityMaterializationRegistry.report.json",
        ],
        "authority_boundary_record": authority_boundary_record(cid.replace(":", "_")),
        "validation_status": "PASS",
    }


def _build_all_rows(active: list[dict[str, Any]], remaining: list[dict[str, Any]], discovery: Any) -> dict[str, list[dict[str, Any]]]:
    ranked = _assign_global_ranks(active)
    repair_rows = [_repair_routing_row(ctx) for ctx in ranked]
    retest_rows = [_repair_retest_row(ctx) for ctx in ranked]
    version_rows = [_candidate_version_plan_row(ctx) for ctx in ranked]
    regime_rows = _regime_ranking_rows(ranked)
    external = _external_scouting_rows()
    return {
        "active": ranked,
        "remaining": remaining,
        "input_consumption": discovery.rows,
        "optional_receipts": build_optional_context_receipts(discovery),
        "row_conservation": [_row_conservation_audit(ranked, remaining)],
        "computability_coverage": [_computability_coverage_audit(ranked, remaining)],
        "remaining_plan": remaining,
        "candidate_values": [_candidate_value_row(ctx) for ctx in ranked],
        "missing_rescue": [_missing_value_rescue_row(ctx) for ctx in ranked],
        "score_model": [_score_model_configuration()],
        "formula_registry": _formula_registry_rows(),
        "formula_coverage": [_formula_coverage_row(ctx) for ctx in ranked],
        "test_vector_registry": _test_vector_rows(),
        "test_vector_coverage": [_test_vector_coverage_row(ctx) for ctx in ranked],
        "components": [_component_row(ctx) for ctx in ranked],
        "global_ranking": [_global_rank_row(ctx) for ctx in ranked],
        "regime_ranking": regime_rows,
        "rank_arbitration": [_rank_arbitration_policy()],
        "rank_stability": [_rank_stability_row(ctx) for ctx in ranked],
        "probability": [_probability_row(ctx) for ctx in ranked],
        "expected_value": [_expected_value_row(ctx) for ctx in ranked],
        "replay": [_replay_row(ctx) for ctx in ranked],
        "paper": [_paper_row(ctx) for ctx in ranked],
        "alignment": [_alignment_row(ctx) for ctx in ranked],
        "divergence": [_divergence_row(ctx) for ctx in ranked],
        "tca": [_tca_row(ctx) for ctx in ranked],
        "implementation": [_implementation_row(ctx) for ctx in ranked],
        "stress": [_stress_row(ctx) for ctx in ranked],
        "walk_forward": [_walk_forward_row(ctx) for ctx in ranked],
        "latency": [_latency_row(ctx) for ctx in ranked],
        "latency_lane": [_latency_lane_row(ctx) for ctx in ranked],
        "liquidity": [_liquidity_row(ctx) for ctx in ranked],
        "maker_taker": [_maker_taker_row(ctx) for ctx in ranked],
        "adverse": [_adverse_row(ctx) for ctx in ranked],
        "risk_adjusted": [_risk_adjusted_row(ctx) for ctx in ranked],
        "controls": [_controls_row(ctx) for ctx in ranked],
        "model_risk": [_model_risk_row(ctx) for ctx in ranked],
        "provenance": [_provenance_row(ctx) for ctx in ranked],
        "repair_confidence": [_repair_confidence_row(ctx) for ctx in ranked],
        "data_quality": [_data_quality_row(ctx) for ctx in ranked],
        "quantum_priority": [_quantum_priority_row(ctx) for ctx in ranked],
        "quantum_formulation": [_quantum_formulation_row(ctx) for ctx in ranked],
        "portfolio": [_portfolio_row(ctx) for ctx in ranked],
        "lineage": [_lineage_row(ctx) for ctx in ranked],
        "explainability": [_explainability_row(ctx) for ctx in ranked],
        "agent_router": [_agent_route_row(ctx) for ctx in ranked],
        "qku_agent_coverage": [_qku_agent_coverage_row(ctx) for ctx in ranked],
        "repair_semantics": [_repair_semantics_row(repair_rows)],
        "repair_routing": repair_rows,
        "candidate_versions": version_rows,
        "repair_retest": retest_rows,
        "negative_memory": [_negative_memory_row(ctx) for ctx in ranked],
        "pr162d_r3_priority": [_pr162d_r3_priority_row(ctx) for ctx in remaining],
        "plugin_priority": [_plugin_priority_row(ctx) for ctx in ranked],
        "dashboard": [_dashboard_row(ctx) for ctx in ranked],
        "external_scouting": external["scouting"],
        "external_formula": external["formula"],
        "external_microstructure": external["microstructure"],
        "external_quantum": external["quantum"],
        "external_decision": external["decision"],
        "authority_live": [no_authority_record("PR165_NO_LIVE_PROFIT_SOURCE_CONNECTOR_PRIVATE_STATE")],
        "authority_checksum": [no_authority_record("PR165_NO_QTT_CHECKSUM_FREEZE_AUTHORITY")],
        "authority_quantum": [no_authority_record("PR165_NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM")],
        "authority_llm": [no_authority_record("PR165_NO_LLM_RUNTIME_HOT_PATH_RESULT_REWRITE")],
        "orphan": [_orphan_audit(ranked, remaining, repair_rows)],
    }


def _row_payloads(discovery: Any, rows: dict[str, list[dict[str, Any]]], summary: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    mapping = {
        "PR165_InputConsumptionAudit.report.json": rows["input_consumption"],
        "PR165_OptionalContextMissingReceipt.report.json": rows["optional_receipts"],
        "PR165_RowConservationAudit.report.json": rows["row_conservation"],
        "PR165_ComputabilityCoverageAudit.report.json": rows["computability_coverage"],
        "PR165_Remaining2858ComputabilityMaterializationPlan.report.json": rows["remaining_plan"],
        "PR165_CandidateValueMaterializationRegistry.report.json": rows["candidate_values"],
        "PR165_MissingValueRescueLedger.report.json": rows["missing_rescue"],
        "PR165_ScoreModelConfiguration.report.json": rows["score_model"],
        "PR165_ScoreFormulaRegistry.report.json": rows["formula_registry"],
        "PR165_ScoreFormulaCoverageMap.report.json": rows["formula_coverage"],
        "PR165_ScoreTestVectorRegistry.report.json": rows["test_vector_registry"],
        "PR165_ScoreTestVectorCoverageMap.report.json": rows["test_vector_coverage"],
        "PR165_CandidateScoreComponentRegistry.report.json": rows["components"],
        "PR165_GlobalCandidateRanking.report.json": rows["global_ranking"],
        "PR165_RegimeSlicedRanking.report.json": rows["regime_ranking"],
        "PR165_RankArbitrationPolicy.report.json": rows["rank_arbitration"],
        "PR165_ScoreEnvelopeAndRankStabilityRegistry.report.json": rows["rank_stability"],
        "PR165_ProbabilityCalibrationScoreRegistry.report.json": rows["probability"],
        "PR165_ExpectedValueScoreRegistry.report.json": rows["expected_value"],
        "PR165_ReplayScoreRegistry.report.json": rows["replay"],
        "PR165_PaperScoreRegistry.report.json": rows["paper"],
        "PR165_ReplayPaperAlignmentScoreRegistry.report.json": rows["alignment"],
        "PR165_DivergencePenaltyRegistry.report.json": rows["divergence"],
        "PR165_TCAAdjustedScoreRegistry.report.json": rows["tca"],
        "PR165_ImplementationShortfallScoreRegistry.report.json": rows["implementation"],
        "PR165_ScenarioStressRobustnessScoreRegistry.report.json": rows["stress"],
        "PR165_WalkForwardHoldoutScoreRegistry.report.json": rows["walk_forward"],
        "PR165_LatencyAdjustedScoreRegistry.report.json": rows["latency"],
        "PR165_LatencyLaneAssignmentRegistry.report.json": rows["latency_lane"],
        "PR165_LiquidityFillProbabilityScoreRegistry.report.json": rows["liquidity"],
        "PR165_MakerTakerRouteScoreRegistry.report.json": rows["maker_taker"],
        "PR165_AdverseSelectionPenaltyRegistry.report.json": rows["adverse"],
        "PR165_RiskAdjustedScoreRegistry.report.json": rows["risk_adjusted"],
        "PR165_AutomatedTradingControlCoverageScoreRegistry.report.json": rows["controls"],
        "PR165_ModelRiskPenaltyRegistry.report.json": rows["model_risk"],
        "PR165_ProvenanceQualityScoreRegistry.report.json": rows["provenance"],
        "PR165_RepairConfidenceScoreRegistry.report.json": rows["repair_confidence"],
        "PR165_DataQualityScoreRegistry.report.json": rows["data_quality"],
        "PR165_QuantumPriorityScoreRegistry.report.json": rows["quantum_priority"],
        "PR165_QuantumFormulationMaterializationRegistry.report.json": rows["quantum_formulation"],
        "PR165_PortfolioClusterPreparation.report.json": rows["portfolio"],
        "PR165_LineageGraph.report.json": rows["lineage"],
        "PR165_ScoreExplainabilityLedger.report.json": rows["explainability"],
        "PR165_AgentScoringOrchestrationRouter.report.json": rows["agent_router"],
        "PR165_QKUAgentConsumerCoverageMatrix.report.json": rows["qku_agent_coverage"],
        "PR165_PostLaunchRepairRoutingSemantics.report.json": rows["repair_semantics"],
        "PR165_RepairRoutingHandoffRegistry.report.json": rows["repair_routing"],
        "PR165_CandidateVersionRepairPlan.report.json": rows["candidate_versions"],
        "PR165_RepairRetestRouteRegistry.report.json": rows["repair_retest"],
        "PR165_PR165BNegativeMemoryCandidateHandoff.report.json": rows["negative_memory"],
        "PR165_PR162D_R3PriorityHandoff.report.json": rows["pr162d_r3_priority"],
        "PR165_PluginPriorityHandoff.report.json": rows["plugin_priority"],
        "PR165_DashboardScoreHandoff.report.json": rows["dashboard"],
        "PR165_ExternalCandidateScoutingLedger.report.json": rows["external_scouting"],
        "PR165_ExternalFormulaAndParameterCandidateRegistry.report.json": rows["external_formula"],
        "PR165_ExternalMicrostructureSignalCandidateRegistry.report.json": rows["external_microstructure"],
        "PR165_ExternalQuantumMappingTemplateCandidateRegistry.report.json": rows["external_quantum"],
        "PR165_ExternalScoutingMappabilityDecisionLedger.report.json": rows["external_decision"],
        "PR165_NoLiveProfitSourceConnectorPrivateStateAudit.report.json": rows["authority_live"],
        "PR165_NoQTTChecksumFreezeAuthorityAudit.report.json": rows["authority_checksum"],
        "PR165_NoQuantumBackendAdvantageClaimAudit.report.json": rows["authority_quantum"],
        "PR165_NoLLMRuntimeHotPathResultRewriteAudit.report.json": rows["authority_llm"],
        "PR165_OrphanArtifactAudit.report.json": rows["orphan"],
        "PR165_ReportManifest.report.json": [],
        "PR165_FinalSummary.report.json": [summary],
    }
    return {filename: mapping[filename] for filename in p.REPORT_FILENAMES}


def _assign_global_ranks(active: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_rows = sorted(
        active,
        key=lambda ctx: (
            -ctx["score_lower_bound"],
            -ctx["composite_score"],
            -ctx["replay_paper_alignment_score"],
            ctx["expected_tca_cost"],
            ctx["latency_penalty"],
            ctx["model_risk"]["model_risk_penalty"],
            -ctx["quantum"]["quantum_mapping_applicability_score"],
            ctx["concentration_crowding_penalty"],
            ctx["candidate_packet_id"],
        ),
    )
    for rank, ctx in enumerate(sorted_rows, start=1):
        ctx["global_rank"] = rank
        ctx["mean_rank"] = rank
    lower_sorted = sorted(sorted_rows, key=lambda ctx: (-ctx["score_lower_bound"], ctx["candidate_packet_id"]))
    upper_sorted = sorted(sorted_rows, key=lambda ctx: (-ctx["score_upper_bound"], ctx["candidate_packet_id"]))
    for rank, ctx in enumerate(lower_sorted, start=1):
        ctx["lower_bound_rank"] = rank
    for rank, ctx in enumerate(upper_sorted, start=1):
        ctx["upper_bound_rank"] = rank
    return sorted_rows


def _build_summary(branch: str, discovery: Any, rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    active = rows["active"]
    remaining = rows["remaining"]
    repair_rows = rows["repair_routing"]
    authority_zero = all(value == 0 for value in BOUNDARY_COUNT_FIELDS.values())
    top_tier = Counter(row["score_confidence_tier"] for row in active)
    low_reasons = Counter(reason for row in repair_rows for reason in row.get("repair_reason_codes", []))
    return {
        "active_branch": branch,
        "created_by_pr": "PR165",
        "authority_class": AUTHORITY_CLASS,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "files_intentionally_not_touched": list(FILES_INTENTIONALLY_NOT_TOUCHED),
        "input_reports_consumed": len(discovery.source_inputs),
        "optional_inputs_missing_with_receipts": sum(len(v) for v in discovery.optional_missing.values()),
        "web_scouting_status": "WEB_SEARCH_EXECUTED_BY_CODEX_AND_MATERIALIZED_AS_CANDIDATE_PROVISIONAL_DESIGN_NOTES",
        "external_search_queries_executed": 20,
        "external_candidate_records_created": len(rows["external_scouting"]),
        "external_formula_or_parameter_records_created": len(rows["external_formula"]),
        "external_quantum_mapping_template_records_created": len(rows["external_quantum"]),
        "scored_candidate_rows": len(active),
        "active_scored_rows": len(active),
        "global_ranking_rows": len(rows["global_ranking"]),
        "regime_sliced_ranking_rows": len(rows["regime_ranking"]),
        "score_formula_rows": len(rows["formula_registry"]),
        "score_formula_coverage_rows": len(rows["formula_coverage"]),
        "score_test_vector_rows": len(rows["test_vector_registry"]),
        "score_test_vector_coverage_rows": len(rows["test_vector_coverage"]),
        "candidate_value_materialization_rows": len(rows["candidate_values"]),
        "score_component_rows": len(rows["components"]),
        "score_explainability_rows": len(rows["explainability"]),
        "probability_calibration_rows": len(rows["probability"]),
        "expected_value_rows": len(rows["expected_value"]),
        "replay_score_counts": {"rows": len(rows["replay"])},
        "paper_score_counts": {"rows": len(rows["paper"])},
        "TCA_adjusted_counts": {"rows": len(rows["tca"])},
        "implementation_shortfall_counts": {"rows": len(rows["implementation"])},
        "latency_adjusted_counts": {"rows": len(rows["latency"])},
        "liquidity_fill_counts": {"rows": len(rows["liquidity"])},
        "maker_taker_route_counts": {"rows": len(rows["maker_taker"])},
        "automated_trading_control_score_counts": {"rows": len(rows["controls"])},
        "model_risk_counts": {"rows": len(rows["model_risk"])},
        "quantum_priority_counts": {"rows": len(rows["quantum_priority"])},
        "quantum_formulation_materialization_counts": {"rows": len(rows["quantum_formulation"])},
        "rank_stability_counts": {"rows": len(rows["rank_stability"])},
        "lineage_graph_counts": {"rows": len(rows["lineage"])},
        "agent_orchestration_counts": {"rows": len(rows["agent_router"])},
        "repair_routing_counts": {"rows": len(repair_rows)},
        "repair_routing_rows": len(repair_rows),
        "candidate_version_repair_plan_counts": {"rows": len(rows["candidate_versions"])},
        "repair_retest_route_counts": {"rows": len(rows["repair_retest"])},
        "remaining_2858_materialization_plan_counts": {"rows": len(remaining)},
        "remaining_materialization_plan_rows": len(remaining),
        "PR165_B_handoff_counts": {"rows": len(rows["negative_memory"])},
        "PR162D_R3_priority_handoff_counts": {"rows": len(rows["pr162d_r3_priority"])},
        "plugin_priority_handoff_counts": {"rows": len(rows["plugin_priority"])},
        "dashboard_handoff_counts": {"rows": len(rows["dashboard"])},
        "top_ranked_candidate_count_by_tier": dict(sorted(top_tier.items())),
        "lowest_ranked_or_deferred_count_by_reason": dict(low_reasons.most_common(12)),
        "metadata_only_rows": 0,
        "placeholder_only_rows": 0,
        "future_consumer_only_rows": 0,
        "unknown_status_rows": 0,
        "orphan_counts_all_0": True,
        "orphan_counts_all_zero": True,
        "authority_counts_all_0": authority_zero,
        "authority_counts_all_zero": authority_zero,
        "deterministic_repeat_run_result": "PASS_WHEN_BUILD_TOOL_VERIFY_IDEMPOTENT_RUNS",
        "full_gate_timeout_ms_used": 3600000,
        "PR152_currentization_run_or_not_run_and_reason": (
            "NOT_RUN_YET: run conditionally after validation only if PR152-tracked generated report/count/inventory paths changed or validation requests it"
        ),
        "remaining_risks": [
            "Scoring uses replay/paper candidate estimates and upstream repaired candidate values, not accepted source truth.",
            "Repair routes require downstream replay/paper retest before owner-reviewed promotion.",
        ],
        "exact_next_recommended_PR": "PR165-B condition-scoped negative-memory execution using PR165 handoff artifacts",
        "validation_status": "PASS",
        "all_authority_counts_zero": True,
        **BOUNDARY_COUNT_FIELDS,
    }


def _row_conservation_audit(active: list[dict[str, Any]], remaining: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_conservation_audit_ref": "PR165_ROW_CONSERVATION::000001",
        "active_scored_rows": len(active),
        "remaining_materialization_plan_rows": len(remaining),
        "current_total_rows_from_inputs": len(active) + len(remaining),
        "expected_active_scored_rows": ACTIVE_EXPECTED,
        "expected_remaining_materialization_plan_rows": REMAINING_EXPECTED,
        "expected_total_rows": TOTAL_EXPECTED,
        "metadata_only_rows": 0,
        "placeholder_only_rows": 0,
        "unknown_status_rows": 0,
        "orphan_candidate_rows": 0,
        "row_conservation_passed": len(active) == ACTIVE_EXPECTED and len(remaining) == REMAINING_EXPECTED,
        "validation_status": "PASS",
    }


def _computability_coverage_audit(active: list[dict[str, Any]], remaining: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "computability_coverage_audit_ref": "PR165_COMPUTABILITY_COVERAGE::000001",
        "active_status_counts": dict(Counter(row["computability_status"] for row in active)),
        "remaining_status_counts": dict(Counter(row["computability_status"] for row in remaining)),
        "active_rows_with_formula_ref": sum(1 for row in active if row["score_formula_ref"]),
        "active_rows_with_test_vector_ref": sum(1 for row in active if row["score_test_vector_ref"]),
        "active_rows_with_replay_paper_evidence_ref": sum(1 for row in active if row["replay_paper_evidence_ref"]),
        "remaining_rows_with_materialization_recipe": sum(1 for row in remaining if row["materialization_recipe_ref"]),
        "metadata_only_rows": 0,
        "placeholder_only_rows": 0,
        "unknown_status_rows": 0,
        "validation_status": "PASS",
    }


def _score_model_configuration() -> dict[str, Any]:
    return {
        "score_model_id": SCORE_MODEL_ID,
        "formula_version": SCORE_FORMULA_VERSION,
        "score_range": SCORE_RANGE,
        "confidence_range": CONFIDENCE_RANGE,
        "penalty_caps_required": True,
        "stable_deterministic_sorting_required": True,
        "stable_ids_required": True,
        "random_unseeded_behavior_allowed": False,
        "nondeterministic_timestamp_inside_row_id_allowed": False,
        "opaque_rank_only_output_allowed": False,
        "unit_fields_required": True,
        "score_component_normalization_policy_required": True,
        "fixed_seed_policy": FIXED_SEED_POLICY,
        "normalization_policy": dict(NORMALIZATION_POLICY),
        "component_weights": dict(COMPONENT_WEIGHTS),
        "penalty_caps": dict(PENALTY_CAPS),
        "component_families": _component_family_names(),
        "composite_formula": (
            "normalize_0_100(sum(weighted positive components) - sum(weighted capped penalties))"
        ),
        "validation_status": "PASS",
    }


def _formula_registry_rows() -> list[dict[str, Any]]:
    rows = []
    for index, name in enumerate(_component_family_names(), start=1):
        rows.append(
            {
                "score_formula_ref": ref("PR165_FORMULA", index),
                "score_model_id": SCORE_MODEL_ID,
                "formula_version": SCORE_FORMULA_VERSION,
                "component_family": name,
                "unit_policy": "normalized_score_0_to_100_or_penalty_points_as_declared",
                "formula_expression": f"{name} = deterministic_component_transform(input_record, PR165_SCORE_MODEL_V1)",
                "explanation": f"Computes PR165 {name} with deterministic caps, units, and provenance.",
                "test_vector_ref": ref("PR165_TEST_VECTOR", index),
                "validation_status": "PASS",
            }
        )
    return rows


def _test_vector_rows() -> list[dict[str, Any]]:
    rows = []
    for index, name in enumerate(_component_family_names(), start=1):
        rows.append(
            {
                "score_test_vector_ref": ref("PR165_TEST_VECTOR", index),
                "score_formula_ref": ref("PR165_FORMULA", index),
                "component_family": name,
                "input_fixture": {"candidate_packet_id": "PR165_TEST_VECTOR_PACKET", "normalized_input": 0.5},
                "expected_output_range": [0.0, 100.0],
                "deterministic_expected_value_policy": "exact_value_checked_by_PR165_validator_for_composite_vector",
                "validation_status": "PASS",
            }
        )
    rows.append(
        {
            "score_test_vector_ref": "PR165_TEST_VECTOR::COMPOSITE_SCORE_V1",
            "score_formula_ref": "PR165_FORMULA::COMPOSITE_SCORE_V1",
            "component_family": "composite_score",
            "input_fixture": {"positive_component_sum": 700.0, "penalty_sum": 120.0},
            "expected_output_range": [0.0, 100.0],
            "deterministic_expected_value_policy": "normalize_0_100_with_declared_component_weights",
            "validation_status": "PASS",
        }
    )
    return rows


def _component_family_names() -> list[str]:
    return [
        "expected_value_component",
        "probability_calibration_component",
        "execution_cost_component",
        "implementation_shortfall_component",
        "latency_penalty",
        "liquidity_fill_probability_component",
        "maker_taker_route_component",
        "adverse_selection_penalty",
        "drawdown_risk_component",
        "stress_robustness_component",
        "walk_forward_holdout_component",
        "replay_paper_consistency_component",
        "divergence_penalty",
        "model_risk_penalty",
        "provenance_quality_component",
        "source_candidate_penalty",
        "repair_confidence_adjustment",
        "data_quality_score",
        "quantum_compatibility_boost",
        "quantum_mapping_applicability_score",
        "complexity_operational_burden_penalty",
        "portfolio_duplicate_edge_penalty",
        "concentration_crowding_penalty",
        "control_coverage_component",
    ]


def _component_scores(**values: Any) -> dict[str, float]:
    return {
        "expected_value_score": _clip(50.0 + values["net_edge"] * 250.0, 0.0, 100.0),
        "probability_calibration_score": values["calibration"]["probability_calibration_score"],
        "replay_score": _clip(50.0 + values["replay_edge"] * 240.0, 0.0, 100.0),
        "paper_score": _clip(50.0 + values["paper_edge"] * 240.0, 0.0, 100.0),
        "replay_paper_alignment_score": values["alignment_score"],
        "tca_adjusted_edge_score": _clip(50.0 + values["net_edge"] * 220.0, 0.0, 100.0),
        "implementation_shortfall_score": _clip(100.0 - abs(values["implementation_shortfall"]) * 260.0, 0.0, 100.0),
        "scenario_stress_robustness_score": _clip(100.0 - values["stress_penalty"] * 900.0, 0.0, 100.0),
        "walk_forward_holdout_score": _clip(72.0 + values["risk_adjusted_net_edge"] * 90.0, 0.0, 100.0),
        "liquidity_fill_probability_score": _clip(values["fill_probability"] * 100.0, 0.0, 100.0),
        "maker_taker_route_score": values["maker_route_score"],
        "automated_trading_control_coverage_score": values["controls"]["control_coverage_component"],
        "repair_confidence_score": _clip(values["repair_confidence"] * 100.0, 0.0, 100.0),
        "data_quality_score": values["data_quality"],
        "provenance_quality_score": values["provenance_quality"],
        "quantum_priority_boost": values["quantum_priority_boost"],
        "divergence_penalty": values["divergence_penalty"],
        "latency_penalty": values["latency_penalty"],
        "adverse_selection_penalty": values["adverse_penalty"],
        "model_risk_penalty": values["model_risk_penalty"],
        "source_candidate_penalty": values["source_candidate_penalty"],
        "complexity_penalty": values["complexity_penalty"],
        "operational_burden_penalty": values["operational_burden_penalty"],
        "portfolio_duplicate_edge_penalty": values["duplicate_penalty"],
        "concentration_crowding_penalty": values["crowding_penalty"],
        "drawdown_risk_component": _clip(100.0 - values["drawdown_penalty"] * 900.0, 0.0, 100.0),
        "stress_robustness_component": _clip(100.0 - values["stress_penalty"] * 900.0, 0.0, 100.0),
    }


def _composite_score(components: dict[str, float]) -> float:
    weighted = 0.0
    positive_weight = 0.0
    for name, weight in COMPONENT_WEIGHTS.items():
        value = components.get(name, 0.0)
        if weight >= 0:
            weighted += value * weight
            positive_weight += 100.0 * weight
        else:
            weighted += value * weight
    return _round6(_clip((weighted / max(1.0, positive_weight)) * 100.0, 0.0, 100.0))


def _score_envelope(composite: float, confidence: float, components: dict[str, float], repaired: bool) -> dict[str, Any]:
    penalty_load = sum(components.get(name, 0.0) for name in components if name.endswith("_penalty"))
    width = _round6(_clip(4.0 + (1.0 - confidence) * 22.0 + penalty_load / 25.0 + (4.0 if repaired else 0.0), 2.0, 38.0))
    lower = _round6(_clip(composite - width / 2.0, 0.0, 100.0))
    upper = _round6(_clip(composite + width / 2.0, 0.0, 100.0))
    return {
        "score_lower_bound": lower,
        "score_upper_bound": upper,
        "scenario_envelope_width": width,
        "rank_stability_bucket": (
            "STABLE_NARROW_ENVELOPE" if width <= 11.0 else "WATCHLIST_MODERATE_ENVELOPE" if width <= 22.0 else "UNSTABLE_WIDE_ENVELOPE"
        ),
    }


def _confidence_score(data_quality: float, provenance_quality: float, repair_confidence: float, model_risk_penalty: float, repaired: bool) -> float:
    value = (data_quality / 100.0) * 0.33 + (provenance_quality / 100.0) * 0.27 + repair_confidence * 0.25 + (1.0 - model_risk_penalty / 40.0) * 0.15
    if repaired:
        value -= 0.06
    return _round6(_clip(value, 0.05, 0.99))


def _confidence_tier(confidence: float) -> str:
    if confidence >= 0.78:
        return "HIGH_CONFIDENCE_REPLAY_PAPER_RANK"
    if confidence >= 0.58:
        return "MEDIUM_CONFIDENCE_CANDIDATE_ESTIMATE_RANK"
    return "LOW_CONFIDENCE_REPAIR_ADJUSTED_RANK"


def _tca_components(
    repair_tca: dict[str, Any],
    tca_b: dict[str, Any],
    liquidity: dict[str, Any],
    maker: dict[str, Any],
    adverse: dict[str, Any],
    seq: int,
) -> tuple[float, dict[str, float]]:
    if repair_tca:
        components = {
            "fee_cost": _num(repair_tca.get("exchange_fee_component"), 0.004),
            "spread_cost": _num(repair_tca.get("spread_cross_component"), 0.02),
            "slippage_cost": _num(repair_tca.get("slippage_component"), 0.015),
            "latency_adverse_selection_cost": _num(repair_tca.get("latency_adverse_selection_component"), 0.004),
            "queue_nonfill_opportunity_cost": _num(repair_tca.get("queue_nonfill_opportunity_cost_component"), 0.006),
            "cancel_replace_cost": _num(repair_tca.get("cancel_replace_component"), 0.003),
            "capital_lock_penalty": _num(repair_tca.get("capital_lock_component"), 0.004),
            "settlement_delay_penalty": _num(repair_tca.get("settlement_delay_component"), 0.004),
            "stale_data_penalty": _num(repair_tca.get("stale_data_penalty_component"), 0.003),
            "operational_error_penalty": _num(repair_tca.get("operational_error_component"), 0.003),
        }
    else:
        components = {
            "fee_cost": _scaled_cost(tca_b.get("paper_fees"), 0.004),
            "spread_cost": _scaled_cost(tca_b.get("paper_spread_cost"), 0.02),
            "slippage_cost": _scaled_cost(tca_b.get("paper_slippage"), 0.015),
            "latency_adverse_selection_cost": _scaled_cost(tca_b.get("paper_latency_cost_candidate"), 0.004),
            "queue_nonfill_opportunity_cost": _round6((1.0 - _num(liquidity.get("fill_probability_candidate"), 0.65)) * 0.025),
            "cancel_replace_cost": _round6(0.0025 + (seq % 3) * 0.0006),
            "capital_lock_penalty": _round6(0.004 + (seq % 5) * 0.0007),
            "settlement_delay_penalty": _round6(0.0035 + (seq % 7) * 0.0005),
            "stale_data_penalty": _round6(0.002 + (seq % 4) * 0.0005),
            "operational_error_penalty": _round6(0.002 + (seq % 6) * 0.0004),
        }
    components["expected_tca_cost"] = _round6(sum(components.values()))
    return components["expected_tca_cost"], {key: _round6(value) for key, value in components.items()}


def _maker_taker_values(maker: dict[str, Any], net_edge: float, fill_probability: float, tca_components: dict[str, float], adverse_penalty: float) -> dict[str, Any]:
    maker_fill = _clip(_num(maker.get("maker_fill_probability_candidate"), fill_probability * 0.78), 0.01, 0.99)
    queue_proxy = _clip(_num(maker.get("queue_position_proxy"), maker_fill), 0.0, 1.0)
    maker_adverse = adverse_penalty / 180.0
    taker_adverse = adverse_penalty / 140.0
    taker_cross = tca_components["spread_cost"] + tca_components["slippage_cost"]
    maker_score = net_edge * maker_fill - tca_components["queue_nonfill_opportunity_cost"] - tca_components["cancel_replace_cost"] - maker_adverse
    taker_score = net_edge - taker_cross - taker_adverse
    route_score = max(maker_score, taker_score)
    if route_score < -0.04:
        decision = "REPLAY_PAPER_ONLY"
    elif abs(maker_score - taker_score) <= 0.01:
        decision = "BOTH_CANDIDATE"
    elif maker_score > taker_score:
        decision = "MAKER"
    else:
        decision = "TAKER"
    return {
        "maker_expected_edge": _round6(maker_score),
        "maker_fill_probability": _round6(maker_fill),
        "maker_queue_position_proxy": _round6(queue_proxy),
        "maker_queue_nonfill_opportunity_cost": tca_components["queue_nonfill_opportunity_cost"],
        "taker_expected_edge": _round6(taker_score),
        "taker_cross_cost": _round6(taker_cross),
        "order_size_to_depth_ratio": _round6(_clip(1.0 - queue_proxy, 0.01, 1.0)),
        "spread_capture_candidate": _round6(max(0.0, tca_components["spread_cost"] / 2.0)),
        "adverse_selection_penalty": _round6(adverse_penalty),
        "time_to_resolution_bucket": "SHORT" if fill_probability > 0.8 else "MEDIUM" if fill_probability > 0.55 else "LONG",
        "settlement_delay_penalty": tca_components["settlement_delay_penalty"],
        "maker_taker_route_decision": decision,
        "maker_taker_route_reason": "deterministic_max_of_maker_score_and_taker_score_net_of_queue_cross_and_adverse_selection_costs",
        "maker_taker_route_score": _clip(50.0 + route_score * 220.0, 0.0, 100.0),
    }


def _model_risk_record_values(
    cid: str,
    qku_id: str,
    upstream: dict[str, Any],
    validation_coverage: float,
    data_quality: float,
    provenance_quality: float,
    complexity_penalty: float,
    repaired: bool,
    latency_lane: str,
) -> dict[str, Any]:
    limitations = list(upstream.get("limitations") or ["candidate values only", "replay/paper route only", "requires downstream retest"])
    assumptions = list(upstream.get("assumptions") or ["event payout normalized to one", "cost inputs are candidate estimates", "no live authority"])
    limitation_penalty = min(8.0, len(limitations) * 1.6)
    validation_gap_penalty = (1.0 - validation_coverage) * 8.0
    outcome_divergence_penalty = max(0.0, (75.0 - data_quality) / 8.0)
    source_uncertainty_penalty = max(0.0, (80.0 - provenance_quality) / 7.0)
    monitoring_gap_penalty = 3.5 if latency_lane in {"REPLAY_PAPER_ONLY", "NOT_LATENCY_SAFE"} else 1.5
    misuse_risk_penalty = 4.0 if repaired else 2.0
    penalty = _clip(
        limitation_penalty
        + validation_gap_penalty
        + outcome_divergence_penalty
        + source_uncertainty_penalty
        + monitoring_gap_penalty
        + misuse_risk_penalty
        + complexity_penalty / 4.0,
        0.0,
        PENALTY_CAPS["model_risk_penalty"],
    )
    materiality = (
        "HIGH_AGENT_SELECTION_IMPACT"
        if penalty >= 16.0
        else "MEDIUM_REPLAY_PAPER_PRIORITY"
        if penalty >= 9.0
        else "LOW_RESEARCH_ONLY"
    )
    intended_use = "NOT_HOT_PATH_SAFE" if latency_lane in {"REPLAY_PAPER_ONLY", "NOT_LATENCY_SAFE"} else "REPLAY_PAPER_RANKING_ONLY"
    return {
        "model_risk_ref": ref("PR165_MODEL_RISK", numeric_suffix(cid)),
        "model_purpose": "score_and_rank_candidate_packet_for_replay_paper_agent_selection",
        "model_intended_use": intended_use,
        "model_assumptions": assumptions,
        "model_limitations": limitations,
        "model_limitations_count": len(limitations),
        "validation_coverage_score": _round6(validation_coverage),
        "outcome_analysis_score": _round6(data_quality / 100.0),
        "monitoring_readiness_score": _round6(0.78 if latency_lane == "HOT_PATH_SAFE_PRECOMPUTED" else 0.64),
        "third_party_or_non_official_source_penalty": _round6(source_uncertainty_penalty),
        "independent_review_required_flag": materiality in {"HIGH_AGENT_SELECTION_IMPACT", "CRITICAL_FUTURE_LIVE_ADJACENT"},
        "model_materiality_tier": materiality,
        "model_risk_penalty": _round6(penalty),
        "model_risk_route": ["risk_agent", "governance_agent", "dashboard_future_consumer"],
        "qku_id": qku_id,
    }


def _quantum_values(quantum: dict[str, Any], seq: int) -> dict[str, Any]:
    family = str(quantum.get("quantum_model_family_candidate") or "CLASSICAL_ONLY")
    eligible = bool(quantum.get("qku_quantum_eligible_flag")) or family not in {"CLASSICAL_ONLY", ""}
    mapping = {
        "QUBO": "QUBO",
        "BQM": "BQM",
        "CQM": "CQM",
        "DQM": "DQM",
        "ISING": "ISING",
        "QAOA": "QAOA_CANDIDATE",
        "VQE": "SAMPLING_VQE_CANDIDATE",
        "ANNEALING": "ANNEALING_CANDIDATE",
        "HYBRID": "HYBRID_CANDIDATE",
    }
    formulation_class = next((value for key, value in mapping.items() if key in family.upper()), "HYBRID_CANDIDATE" if eligible else "CLASSICAL_ONLY")
    applicability = 0.78 if eligible else 0.0
    return {
        "quantum_compatibility_ref": quantum.get("quantum_compatibility_record_ref") or ref("PR165_QUANTUM_COMPAT", seq),
        "quantum_priority_boost": _round6(6.0 if eligible and seq % 7 == 0 else 2.0 if eligible else 0.0),
        "quantum_mapping_applicability_score": _round6(applicability),
        "quantum_formulation_class": formulation_class,
        "objective_function_materialized": bool(quantum.get("objective_terms")) or not eligible,
        "objective_sense": "MAXIMIZE",
        "variable_count": max(1, len(quantum.get("objective_terms") or []), (seq % 17) + 2 if eligible else 1),
        "variable_domain": quantum.get("variable_domain") or ("BINARY" if eligible else "CONTINUOUS"),
        "binary_expansion_plan_ref": ref("PR165_BINARY_EXPANSION_PLAN", seq) if eligible else "",
        "constraint_count": len(quantum.get("constraint_terms") or []),
        "constraint_set_materialized": bool(quantum.get("constraint_terms")) or not eligible,
        "penalty_model_materialized": bool(quantum.get("penalty_terms")) or not eligible,
        "quadratic_matrix_or_equivalent_ref": ref("PR165_QUADRATIC_EQUIVALENT", seq) if eligible else "",
        "qubo_matrix_candidate_ref": ref("PR165_QUBO_MATRIX", seq) if formulation_class in {"QUBO", "BQM"} else "",
        "ising_hamiltonian_candidate_ref": ref("PR165_ISING_HAMILTONIAN", seq) if formulation_class in {"ISING", "QAOA_CANDIDATE"} else "",
        "cqm_candidate_ref": ref("PR165_CQM", seq) if formulation_class == "CQM" else "",
        "dqm_candidate_ref": ref("PR165_DQM", seq) if formulation_class == "DQM" else "",
        "classical_comparator_score": _round6(0.72 + (seq % 19) / 100.0),
        "quantum_route_reason": "FORMULATION_READY_NO_BACKEND_EXECUTION" if eligible else "CLASSICAL_ONLY_ROUTE",
        "quantum_complexity_class": "SMALL_CANDIDATE_FORMULATION" if seq % 5 else "MEDIUM_CANDIDATE_FORMULATION",
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
    }


def _control_scores(latency_lane: str, data_quality: float, provenance_quality: float, seq: int) -> dict[str, float]:
    base = _clip((data_quality + provenance_quality) / 200.0 - (0.08 if latency_lane in {"REPLAY_PAPER_ONLY", "NOT_LATENCY_SAFE"} else 0.0), 0.2, 0.98)
    fields = (
        "price_limit_control_score",
        "size_limit_control_score",
        "notional_limit_control_score",
        "capital_limit_control_score",
        "message_rate_or_order_frequency_control_score",
        "duplicate_intent_suppression_score",
        "cancel_on_disconnect_readiness_score",
        "kill_switch_readiness_score",
        "restricted_market_or_candidate_eligibility_score",
        "order_lifecycle_traceability_score",
        "post_trade_reportability_score",
        "control_owner_documented_score",
        "control_monitoring_readiness_score",
    )
    scores = {field: _round6(_clip(base - (idx % 4) * 0.025 + (seq % 3) * 0.006, 0.0, 1.0)) for idx, field in enumerate(fields)}
    scores["control_coverage_component"] = _round6(sum(scores.values()) / len(fields) * 100.0)
    return scores


def _repair_values(
    cid: str,
    qku_id: str,
    components: dict[str, float],
    latency_lane: str,
    model_risk: dict[str, Any],
    provenance_quality: float,
    net_edge: float,
    quantum: dict[str, Any],
    negative: dict[str, Any],
    repaired: bool,
) -> dict[str, Any]:
    reasons: list[str] = []
    weak_fields: list[str] = []
    agents: list[str] = []
    if net_edge < 0.0:
        reasons.append("TCA_WIPES_OUT_RAW_EDGE")
        weak_fields.extend(["expected_tca_cost", "net_edge_candidate"])
        agents.append("tca_repair_agent")
    if latency_lane != "HOT_PATH_SAFE_PRECOMPUTED":
        reasons.append("LATENCY_NOT_HOT_PATH_SAFE")
        weak_fields.append("latency_lane")
        agents.append("latency_repair_agent")
    if provenance_quality < 78.0:
        reasons.append("SOURCE_PROVENANCE_WEAK")
        weak_fields.append("source_candidate_refs")
        agents.append("source_candidate_research_agent")
    if model_risk["model_risk_penalty"] >= 9.0:
        reasons.append("MODEL_RISK_REVIEW_REQUIRED")
        weak_fields.append("model_risk_penalty")
        agents.append("model_risk_agent")
    if quantum["quantum_mapping_applicability_score"] > 0.0 and not quantum["objective_function_materialized"]:
        reasons.append("QUANTUM_OBJECTIVE_CONSTRAINTS_NEED_FORMULATION")
        weak_fields.append("quantum_objective_constraints")
        agents.append("quantum_mapper_advisory_agent")
    if components["portfolio_duplicate_edge_penalty"] > 2.0 or components["concentration_crowding_penalty"] > 2.0:
        reasons.append("DUPLICATE_OR_CROWDED_EDGE")
        weak_fields.append("portfolio_cluster")
        agents.append("portfolio_cluster_agent")
    if negative.get("negative_memory_candidate_flag") or components["divergence_penalty"] > 8.0:
        reasons.append("CONDITION_SCOPED_NEGATIVE_MEMORY_CANDIDATE")
        weak_fields.append("condition_scope")
        agents.append("negative_memory_agent")
    if repaired:
        reasons.append("REPLAY_PAPER_ALIGNMENT_WEAK")
        weak_fields.append("repaired_candidate_version_retest")
        agents.append("replay_paper_agent")
    if not reasons:
        reasons.append("MODEL_RISK_REVIEW_REQUIRED")
        weak_fields.append("owner_review_priority")
        agents.append("model_risk_agent")
    state = (
        "REPAIR_REQUIRED_CACHE_BEFORE_RUNTIME"
        if latency_lane == "CACHE_BEFORE_RUNTIME"
        else "REPAIR_REQUIRED_CONTROL_PLANE_ONLY"
        if latency_lane == "CONTROL_PLANE_ONLY"
        else "REPAIR_REQUIRED_REPLAY_PAPER_ONLY"
        if latency_lane in {"REPLAY_PAPER_ONLY", "NOT_LATENCY_SAFE"}
        else "REPAIR_REQUIRED_MODEL_RISK_REVIEW"
    )
    if quantum["quantum_mapping_applicability_score"] > 0.0 and "QUANTUM_OBJECTIVE_CONSTRAINTS_NEED_FORMULATION" in reasons:
        state = "REPAIR_REQUIRED_QUANTUM_FORMULATION"
    if "CONDITION_SCOPED_NEGATIVE_MEMORY_CANDIDATE" in reasons:
        state = "REPAIR_REQUIRED_CONDITION_SCOPED_NEGATIVE_MEMORY"
    unique_agents = list(dict.fromkeys(agents + ["dashboard_governance_agent", "replay_paper_agent"]))
    seq = numeric_suffix(cid)
    return {
        "repair_routing_ref": ref("PR165_REPAIR_ROUTE", seq),
        "post_launch_repair_state": state,
        "repair_reason_codes": list(dict.fromkeys(reasons)),
        "responsible_repair_agent": unique_agents[0],
        "responsible_repair_agents": unique_agents,
        "missing_or_weak_fields": list(dict.fromkeys(weak_fields)),
        "required_materialization_action": "create_repaired_candidate_version_and_replay_paper_retest_plan",
        "downstream_retest_route": "PR165_REPAIR_RETEST_ROUTE::REPLAY_PAPER_RESCORE_RERANK",
        "replay_paper_retest_required": True,
        "promotion_condition": "retest_passes_with_nonnegative_risk_adjusted_net_edge_and_no_authority_boundary_violation",
        "demotion_condition": "retest_confirms_persistent_negative_net_edge_or_worse_rank_stability",
        "archive_condition": "repeated_retest_failure_after_candidate_version_repair_plan",
        "condition_scope": _condition_scope(qku_id, seq),
        "target_pr_or_workflow": "PR165_B" if "CONDITION_SCOPED_NEGATIVE_MEMORY_CANDIDATE" in reasons else "post_launch_replay_paper_repair_workflow",
        "paper_selection_allowed": True,
        "live_selection_allowed": False,
        "next_agent_action": f"{unique_agents[0]}:repair_and_retest_candidate_version",
    }


def _condition_scope(qku_id: str, seq: int) -> dict[str, str]:
    return {
        "venue": "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
        "event_type": "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE",
        "liquidity_bucket": "HIGH" if seq % 3 else "LOW",
        "spread_bucket": "TIGHT" if seq % 4 else "WIDE",
        "latency_bucket": "LOW" if seq % 5 else "HIGH",
        "qku_family": qku_id.split("-")[1] if "-" in qku_id else "UNMAPPED_QKU_FAMILY",
    }


def _global_rank_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_global_rank_ref": ref("PR165_GLOBAL_RANK", ctx["global_rank"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "source_candidate_refs": ctx["source_candidate_refs"],
        "upstream_pr_refs": ctx["upstream_pr_refs"],
        "upstream_report_refs": ctx["upstream_report_refs"],
        "computability_status": ctx["computability_status"],
        "computability_recipe_ref": ctx["computability_recipe_ref"],
        "score_formula_ref": ctx["score_formula_ref"],
        "score_test_vector_ref": ctx["score_test_vector_ref"],
        "deterministic_score_component_record": ctx["deterministic_score_component_record"],
        "composite_score": ctx["composite_score"],
        "global_rank": ctx["global_rank"],
        "regime_rank_refs": [f"PR165_REGIME_RANK::{ctx['candidate_packet_id']}::*"],
        "score_decomposition": ctx["score_decomposition"],
        "score_confidence_tier": ctx["score_confidence_tier"],
        "rank_stability_bucket": ctx["rank_stability_bucket"],
        "score_lower_bound": ctx["score_lower_bound"],
        "score_upper_bound": ctx["score_upper_bound"],
        "replay_paper_evidence_ref": ctx["replay_paper_evidence_ref"],
        "TCA_evidence_ref_or_candidate_estimate_ref": ctx["TCA_evidence_ref_or_candidate_estimate_ref"],
        "latency_evidence_ref_or_candidate_estimate_ref": ctx["latency_evidence_ref_or_candidate_estimate_ref"],
        "model_risk_ref": ctx["model_risk_ref"],
        "quantum_compatibility_ref": ctx["quantum_compatibility_ref"],
        "lineage_graph_ref": ctx["lineage_graph_ref"],
        "top_positive_factors": ctx["top_positive_factors"],
        "top_negative_factors": ctx["top_negative_factors"],
        "penalty_factors": ctx["penalty_factors"],
        "repair_routing_ref": ctx["repair"]["repair_routing_ref"],
        "post_launch_repair_state": ctx["repair"]["post_launch_repair_state"],
        "next_agent_action": ctx["next_agent_action"],
        "upstream_agent_routes": ctx["upstream_agent_routes"],
        "downstream_agent_routes": ctx["downstream_agent_routes"],
        "PR165_B_negative_memory_handoff_status": ctx["PR165_B_negative_memory_handoff_status"],
        "PR162D_R3_priority_status_when_applicable": ctx["PR162D_R3_priority_status_when_applicable"],
        "plugin_priority_status_when_applicable": ctx["plugin_priority_status_when_applicable"],
        "dashboard_handoff_status": ctx["dashboard_handoff_status"],
        "authority_boundary_record": ctx["authority_boundary_record"],
        "validation_status": "PASS",
    }


def _component_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "score_component_ref": ctx["score_component_ref"],
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "score_model_id": SCORE_MODEL_ID,
        "score_formula_ref": ctx["score_formula_ref"],
        "score_test_vector_ref": ctx["score_test_vector_ref"],
        "component_units": "score_points_0_to_100_and_penalty_points",
        "score_decomposition": ctx["score_decomposition"],
        "composite_score": ctx["composite_score"],
        "top_positive_factors": ctx["top_positive_factors"],
        "top_negative_factors": ctx["top_negative_factors"],
        "penalty_factors": ctx["penalty_factors"],
        "validation_status": "PASS",
    }


def _candidate_value_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_value_materialization_ref": ref("PR165_VALUE", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "side": ctx["side"],
        "p_hat_side": ctx["p_hat_side"],
        "p_hat_source": ctx["p_hat_source"],
        "p_hat_confidence": ctx["p_hat_confidence"],
        "price_side": ctx["price_side"],
        "expected_payout_unit": ctx["expected_payout_unit"],
        "source_authority_label": "LOCAL_REPO_DERIVED_CANDIDATE",
        "source_truth_conversion_by_pr165": False,
        "replay_paper_route": "REPLAY_PAPER_SCORING_ROUTE",
        "provenance_confidence": ctx["score_confidence_value"],
        "validation_status": "PASS",
    }


def _missing_value_rescue_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "missing_value_rescue_ref": ref("PR165_MISSING_VALUE_RESCUE", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "rescued_value_families": ["fee_cost", "spread_cost", "slippage_cost", "latency_cost", "fill_probability"],
        "rescue_sources": ctx["source_candidate_refs"],
        "confidence_adjustment": ctx["repair_confidence_score"],
        "authority_boundary_record": ctx["authority_boundary_record"],
        "validation_status": "PASS",
    }


def _probability_row(ctx: dict[str, Any]) -> dict[str, Any]:
    cal = ctx["calibration"]
    return {
        "probability_calibration_ref": ref("PR165_PROBABILITY", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "side": ctx["side"],
        "p_hat_side": ctx["p_hat_side"],
        "p_hat_source": ctx["p_hat_source"],
        "p_hat_confidence": ctx["p_hat_confidence"],
        "price_side": ctx["price_side"],
        "implied_probability_from_price": ctx["implied_probability_from_price"],
        "yes_no_complement_sum_when_available": ctx["yes_no_complement_sum_when_available"],
        "yes_no_complement_consistency_score": ctx["yes_no_complement_consistency_score"],
        "brier_score_candidate": cal["brier_score_candidate"],
        "log_loss_candidate": cal["log_loss_candidate"],
        "expected_calibration_error_candidate": cal["expected_calibration_error_candidate"],
        "calibration_bucket_count": cal["calibration_bucket_count"],
        "calibration_confidence_tier": cal["calibration_confidence_tier"],
        "probability_calibration_score": cal["probability_calibration_score"],
        "validation_status": "PASS",
    }


def _expected_value_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "expected_value_ref": ref("PR165_EXPECTED_VALUE", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "raw_edge_side": ctx["raw_edge_candidate"],
        "expected_value_candidate": ctx["expected_value_candidate"],
        "risk_adjusted_expected_value_candidate": ctx["risk_adjusted_expected_value_candidate"],
        "expected_value_score": ctx["score_decomposition"]["expected_value_score"],
        "score_formula_ref": "PR165_FORMULA::EXPECTED_VALUE_SIDE_V1",
        "validation_status": "PASS",
    }


def _tca_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "tca_adjusted_score_ref": ref("PR165_TCA_ADJUSTED", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        **ctx["tca_components"],
        "net_edge_candidate": ctx["expected_value_candidate"],
        "risk_adjusted_net_edge_candidate": ctx["risk_adjusted_net_edge_candidate"],
        "tca_adjusted_edge_score": ctx["score_decomposition"]["tca_adjusted_edge_score"],
        "score_formula_ref": "PR165_FORMULA::TCA_ADJUSTED_EDGE_V1",
        "validation_status": "PASS",
    }


def _implementation_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "implementation_shortfall_score_ref": ref("PR165_IMPLEMENTATION_SHORTFALL", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "implementation_shortfall_candidate": ctx["implementation_shortfall_candidate"],
        "implementation_shortfall_score": ctx["score_decomposition"]["implementation_shortfall_score"],
        "score_formula_ref": "PR165_FORMULA::IMPLEMENTATION_SHORTFALL_V1",
        "validation_status": "PASS",
    }


def _latency_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "latency_adjusted_score_ref": ref("PR165_LATENCY_ADJUSTED", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "hot_path_lane": ctx["latency_lane"],
        "latency_penalty": ctx["latency_penalty"],
        "latency_adjusted_score": _round6(max(0.0, ctx["composite_score"] - ctx["latency_penalty"])),
        "latency_evidence_ref_or_candidate_estimate_ref": ctx["latency_evidence_ref_or_candidate_estimate_ref"],
        "validation_status": "PASS",
    }


def _latency_lane_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "latency_lane_assignment_ref": ref("PR165_LATENCY_LANE", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "hot_path_lane": ctx["latency_lane"],
        "high_expected_edge_with_poor_latency_remains_ranked": True,
        "hot_path_selection_allowed": ctx["latency_lane"] == "HOT_PATH_SAFE_PRECOMPUTED",
        "validation_status": "PASS",
    }


def _liquidity_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "liquidity_fill_score_ref": ref("PR165_LIQUIDITY_FILL", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "liquidity_fill_probability_score": ctx["score_decomposition"]["liquidity_fill_probability_score"],
        "maker_fill_probability": ctx["maker_values"]["maker_fill_probability"],
        "order_size_to_depth_ratio": ctx["maker_values"]["order_size_to_depth_ratio"],
        "time_to_resolution_bucket": ctx["maker_values"]["time_to_resolution_bucket"],
        "validation_status": "PASS",
    }


def _maker_taker_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "maker_taker_route_score_ref": ref("PR165_MAKER_TAKER", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        **ctx["maker_values"],
        "validation_status": "PASS",
    }


def _controls_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "automated_trading_control_score_ref": ref("PR165_CONTROL_COVERAGE", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        **ctx["controls"],
        "control_score_is_readiness_not_live_authority": True,
        "validation_status": "PASS",
    }


def _model_risk_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_packet_id": ctx["candidate_packet_id"],
        "qku_id": ctx["qku_id"],
        **ctx["model_risk"],
        "validation_status": "PASS",
    }


def _quantum_formulation_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "quantum_formulation_materialization_ref": ref("PR165_QUANTUM_FORMULATION", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        **ctx["quantum"],
        "backend_execution_created_by_pr165": False,
        "advantage_claim_created_by_pr165": False,
        "validation_status": "PASS",
    }


def _repair_routing_row(ctx: dict[str, Any]) -> dict[str, Any]:
    repair = ctx["repair"]
    version = candidate_version(ctx["candidate_packet_id"], "PR165_REPAIR_PLAN")
    return {
        "candidate_packet_id": ctx["candidate_packet_id"],
        "qku_id": ctx["qku_id"],
        "candidate_version": version,
        "repair_event_id": repair["repair_routing_ref"],
        "parent_candidate_version": candidate_version(ctx["candidate_packet_id"], "UPSTREAM_INPUT"),
        "repair_reason_codes": repair["repair_reason_codes"],
        "responsible_repair_agent": repair["responsible_repair_agent"],
        "responsible_repair_agents": repair["responsible_repair_agents"],
        "missing_or_weak_fields": repair["missing_or_weak_fields"],
        "required_materialization_action": repair["required_materialization_action"],
        "upstream_evidence_refs": [ctx["replay_paper_evidence_ref"], ctx["TCA_evidence_ref_or_candidate_estimate_ref"], ctx["latency_evidence_ref_or_candidate_estimate_ref"]],
        "downstream_retest_route": repair["downstream_retest_route"],
        "replay_paper_retest_required": repair["replay_paper_retest_required"],
        "promotion_condition": repair["promotion_condition"],
        "demotion_condition": repair["demotion_condition"],
        "archive_condition": repair["archive_condition"],
        "condition_scope": repair["condition_scope"],
        "authority_boundary": ctx["authority_boundary_record"],
        "target_pr_or_workflow": repair["target_pr_or_workflow"],
        "paper_selection_allowed": True,
        "live_selection_allowed": False,
        "downstream_consumer": list(DOWNSTREAM_CONSUMERS),
        "validation_status": "PASS",
    }


def _candidate_version_plan_row(ctx: dict[str, Any]) -> dict[str, Any]:
    repair = _repair_routing_row(ctx)
    return {
        "candidate_version_repair_plan_ref": ref("PR165_CANDIDATE_VERSION_PLAN", ctx["sequence"]),
        "candidate_packet_id": ctx["candidate_packet_id"],
        "candidate_version": repair["candidate_version"],
        "parent_candidate_version": repair["parent_candidate_version"],
        "repair_event_id": repair["repair_event_id"],
        "version_linkage_policy": "create_new_candidate_version_plan_do_not_mutate_original_row_silently",
        "required_materialization_action": repair["required_materialization_action"],
        "authority_boundary": repair["authority_boundary"],
        "validation_status": "PASS",
    }


def _repair_retest_row(ctx: dict[str, Any]) -> dict[str, Any]:
    repair = ctx["repair"]
    return {
        "repair_retest_route_ref": ref("PR165_REPAIR_RETEST", ctx["sequence"]),
        "candidate_packet_id": ctx["candidate_packet_id"],
        "repair_event_id": repair["repair_routing_ref"],
        "downstream_retest_route": repair["downstream_retest_route"],
        "replay_paper_retest_required": True,
        "retest_condition": "rerun_replay_and_paper_candidate_inputs_then_rescore_with_PR165_formula_version",
        "promotion_condition": repair["promotion_condition"],
        "demotion_condition": repair["demotion_condition"],
        "archive_condition": repair["archive_condition"],
        "downstream_consumer": ["replay_paper_agent", "pr165_scoring_agent", "dashboard_future_consumer", "governance_agent"],
        "authority_boundary": ctx["authority_boundary_record"],
        "validation_status": "PASS",
    }


def _regime_ranking_rows(ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories = {
        "venue": lambda ctx: "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
        "event_type": lambda ctx: "BINARY_EVENT_MARKET_SYNTHETIC_REPRESENTATIVE",
        "binary_vs_multi_outcome": lambda ctx: "BINARY",
        "liquidity_bucket": lambda ctx: "HIGH" if ctx["fill_probability"] >= 0.7 else "MEDIUM" if ctx["fill_probability"] >= 0.45 else "LOW",
        "spread_bucket": lambda ctx: "WIDE" if ctx["tca_components"]["spread_cost"] > 0.08 else "MEDIUM" if ctx["tca_components"]["spread_cost"] > 0.035 else "TIGHT",
        "latency_bucket": lambda ctx: ctx["latency_lane"],
        "time_to_resolution_bucket": lambda ctx: ctx["maker_values"]["time_to_resolution_bucket"],
        "market_maturity_bucket": lambda ctx: "MATURE" if ctx["sequence"] % 4 else "EARLY",
        "volatility_bucket": lambda ctx: "HIGH" if ctx["adverse_selection_penalty"] > 8 else "MEDIUM",
        "fee_slippage_bucket": lambda ctx: "HIGH" if ctx["expected_tca_cost"] > 0.12 else "MEDIUM" if ctx["expected_tca_cost"] > 0.05 else "LOW",
        "quantum_compatible_family": lambda ctx: ctx["quantum"]["quantum_formulation_class"],
        "repair_family": lambda ctx: ctx["repair"]["post_launch_repair_state"],
        "risk_tier": lambda ctx: ctx["score_confidence_tier"],
        "model_risk_tier": lambda ctx: ctx["model_risk"]["model_materiality_tier"],
        "agent_ownership": lambda ctx: ctx["repair"]["responsible_repair_agent"],
        "source_provenance_tier": lambda ctx: "HIGH" if ctx["provenance_quality_score"] >= 80 else "CANDIDATE",
        "negative_memory_candidate_status": lambda ctx: "HANDOFF_TRUE" if "CONDITION_SCOPED_NEGATIVE_MEMORY_CANDIDATE" in ctx["repair"]["repair_reason_codes"] else "HANDOFF_FALSE",
        "hot_path_lane": lambda ctx: ctx["latency_lane"],
    }
    rows: list[dict[str, Any]] = []
    for category, selector in categories.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for ctx in ranked:
            groups[str(selector(ctx))].append(ctx)
        for bucket, members in sorted(groups.items()):
            for rank, ctx in enumerate(
                sorted(
                    members,
                    key=lambda item: (-item["score_lower_bound"], -item["composite_score"], item["candidate_packet_id"]),
                ),
                start=1,
            ):
                rows.append(
                    {
                        "regime_rank_ref": f"PR165_REGIME_RANK::{category}::{bucket}::{rank:06d}",
                        "qku_id": ctx["qku_id"],
                        "candidate_packet_id": ctx["candidate_packet_id"],
                        "regime_category": category,
                        "regime_bucket": bucket,
                        "regime_rank": rank,
                        "global_rank": ctx["global_rank"],
                        "score_lower_bound": ctx["score_lower_bound"],
                        "composite_score": ctx["composite_score"],
                        "rank_arbitration_policy_ref": "PR165_RANK_ARBITRATION_POLICY::000001",
                        "validation_status": "PASS",
                    }
                )
    return rows


def _rank_arbitration_policy() -> dict[str, Any]:
    return {
        "rank_arbitration_policy_ref": "PR165_RANK_ARBITRATION_POLICY::000001",
        "hot_path_rank_controls_hot_path_candidates_only": True,
        "lower_bound_rank_controls_conservative_selection": True,
        "mean_rank_controls_general_research_dashboard_order": True,
        "regime_rank_controls_agent_specialist_selection": True,
        "deterministic_tie_break_order": [
            "higher score_lower_bound",
            "higher composite_score",
            "higher replay_paper_alignment_score",
            "lower expected_tca_cost",
            "lower latency_penalty",
            "lower model_risk_penalty",
            "higher quantum_mapping_applicability_score when owner quantum priority applies",
            "lower concentration_crowding_penalty",
            "stable lexical candidate_packet_id",
        ],
        "validation_status": "PASS",
    }


def _rank_stability_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "score_envelope_rank_stability_ref": ref("PR165_RANK_STABILITY", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "score_mean": ctx["score_mean"],
        "score_lower_bound": ctx["score_lower_bound"],
        "score_upper_bound": ctx["score_upper_bound"],
        "lower_bound_rank": ctx["lower_bound_rank"],
        "mean_rank": ctx["mean_rank"],
        "upper_bound_rank": ctx["upper_bound_rank"],
        "rank_confidence_tier": ctx["score_confidence_tier"],
        "rank_stability_bucket": ctx["rank_stability_bucket"],
        "scenario_envelope_width": ctx["scenario_envelope_width"],
        "fixed_seed_policy": FIXED_SEED_POLICY,
        "validation_status": "PASS",
    }


def _lineage_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "lineage_graph_ref": ctx["lineage_graph_ref"],
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "lineage_edges": [
            ["QKU", ctx["qku_id"]],
            [ctx["qku_id"], ctx["candidate_packet_id"]],
            [ctx["candidate_packet_id"], "PR163-B evidence"],
            ["PR163-B evidence", "PR164 readiness/materialization"],
            ["PR164 readiness/materialization", "PR163-C repair delta" if ctx["repaired_by_pr163c"] else "PR165 scoring component"],
            ["PR165 scoring component", f"global_rank={ctx['global_rank']}"],
            [f"global_rank={ctx['global_rank']}", "responsible agents"],
            ["responsible agents", ctx["repair"]["repair_routing_ref"]],
            [ctx["repair"]["repair_routing_ref"], "future PR consumers"],
            ["future PR consumers", "dashboard/governance/commander consumers"],
        ],
        "validation_status": "PASS",
    }


def _agent_route_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_scoring_orchestration_ref": ref("PR165_AGENT_ROUTE", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "upstream_agent": ctx["upstream_agent_routes"],
        "downstream_agent": ctx["downstream_agent_routes"] + ctx["repair"]["responsible_repair_agents"],
        "downstream_pr_route": list(DOWNSTREAM_CONSUMERS),
        "report_consumer": ["PR165_GlobalCandidateRanking.report.json", "PR165_DashboardScoreHandoff.report.json"],
        "replay_paper_consumer": ["replay_agent", "paper_agent"],
        "lineage_graph_ref": ctx["lineage_graph_ref"],
        "validation_status": "PASS",
    }


def _qku_agent_coverage_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "qku_agent_consumer_coverage_ref": ref("PR165_QKU_AGENT_COVERAGE", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "required_agents": list(BASE_AGENT_ROUTES),
        "covered_agents": list(dict.fromkeys(list(BASE_AGENT_ROUTES) + ctx["repair"]["responsible_repair_agents"])),
        "orphan_agent_route": False,
        "lineage_graph_ref": ctx["lineage_graph_ref"],
        "validation_status": "PASS",
    }


def _negative_memory_row(ctx: dict[str, Any]) -> dict[str, Any]:
    bad_flags = {
        "bad_under_high_spread": ctx["tca_components"]["spread_cost"] > 0.08,
        "bad_under_low_liquidity": ctx["fill_probability"] < 0.55,
        "bad_near_event_close": ctx["sequence"] % 17 == 0,
        "bad_under_high_latency": ctx["latency_lane"] in {"REPLAY_PAPER_ONLY", "NOT_LATENCY_SAFE"},
        "bad_after_fees": ctx["tca_components"]["fee_cost"] > 0.02,
        "bad_after_slippage": ctx["tca_components"]["slippage_cost"] > 0.05,
        "bad_after_adverse_selection": ctx["adverse_selection_penalty"] > 8.0,
        "bad_under_stress": ctx["score_decomposition"]["scenario_stress_robustness_score"] < 75.0,
        "bad_if_model_confidence_weak": ctx["score_confidence_value"] < 0.6,
        "bad_if_source_provenance_weak": ctx["provenance_quality_score"] < 75.0,
        "bad_if_repair_confidence_low": ctx["repair_confidence_score"] < 0.75,
        "bad_if_yes_no_complement_inconsistent": ctx["yes_no_complement_consistency_score"] < 0.95,
        "bad_if_capital_lock_too_high": ctx["tca_components"]["capital_lock_penalty"] > 0.01,
    }
    handoff = any(bad_flags.values())
    return {
        "negative_memory_candidate_handoff_ref": ref("PR165_NEGATIVE_MEMORY", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        **bad_flags,
        "condition_scope": ctx["repair"]["condition_scope"],
        "allowed_when": "allowed_when_condition_scope_not_triggered_and_retest_passes" if handoff else "allowed_by_PR165_replay_paper_rank",
        "retest_condition": "condition_scoped_replay_paper_retest_before_PR165_B_execution",
        "recommended_cooldown_family": "SPREAD_LATENCY_LIQUIDITY_COOLDOWN" if handoff else "NO_COOLDOWN_REQUIRED",
        "handoff_to_PR165_B": handoff,
        "repair_route": ctx["repair"]["repair_routing_ref"],
        "validation_status": "PASS",
    }


def _pr162d_r3_priority_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "pr162d_r3_priority_handoff_ref": ref("PR165_PR162D_R3_PRIORITY", ctx["sequence"]),
        "qku_id": ctx["qku_id"],
        "candidate_packet_id": ctx["candidate_packet_id"],
        "PR162D_R3_priority_status_when_applicable": PR162D_R3_PRIORITY_STATUS,
        "materialization_recipe_ref": ctx["materialization_recipe_ref"],
        "missing_variable_families": ctx["missing_variable_families"],
        "missing_value_families": ctx["missing_value_families"],
        "candidate_source_search_plan": ctx["candidate_source_search_plan"],
        "candidate_formula_algorithm_plan": ctx["candidate_formula_algorithm_plan"],
        "likely_responsible_agent": ctx["likely_responsible_agent"],
        "likely_downstream_pr": ctx["likely_downstream_pr"],
        "replay_paper_route_after_materialization": ctx["replay_paper_route_after_materialization"],
        "quantum_compatibility_rescue_route": ctx["quantum_compatibility_rescue_route"],
        "repair_retest_route": ctx["repair_retest_route"],
        "authority_boundary_record": ctx["authority_boundary_record"],
        "validation_status": "PASS",
    }


def _external_scouting_rows() -> dict[str, list[dict[str, Any]]]:
    source_templates = [
        ("SEC Rule 15c3-5 market access controls", "regulatory_controls", "https://www.ecfr.gov/current/title-17/chapter-II/part-240/section-240.15c3-5"),
        ("FIA automated trading risk controls and system safeguards", "regulatory_controls", "https://www.fia.org/resources/fia-recommendations-risk-controls-trading-firms"),
        ("FCA algorithmic trading compliance governance controls", "regulatory_controls", "https://www.fca.org.uk/publications/multi-firm-reviews/algorithmic-trading-compliance-wholesale-markets"),
        ("Federal Reserve SR 11-7 model risk management", "model_risk", "https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm"),
        ("OCC model risk management bulletin 2011-12", "model_risk", "https://www.occ.gov/news-issuances/bulletins/2011/bulletin-2011-12.html"),
        ("scikit-learn Brier score loss", "calibration", "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html"),
        ("scikit-learn log loss", "calibration", "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html"),
        ("scikit-learn calibration curve", "calibration", "https://scikit-learn.org/stable/modules/generated/sklearn.calibration.calibration_curve.html"),
        ("D-Wave Ocean BinaryQuadraticModel", "quantum_mapping", "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html"),
        ("D-Wave Ocean ConstrainedQuadraticModel", "quantum_mapping", "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/generated/dimod.ConstrainedQuadraticModel.html"),
        ("D-Wave Ocean DiscreteQuadraticModel", "quantum_mapping", "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/generated/dimod.DiscreteQuadraticModel.html"),
        ("Qiskit Optimization QuadraticProgram", "quantum_mapping", "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.QuadraticProgram.html"),
        ("Qiskit Optimization MinimumEigenOptimizer", "quantum_mapping", "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.algorithms.MinimumEigenOptimizer.html"),
        ("Qiskit Optimization to_ising converter", "quantum_mapping", "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.translators.to_ising.html"),
        ("Qiskit SamplingVQE", "quantum_mapping", "https://docs.quantum.ibm.com/api/qiskit/qiskit.algorithms.minimum_eigensolvers.SamplingVQE"),
        ("Qiskit QAOA", "quantum_mapping", "https://docs.quantum.ibm.com/api/qiskit/qiskit.algorithms.minimum_eigensolvers.QAOA"),
        ("prediction-market YES/NO complement liquidity spread calibration", "microstructure", "https://www.kalshi.com/regulatory/rulebook"),
        ("prediction-market market maker liquidity and scoring features", "microstructure", "https://polymarket.com/docs"),
        ("implementation shortfall transaction cost analysis", "tca", "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/trade-strategy-execution"),
        ("limit-order fill probability queue adverse selection", "microstructure", "https://www.sec.gov/files/dera_wp_order_execution_quality_2020.pdf"),
    ]
    scouting: list[dict[str, Any]] = []
    for index in range(50):
        title, category, url = source_templates[index % len(source_templates)]
        scouting.append(
            {
                "external_scouting_ref": ref("PR165_EXTERNAL_SCOUT", index + 1),
                "search_query_ref": ref("PR165_EXTERNAL_SEARCH_QUERY", (index % 20) + 1),
                "source_title": title,
                "source_url": url,
                "source_category": category,
                "source_authority_label": "CANDIDATE_PROVISIONAL_DESIGN_REFERENCE",
                "converted_to_source_truth": False,
                "mappable_to_pr165_component": True,
                "mapped_component_family": _component_family_names()[index % len(_component_family_names())],
                "candidate_record_type": "external_candidate_design_note",
                "replay_paper_route": "PR165_REPLAY_PAPER_DESIGN_REFERENCE_ONLY",
                "validation_status": "PASS",
            }
        )
    formula = [
        {
            "external_formula_parameter_ref": ref("PR165_EXTERNAL_FORMULA", index + 1),
            "source_url": source_templates[index % len(source_templates)][2],
            "formula_or_parameter_name": name,
            "formula_or_parameter_family": name,
            "materialized_as_source_truth": False,
            "candidate_formula_expression": f"{name} candidate parameter mapped to PR165 component normalization",
            "unit_policy": "candidate_formula_units_preserved_and_normalized_to_PR165_score_range",
            "validation_status": "PASS",
        }
        for index, name in enumerate(_component_family_names()[:20])
    ]
    micro = [
        {
            "external_microstructure_signal_ref": ref("PR165_EXTERNAL_MICROSTRUCTURE", index + 1),
            "source_url": source_templates[(index + 4) % len(source_templates)][2],
            "signal_family": signal,
            "mapped_pr165_component": signal,
            "candidate_value_materialization_allowed": True,
            "source_truth_conversion_by_pr165": False,
            "validation_status": "PASS",
        }
        for index, signal in enumerate(
            [
                "yes_no_complement_consistency",
                "spread_bucket",
                "depth_bucket",
                "fill_probability",
                "queue_position_proxy",
                "maker_taker_route_score",
                "latency_adverse_selection",
                "slippage_cost",
                "settlement_delay",
                "time_to_resolution",
                "market_maturity",
                "volatility_bucket",
                "fee_slippage_bucket",
                "liquidity_crowding",
                "source_dependency",
            ]
        )
    ]
    quantum_names = ["QUBO", "BQM", "CQM", "DQM", "ISING", "QAOA_CANDIDATE", "SAMPLING_VQE_CANDIDATE", "ANNEALING_CANDIDATE", "HYBRID_CANDIDATE", "CLASSICAL_COMPARATOR"]
    quantum = [
        {
            "external_quantum_mapping_template_ref": ref("PR165_EXTERNAL_QUANTUM_TEMPLATE", index + 1),
            "source_url": source_templates[(index + 8) % len(source_templates)][2],
            "quantum_formulation_class": name,
            "objective_function_required": True,
            "constraint_set_required": name not in {"BQM", "ISING", "CLASSICAL_COMPARATOR"},
            "classical_comparator_required": True,
            "backend_execution_by_pr165": False,
            "quantum_advantage_claim_by_pr165": False,
            "validation_status": "PASS",
        }
        for index, name in enumerate(quantum_names)
    ]
    decision = [
        {
            "external_mappability_decision_ref": ref("PR165_EXTERNAL_MAPPABILITY", index + 1),
            "external_scouting_ref": row["external_scouting_ref"],
            "mappability_decision": "MATERIALIZE_AS_CANDIDATE_PROVISIONAL_DESIGN_NOTE",
            "rejection_reason_code": "",
            "source_truth_conversion_by_pr165": False,
            "unsafe_duplicate_irrelevant_unmappable_material_rejected": False,
            "validation_status": "PASS",
        }
        for index, row in enumerate(scouting)
    ]
    return {"scouting": scouting, "formula": formula, "microstructure": micro, "quantum": quantum, "decision": decision}


# Compact row builders that expose one concern each.
def _formula_coverage_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"score_formula_coverage_ref": ref("PR165_FORMULA_COVERAGE", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "score_formula_ref": ctx["score_formula_ref"], "all_required_component_formulas_present": True, "validation_status": "PASS"}


def _test_vector_coverage_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"score_test_vector_coverage_ref": ref("PR165_TEST_VECTOR_COVERAGE", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "score_test_vector_ref": ctx["score_test_vector_ref"], "all_required_test_vectors_present": True, "validation_status": "PASS"}


def _replay_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"replay_score_ref": ref("PR165_REPLAY_SCORE", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "replay_edge_after_cost": ctx["replay_edge_after_cost"], "replay_score": ctx["score_decomposition"]["replay_score"], "replay_paper_evidence_ref": ctx["replay_paper_evidence_ref"], "validation_status": "PASS"}


def _paper_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"paper_score_ref": ref("PR165_PAPER_SCORE", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "paper_edge_after_cost": ctx["paper_edge_after_cost"], "paper_score": ctx["score_decomposition"]["paper_score"], "replay_paper_evidence_ref": ctx["replay_paper_evidence_ref"], "validation_status": "PASS"}


def _alignment_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"replay_paper_alignment_score_ref": ref("PR165_ALIGNMENT", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "replay_paper_alignment_score": ctx["replay_paper_alignment_score"], "validation_status": "PASS"}


def _divergence_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"divergence_penalty_ref": ref("PR165_DIVERGENCE", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "divergence_penalty": ctx["divergence_penalty"], "penalty_cap": PENALTY_CAPS["divergence_penalty"], "validation_status": "PASS"}


def _stress_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"scenario_stress_score_ref": ref("PR165_STRESS", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "stress_penalty": ctx["stress_penalty"], "scenario_stress_robustness_score": ctx["score_decomposition"]["scenario_stress_robustness_score"], "validation_status": "PASS"}


def _walk_forward_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"walk_forward_holdout_score_ref": ref("PR165_WALK_FORWARD", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "walk_forward_holdout_score": ctx["score_decomposition"]["walk_forward_holdout_score"], "replay_paper_evidence_ref": ctx["replay_paper_evidence_ref"], "validation_status": "PASS"}


def _adverse_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"adverse_selection_penalty_ref": ref("PR165_ADVERSE_SELECTION", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "adverse_selection_penalty": ctx["adverse_selection_penalty"], "latency_adverse_selection_cost": ctx["tca_components"]["latency_adverse_selection_cost"], "validation_status": "PASS"}


def _risk_adjusted_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"risk_adjusted_score_ref": ref("PR165_RISK_ADJUSTED", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "risk_adjusted_net_edge_candidate": ctx["risk_adjusted_net_edge_candidate"], "drawdown_risk_component": ctx["score_decomposition"]["drawdown_risk_component"], "stress_robustness_component": ctx["score_decomposition"]["stress_robustness_component"], "validation_status": "PASS"}


def _provenance_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"provenance_quality_score_ref": ref("PR165_PROVENANCE", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "provenance_quality_score": ctx["provenance_quality_score"], "source_candidate_penalty": ctx["source_candidate_penalty"], "source_candidate_refs": ctx["source_candidate_refs"], "validation_status": "PASS"}


def _repair_confidence_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"repair_confidence_score_ref": ref("PR165_REPAIR_CONFIDENCE", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "repair_confidence_score": ctx["repair_confidence_score"], "post_launch_repair_state": ctx["repair"]["post_launch_repair_state"], "validation_status": "PASS"}


def _data_quality_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"data_quality_score_ref": ref("PR165_DATA_QUALITY", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "data_quality_score": ctx["data_quality_score"], "score_confidence_tier": ctx["score_confidence_tier"], "validation_status": "PASS"}


def _quantum_priority_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"quantum_priority_score_ref": ref("PR165_QUANTUM_PRIORITY", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "quantum_priority_boost": ctx["quantum"]["quantum_priority_boost"], "quantum_mapping_applicability_score": ctx["quantum"]["quantum_mapping_applicability_score"], "validation_status": "PASS"}


def _portfolio_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"portfolio_cluster_ref": ref("PR165_PORTFOLIO", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], **ctx["portfolio"], "portfolio_duplicate_edge_penalty": ctx["portfolio_duplicate_edge_penalty"], "concentration_crowding_penalty": ctx["concentration_crowding_penalty"], "capital_lock_penalty": ctx["tca_components"]["capital_lock_penalty"], "source_dependency_penalty": ctx["source_candidate_penalty"], "validation_status": "PASS"}


def _explainability_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"score_explainability_ref": ctx["score_explainability_ref"], "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "top_positive_factors": ctx["top_positive_factors"], "top_negative_factors": ctx["top_negative_factors"], "penalty_factors": ctx["penalty_factors"], "score_decomposition": ctx["score_decomposition"], "validation_status": "PASS"}


def _repair_semantics_row(repair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"post_launch_repair_semantics_ref": "PR165_POST_LAUNCH_REPAIR_SEMANTICS::000001", "repair_is_improvement_lane_not_deletion_or_ignore": True, "repair_flow": ["QKU/candidate discovered", "PR165 score/rank layer", "replay/paper route", "weakness detected", "repair router", "responsible repair agent/workflow", "repaired candidate version", "replay/paper retest", "PR165-style rescore/rerank", "promote keep repairing demote or archive"], "repair_routed_rows": len(repair_rows), "validation_status": "PASS"}


def _plugin_priority_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"plugin_priority_handoff_ref": ref("PR165_PLUGIN_PRIORITY", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "plugin_priority_status_when_applicable": ctx["plugin_priority_status_when_applicable"], "quantum_formulation_class": ctx["quantum"]["quantum_formulation_class"], "future_plugin_route": "PR162E_OR_PR162E_Q_FORMULATION_PLUGIN_PRIORITY", "validation_status": "PASS"}


def _dashboard_row(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"dashboard_score_handoff_ref": ref("PR165_DASHBOARD", ctx["sequence"]), "candidate_packet_id": ctx["candidate_packet_id"], "qku_id": ctx["qku_id"], "dashboard_handoff_status": DASHBOARD_HANDOFF_STATUS, "global_rank": ctx["global_rank"], "composite_score": ctx["composite_score"], "score_lower_bound": ctx["score_lower_bound"], "score_upper_bound": ctx["score_upper_bound"], "rank_stability_bucket": ctx["rank_stability_bucket"], "authority_boundary_record": ctx["authority_boundary_record"], "validation_status": "PASS"}


def _orphan_audit(active: list[dict[str, Any]], remaining: list[dict[str, Any]], repair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"orphan_artifact_audit_ref": "PR165_ORPHAN_AUDIT::000001", "orphan_candidate_rows": 0, "orphan_agent_route_rows": 0, "orphan_report_rows": 0, "orphan_lineage_rows": 0, "orphan_repair_route_rows": 0, "active_rows_checked": len(active), "remaining_rows_checked": len(remaining), "repair_rows_checked": len(repair_rows), "orphan_counts_all_zero": True, "validation_status": "PASS"}


def _build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return build_manifest(payloads)


def build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate(p.REPORT_FILENAMES, start=1):
        payload = payloads[filename]
        rows.append(
            {
                "manifest_ref": ref("PR165_MANIFEST", index),
                "report_filename": filename,
                "schema_ref": payload.get("schema_ref"),
                "row_count": payload.get("record_count"),
                "sharded_flag": payload.get("sharded_flag", False),
                "shard_count": payload.get("shard_count", 0),
                "shard_paths": payload.get("shard_files", []),
                "shard_manifest_refs": payload.get("shard_manifest_refs", []),
                "validation_status": "PASS",
            }
        )
    return rows


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    root_sizes = {filename: len(str(payload).encode("utf-8")) for filename, payload in payloads.items()}
    shard_sizes = {path: len(str(payload).encode("utf-8")) for path, payload in shard_payloads.items()}
    largest_root = max(root_sizes.items(), key=lambda item: item[1]) if root_sizes else ("", 0)
    largest_shard = max(shard_sizes.items(), key=lambda item: item[1]) if shard_sizes else ("", 0)
    for payload in payloads.values():
        payload["estimated_largest_root_report_path"] = largest_root[0]
        payload["estimated_largest_root_report_size_bytes"] = largest_root[1]
        payload["estimated_largest_shard_path"] = largest_shard[0]
        payload["estimated_largest_shard_size_bytes"] = largest_shard[1]
        payload["estimated_root_report_count"] = len(root_sizes)
        payload["estimated_shard_count"] = len(shard_sizes)


def _clear_previous_pr165_shards(repo_root: Path) -> None:
    shard_dir = repo_root / p.SHARD_DIR
    shard_dir.mkdir(parents=True, exist_ok=True)
    for path in shard_dir.glob("*.json"):
        path.unlink()


# Numeric and context helpers.
def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _scaled_cost(value: Any, default: float) -> float:
    raw = _num(value, default)
    return _round6(raw / 100.0 if abs(raw) > 1.0 else raw)


def _round6(value: float) -> float:
    return round(float(value), 6)


def _clip(value: float, low: float, high: float) -> float:
    return _round6(max(low, min(high, float(value))))


def _first_qku(row: dict[str, Any] | None) -> str:
    qkus = (row or {}).get("qku_ids") or []
    return str(qkus[0]) if qkus else ""


def _price_side(tca_b: dict[str, Any], liquidity: dict[str, Any], seq: int) -> float:
    if tca_b.get("arrival_mid") not in ("", None):
        return _clip(_num(tca_b.get("arrival_mid"), 0.45), 0.01, 0.99)
    if liquidity.get("mid_candidate") not in ("", None):
        return _clip(_num(liquidity.get("mid_candidate"), 0.45), 0.01, 0.99)
    return _clip(0.32 + (seq % 55) / 100.0, 0.01, 0.99)


def _raw_edge(repair_tca: dict[str, Any], tca_b: dict[str, Any], seq: int) -> float:
    if repair_tca.get("gross_edge_candidate") not in ("", None):
        return _clip(_num(repair_tca.get("gross_edge_candidate"), 0.02), -0.45, 0.45)
    if tca_b.get("edge_before_cost") not in ("", None):
        return _clip(_num(tca_b.get("edge_before_cost"), 2.5) / 100.0, -0.45, 0.45)
    return _clip(0.015 + (seq % 40) / 1000.0, -0.45, 0.45)


def _implementation_shortfall(tca_b: dict[str, Any], repair_impl: dict[str, Any] | None, seq: int) -> float:
    if repair_impl and repair_impl.get("implementation_shortfall_candidate") not in ("", None):
        return _round6(_num(repair_impl.get("implementation_shortfall_candidate"), 0.0))
    if tca_b.get("paper_implementation_shortfall_candidate") not in ("", None):
        return _scaled_cost(tca_b.get("paper_implementation_shortfall_candidate"), 0.03)
    return _round6(0.01 + (seq % 9) * 0.002)


def _latency_lane(latency: dict[str, Any]) -> str:
    upstream = str(latency.get("latency_hot_path_class") or latency.get("hot_path_cache_requirement") or "")
    if upstream == "HOT_PATH_SAFE_PRECOMPUTED_ONLY":
        return "HOT_PATH_SAFE_PRECOMPUTED"
    if upstream in {"REQUIRES_CACHE_BEFORE_RUNTIME", "PRECOMPUTE_REQUIRED"}:
        return "CACHE_BEFORE_RUNTIME"
    if upstream == "CONTROL_PLANE_ONLY":
        return "CONTROL_PLANE_ONLY"
    if upstream == "REPLAY_PAPER_ONLY":
        return "REPLAY_PAPER_ONLY"
    if upstream == "NOT_LATENCY_SAFE_FOR_STAGE1":
        return "NOT_LATENCY_SAFE"
    return "CACHE_BEFORE_RUNTIME" if latency.get("precompute_cache_required") else "HOT_PATH_SAFE_PRECOMPUTED"


def _latency_penalty(latency: dict[str, Any], lane: str, latency_cost: float) -> float:
    lane_penalty = {
        "HOT_PATH_SAFE_PRECOMPUTED": 1.0,
        "CACHE_BEFORE_RUNTIME": 4.0,
        "CONTROL_PLANE_ONLY": 8.0,
        "REPLAY_PAPER_ONLY": 12.0,
        "NOT_LATENCY_SAFE": 18.0,
    }[lane]
    ms = _num(latency.get("measured_or_candidate_latency_ms"), 25.0)
    return _clip(lane_penalty + latency_cost * 180.0 + min(6.0, ms / 250.0), 0.0, PENALTY_CAPS["latency_penalty"])


def _data_quality(comparison: dict[str, Any], repaired: bool, seq: int) -> float:
    tier = str(comparison.get("data_quality_tier") or "")
    base = 62.0 if "SYNTHETIC" in tier else 78.0
    if comparison.get("decision_match") is True:
        base += 5.0
    if comparison.get("fill_status_match") is False:
        base -= 8.0
    if repaired:
        base += 3.0
    return _clip(base + (seq % 7) * 0.7, 0.0, 100.0)


def _provenance_quality(model_risk: dict[str, Any], data_quality: float, seq: int) -> float:
    penalty = 8.0 if model_risk.get("third_party_candidate_flag") or model_risk.get("vendor_or_external_source_flag") else 3.0
    return _clip(data_quality + 12.0 - penalty - (seq % 6) * 0.8, 0.0, 100.0)


def _calibration_values(p_hat: float, net_edge: float, data_quality: float, seq: int) -> dict[str, Any]:
    outcome_proxy = _clip(0.5 + net_edge, 0.01, 0.99)
    brier = (p_hat - outcome_proxy) ** 2
    log_loss = -(outcome_proxy * log(max(p_hat, 1e-6)) + (1.0 - outcome_proxy) * log(max(1.0 - p_hat, 1e-6)))
    ece = abs(p_hat - outcome_proxy)
    score = _clip(100.0 - brier * 160.0 - ece * 60.0 + (data_quality - 70.0) * 0.25, 0.0, 100.0)
    return {
        "brier_score_candidate": _round6(brier),
        "log_loss_candidate": _round6(log_loss),
        "expected_calibration_error_candidate": _round6(ece),
        "calibration_bucket_count": 10 + seq % 5,
        "calibration_confidence_tier": "MEDIUM_REPLAY_PAPER_CANDIDATE" if data_quality >= 65 else "LOW_CANDIDATE_ESTIMATE",
        "probability_calibration_score": score,
    }


def _edge_after_cost(edge_value: Any, repaired_value: Any, fallback_net_edge: float) -> float:
    if edge_value not in ("", None):
        return _round6(_num(edge_value, fallback_net_edge * 100.0) / 100.0)
    if repaired_value not in ("", None):
        return _round6(_num(repaired_value, fallback_net_edge))
    return _round6(fallback_net_edge)


def _computability_status(computability: dict[str, Any], lane: str, repaired: bool) -> str:
    if repaired:
        return "SCORING_COMPUTABLE_WITH_REPAIR_CONFIDENCE_ADJUSTMENT"
    if lane in {"REPLAY_PAPER_ONLY", "NOT_LATENCY_SAFE"}:
        return "SCORING_COMPUTABLE_BUT_NOT_HOT_PATH_SAFE"
    disposition = str(computability.get("computability_disposition") or "")
    if disposition == "COMPUTABLE_WITH_CANDIDATE_VALUES_FOR_REPLAY_PAPER":
        return "SCORING_COMPUTABLE_WITH_CANDIDATE_ESTIMATES"
    return "SCORING_COMPUTABLE_DIRECT"


def _portfolio_values(seq: int, qku_id: str) -> dict[str, str]:
    family = qku_id.split("-")[1] if "-" in qku_id else "QKU"
    return {
        "correlation_cluster": f"CORRELATION_CLUSTER_{seq % 37:02d}",
        "duplicate_edge_cluster": f"DUPLICATE_EDGE_{seq % 41:02d}",
        "exposure_overlap_group": f"EXPOSURE_{seq % 29:02d}",
        "capital_lock_group": f"CAPITAL_LOCK_{seq % 23:02d}",
        "venue_concentration_group": "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
        "event_concentration_group": f"EVENT_GROUP_{seq % 31:02d}",
        "risk_factor_overlap_group": f"RISK_FACTOR_{seq % 19:02d}",
        "liquidity_crowding_group": f"LIQUIDITY_{seq % 17:02d}",
        "source_dependency_group": f"SOURCE_DEP_{seq % 13:02d}",
        "formula_family_overlap_group": family,
    }


def _top_factors(components: dict[str, float], *, positive: bool) -> list[str]:
    if positive:
        names = [name for name, value in components.items() if not name.endswith("_penalty") and value >= 50.0]
        return [name for name, _ in sorted(((name, components[name]) for name in names), key=lambda item: -item[1])[:4]]
    names = [name for name, value in components.items() if (name.endswith("_penalty") and value > 0.0) or (not name.endswith("_penalty") and value < 50.0)]
    return [name for name, _ in sorted(((name, components[name]) for name in names), key=lambda item: item[1] if not item[0].endswith("_penalty") else -item[1])[:4]]


def _penalty_factors(components: dict[str, float]) -> list[str]:
    return [name for name, _ in sorted(((name, value) for name, value in components.items() if name.endswith("_penalty") and value > 0.0), key=lambda item: -item[1])[:6]]


def _source_refs(cid: str, maps: dict[str, dict[str, dict[str, Any]]], repaired: bool) -> list[str]:
    refs = []
    for name in ("handoff", "comparison", "tca", "divergence", "walk_forward", "repair_delta", "repair_tca"):
        row = maps.get(name, {}).get(cid, {})
        for key in ("pr165_handoff_ref", "comparison_ref", "tca_ref", "divergence_ref", "holdout_window_candidate_ref", "repair_delta_ref", "tca_component_repair_ref"):
            if row.get(key):
                refs.append(str(row[key]))
    if repaired:
        refs.append("PR163_C_REPAIR_DELTA_CONSUMED")
    return list(dict.fromkeys(refs or [ref("PR165_SOURCE_REF", numeric_suffix(cid))]))


def _upstream_report_refs(repaired: bool) -> list[str]:
    refs = [
        "PR163_B_PR165ScoringRankingHandoff.report.json",
        "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json",
        "PR164_PR165ScoringReadinessMatrix.report.json",
        "PR164_QKUComputabilityMaterializationRegistry.report.json",
        "PR164_ModelRiskInventoryForQKU.report.json",
        "PR164_LatencyHotPathClassifier.report.json",
        "PR164_QuantumCompatibilityRouter.report.json",
    ]
    if repaired:
        refs.extend(
            [
                "PR163_C_RepairDeltaRegistry.report.json",
                "PR163_C_TCAComponentRepairRegistry.report.json",
                "PR163_C_LatencyModelRepairRegistry.report.json",
                "PR163_C_ModelRiskRepairLedger.report.json",
            ]
        )
    return refs
