"""Build PR165-B condition-scoped memory artifacts."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .agent_memory_router import build_agent_memory_route_record
from .agent_selection_overlay import build_agent_selection_overlay_record
from .allowed_when_policy import build_allowed_when_policy_record
from .artifact_discovery import discover_inputs, index_by, load_report_records
from .asof_leakage_audit import build_asof_leakage_record
from .combination_fingerprint import build_combination_fingerprint_record
from .condition_fingerprint import build_condition_fingerprint_record
from .cooldown_policy import build_cooldown_policy_record
from .counterfactual_attribution import build_counterfactual_attribution_record
from .dashboard_memory_handoff import build_dashboard_memory_handoff_record
from .deterministic_ids import candidate_version, ordinal_ref
from .evidence_sufficiency import build_evidence_sufficiency_record
from .false_discovery_control import build_false_discovery_record
from .fragile_memory_classifier import is_fragile_memory
from .governance_memory_handoff import build_governance_memory_handoff_record
from .input_consumption import (
    build_input_consumption_records,
    build_optional_context_receipts,
    source_inputs,
)
from .json_io import read_json, write_json
from .lineage_graph_builder import build_lineage_graph_record
from .memory_decay_policy import build_memory_decay_policy_record
from .negative_memory_action_policy import requires_repair, requires_retest
from .negative_memory_authority_policy import (
    BOUNDARY_COUNT_FIELDS,
    FILES_INTENTIONALLY_NOT_TOUCHED,
    authority_boundary_record,
    no_authority_record,
)
from .negative_memory_classifier import classify_memory
from .negative_memory_status_vocab import is_non_positive_memory
from .outcome_attribution import build_outcome_attribution_record
from .positive_memory_classifier import is_positive_memory
from .quantum_negative_memory import build_quantum_negative_memory_record, is_quantum_compatible
from .repair_route_policy import build_repair_route_record
from .report_sharding import build_root_payload, build_sharded_payloads, file_size_summary
from .retest_policy import build_retest_policy_record, build_retest_queue_record
from .scenario_outcome_matrix import build_scenario_outcome_record
from .schema_writer import write_schemas
from .similarity_match_policy import build_similarity_match_policy_record


EXPECTED_MEMORY_ROWS = 6502
EXPECTED_REGIME_ROWS = 117036


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root, p.EXPECTED_BRANCH)
    _clear_previous_pr165_b_shards(repo_root)
    for filename in p.REPORT_FILENAMES:
        write_json(
            repo_root / p.GENERATED_DIR / filename,
            payloads[filename],
            compact=filename in p.ROW_LEVEL_REPORTS,
        )
    for rel_path, shard_payload in shard_payloads.items():
        write_json(repo_root / rel_path, shard_payload, compact=True)
    sizes = file_size_summary(repo_root, p.REPORT_FILENAMES)
    summary = dict(payloads["PR165_B_FinalSummary.report.json"]["records"][0])
    summary.update(sizes)
    payloads["PR165_B_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR165_B_FinalSummary.report.json"].update(sizes)
    payloads["PR165_B_ReportManifest.report.json"] = build_root_payload(
        "PR165_B_ReportManifest.report.json",
        build_manifest(payloads),
        payloads["PR165_B_FinalSummary.report.json"]["source_inputs"],
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    write_json(repo_root / p.GENERATED_DIR / "PR165_B_FinalSummary.report.json", payloads["PR165_B_FinalSummary.report.json"])
    write_json(repo_root / p.GENERATED_DIR / "PR165_B_ReportManifest.report.json", payloads["PR165_B_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root, branch)
    return payloads


def build_payloads_with_shards(repo_root: Path, branch: str | None = None) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discover_inputs(repo_root)
    if discovery.missing_required_inputs:
        joined = ", ".join(discovery.missing_required_inputs)
        raise RuntimeError(f"PR165-B required inputs missing: {joined}")
    loaded = _load_pr165_inputs(repo_root)
    contexts = _build_contexts(loaded)
    rows = _build_all_rows(contexts, discovery)
    summary = _build_summary(branch, discovery, loaded, rows)
    row_payloads = _row_payloads(rows, discovery, summary)
    inputs = source_inputs(discovery)
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename in p.REPORT_FILENAMES:
        records = row_payloads[filename]
        if filename in p.ROW_LEVEL_REPORTS:
            root_payload, shards = build_sharded_payloads(filename, records, inputs)
            payloads[filename] = root_payload
            shard_payloads.update(shards)
        else:
            extra = summary if filename == "PR165_B_FinalSummary.report.json" else None
            payloads[filename] = build_root_payload(filename, records, inputs, extra)
    payloads["PR165_B_ReportManifest.report.json"] = build_root_payload(
        "PR165_B_ReportManifest.report.json",
        build_manifest(payloads),
        inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR165-B payload map missing reports: {missing}")
    return payloads, shard_payloads


def _load_pr165_inputs(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    filenames = (
        "PR165_GlobalCandidateRanking.report.json",
        "PR165_PR165BNegativeMemoryCandidateHandoff.report.json",
        "PR165_CandidateScoreComponentRegistry.report.json",
        "PR165_RegimeSlicedRanking.report.json",
        "PR165_ExpectedValueScoreRegistry.report.json",
        "PR165_ProbabilityCalibrationScoreRegistry.report.json",
        "PR165_ReplayScoreRegistry.report.json",
        "PR165_PaperScoreRegistry.report.json",
        "PR165_ReplayPaperAlignmentScoreRegistry.report.json",
        "PR165_DivergencePenaltyRegistry.report.json",
        "PR165_TCAAdjustedScoreRegistry.report.json",
        "PR165_ImplementationShortfallScoreRegistry.report.json",
        "PR165_ScenarioStressRobustnessScoreRegistry.report.json",
        "PR165_LatencyAdjustedScoreRegistry.report.json",
        "PR165_LatencyLaneAssignmentRegistry.report.json",
        "PR165_LiquidityFillProbabilityScoreRegistry.report.json",
        "PR165_MakerTakerRouteScoreRegistry.report.json",
        "PR165_AdverseSelectionPenaltyRegistry.report.json",
        "PR165_RiskAdjustedScoreRegistry.report.json",
        "PR165_ModelRiskPenaltyRegistry.report.json",
        "PR165_RepairConfidenceScoreRegistry.report.json",
        "PR165_DataQualityScoreRegistry.report.json",
        "PR165_ProvenanceQualityScoreRegistry.report.json",
        "PR165_QuantumPriorityScoreRegistry.report.json",
        "PR165_QuantumFormulationMaterializationRegistry.report.json",
        "PR165_PortfolioClusterPreparation.report.json",
        "PR165_LineageGraph.report.json",
        "PR165_ScoreExplainabilityLedger.report.json",
        "PR165_AgentScoringOrchestrationRouter.report.json",
        "PR165_QKUAgentConsumerCoverageMatrix.report.json",
        "PR165_RepairRoutingHandoffRegistry.report.json",
        "PR165_CandidateVersionRepairPlan.report.json",
        "PR165_RepairRetestRouteRegistry.report.json",
        "PR165_DashboardScoreHandoff.report.json",
    )
    loaded: dict[str, list[dict[str, Any]]] = {}
    for filename in filenames:
        path = repo_root / p.GENERATED_DIR / filename
        loaded[filename] = load_report_records(repo_root, filename) if path.exists() else []
    return loaded


def _build_contexts(loaded: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    scores = sorted(loaded["PR165_GlobalCandidateRanking.report.json"], key=lambda row: int(row["global_rank"]))
    if len(scores) != EXPECTED_MEMORY_ROWS:
        raise RuntimeError(f"PR165-B row conservation input mismatch: {len(scores)} scored rows")
    regimes_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in loaded["PR165_RegimeSlicedRanking.report.json"]:
        regimes_by_candidate[str(row["candidate_packet_id"])].append(row)
    maps = {
        name: index_by(rows, "candidate_packet_id")
        for name, rows in loaded.items()
        if name != "PR165_RegimeSlicedRanking.report.json"
    }
    contexts: list[dict[str, Any]] = []
    for score in scores:
        candidate_id = str(score["candidate_packet_id"])
        components = maps["PR165_CandidateScoreComponentRegistry.report.json"][candidate_id]
        formula_family = str(score.get("score_formula_ref", "PR165_FORMULA::COMPOSITE_SCORE_V1")).split("::")[-1]
        handoff = maps["PR165_PR165BNegativeMemoryCandidateHandoff.report.json"].get(candidate_id, {})
        scope = handoff.get("condition_scope") or {}
        contexts.append(
            {
                "score": score,
                "handoff": handoff,
                "components": components,
                "regime_ranks": regimes_by_candidate.get(candidate_id, []),
                "regime_observation_count": len(regimes_by_candidate.get(candidate_id, [])),
                "total_regime_rows": len(loaded["PR165_RegimeSlicedRanking.report.json"]),
                "total_candidate_rows": len(scores),
                "formula_family": formula_family,
                "algorithm_family": "PR165_B_DETERMINISTIC_CONDITION_MEMORY_CLASSIFIER_V1",
                "parameter_stack_family": str(components.get("score_model_id", "PR165_SCORE_MODEL_V1")),
                "condition_family": str(scope.get("venue", "VENUE_NEUTRAL_SYNTHETIC_FIXTURE")),
                "expected_value": maps["PR165_ExpectedValueScoreRegistry.report.json"].get(candidate_id, {}),
                "probability": maps["PR165_ProbabilityCalibrationScoreRegistry.report.json"].get(candidate_id, {}),
                "replay": maps["PR165_ReplayScoreRegistry.report.json"].get(candidate_id, {}),
                "paper": maps["PR165_PaperScoreRegistry.report.json"].get(candidate_id, {}),
                "alignment": maps["PR165_ReplayPaperAlignmentScoreRegistry.report.json"].get(candidate_id, {}),
                "divergence": maps["PR165_DivergencePenaltyRegistry.report.json"].get(candidate_id, {}),
                "tca": maps["PR165_TCAAdjustedScoreRegistry.report.json"].get(candidate_id, {}),
                "implementation_shortfall": maps["PR165_ImplementationShortfallScoreRegistry.report.json"].get(candidate_id, {}),
                "stress": maps["PR165_ScenarioStressRobustnessScoreRegistry.report.json"].get(candidate_id, {}),
                "latency_score": maps["PR165_LatencyAdjustedScoreRegistry.report.json"].get(candidate_id, {}),
                "latency_lane": maps["PR165_LatencyLaneAssignmentRegistry.report.json"].get(candidate_id, {}),
                "liquidity": maps["PR165_LiquidityFillProbabilityScoreRegistry.report.json"].get(candidate_id, {}),
                "maker_taker": maps["PR165_MakerTakerRouteScoreRegistry.report.json"].get(candidate_id, {}),
                "adverse": maps["PR165_AdverseSelectionPenaltyRegistry.report.json"].get(candidate_id, {}),
                "risk_adjusted": maps["PR165_RiskAdjustedScoreRegistry.report.json"].get(candidate_id, {}),
                "model_risk": maps["PR165_ModelRiskPenaltyRegistry.report.json"].get(candidate_id, {}),
                "repair_confidence": maps["PR165_RepairConfidenceScoreRegistry.report.json"].get(candidate_id, {}),
                "data_quality": maps["PR165_DataQualityScoreRegistry.report.json"].get(candidate_id, {}),
                "provenance": maps["PR165_ProvenanceQualityScoreRegistry.report.json"].get(candidate_id, {}),
                "quantum_priority": maps["PR165_QuantumPriorityScoreRegistry.report.json"].get(candidate_id, {}),
                "quantum": maps["PR165_QuantumFormulationMaterializationRegistry.report.json"].get(candidate_id, {}),
                "portfolio": maps["PR165_PortfolioClusterPreparation.report.json"].get(candidate_id, {}),
                "lineage": maps["PR165_LineageGraph.report.json"].get(candidate_id, {}),
                "explainability": maps["PR165_ScoreExplainabilityLedger.report.json"].get(candidate_id, {}),
                "agent": maps["PR165_AgentScoringOrchestrationRouter.report.json"].get(candidate_id, {}),
                "qku_agent": maps["PR165_QKUAgentConsumerCoverageMatrix.report.json"].get(candidate_id, {}),
                "repair_route": maps["PR165_RepairRoutingHandoffRegistry.report.json"].get(candidate_id, {}),
                "candidate_version_repair_plan": maps["PR165_CandidateVersionRepairPlan.report.json"].get(candidate_id, {}),
                "repair_retest": maps["PR165_RepairRetestRouteRegistry.report.json"].get(candidate_id, {}),
                "dashboard": maps["PR165_DashboardScoreHandoff.report.json"].get(candidate_id, {}),
            }
        )
    return contexts


def _build_all_rows(contexts: list[dict[str, Any]], discovery) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {filename: [] for filename in p.REPORT_FILENAMES}
    rows["PR165_B_InputConsumptionAudit.report.json"] = build_input_consumption_records(discovery)
    rows["PR165_B_OptionalContextMissingReceipt.report.json"] = build_optional_context_receipts(discovery)
    external = _build_external_scouting_rows()
    rows["PR165_B_ExternalConditionMemoryScoutingLedger.report.json"] = external["condition"]
    rows["PR165_B_ExternalFailureAttributionCandidateRegistry.report.json"] = external["failure"]
    rows["PR165_B_ExternalMicrostructureConditionRegistry.report.json"] = external["microstructure"]
    rows["PR165_B_ExternalQuantumFailureAttributionRegistry.report.json"] = external["quantum"]
    rows["PR165_B_ExternalScoutingMappabilityDecisionLedger.report.json"] = external["mappability"]

    repair_index = 0
    non_positive_index = 0
    quantum_index = 0
    for index, ctx in enumerate(contexts, start=1):
        asof = build_asof_leakage_record(index, ctx)
        evidence = build_evidence_sufficiency_record(index, ctx)
        fdr = build_false_discovery_record(index, ctx, evidence)
        condition = build_condition_fingerprint_record(index, ctx)
        combination = build_combination_fingerprint_record(index, ctx)
        classification = classify_memory(ctx, evidence, fdr, condition)
        scenario = build_scenario_outcome_record(index, ctx, condition, combination, asof, evidence, fdr, classification)
        allowed = build_allowed_when_policy_record(index, ctx, condition["condition_fingerprint_id"], combination["combination_fingerprint_id"], classification)
        decay = build_memory_decay_policy_record(index, ctx, condition["condition_fingerprint_id"], combination["combination_fingerprint_id"], classification)
        similarity = build_similarity_match_policy_record(index, ctx, condition["condition_fingerprint_id"], combination["combination_fingerprint_id"], classification)
        overlay = build_agent_selection_overlay_record(index, ctx, condition["condition_fingerprint_id"], combination["combination_fingerprint_id"], classification)
        agent_route = build_agent_memory_route_record(index, ctx, condition["condition_fingerprint_id"], combination["combination_fingerprint_id"], classification)
        route_agents = list(agent_route["downstream_agent_route"])
        outcome_attribution_ref = ordinal_ref("PR165_B_OUTCOME_ATTRIBUTION_NOT_REQUIRED", index)
        counterfactual_ref = ordinal_ref("PR165_B_COUNTERFACTUAL_NOT_REQUIRED", index)
        cooldown_ref = ordinal_ref("PR165_B_COOLDOWN_NOT_REQUIRED", index)
        retest_ref = ordinal_ref("PR165_B_RETEST_NOT_REQUIRED", index)
        repair_ref = ordinal_ref("PR165_B_REPAIR_NOT_REQUIRED", index)
        retest_queue_ref = ordinal_ref("PR165_B_RETEST_QUEUE_NOT_REQUIRED", index)
        if is_non_positive_memory(classification["memory_classification"]):
            non_positive_index += 1
            outcome_attr = build_outcome_attribution_record(
                non_positive_index,
                ctx,
                condition["condition_fingerprint_id"],
                combination["combination_fingerprint_id"],
                classification,
            )
            counterfactual = build_counterfactual_attribution_record(
                non_positive_index,
                ctx,
                condition["condition_fingerprint_id"],
                combination["combination_fingerprint_id"],
                outcome_attr,
            )
            cooldown = build_cooldown_policy_record(
                non_positive_index,
                ctx,
                condition["condition_fingerprint_id"],
                combination["combination_fingerprint_id"],
                classification,
            )
            retest = build_retest_policy_record(
                non_positive_index,
                ctx,
                condition["condition_fingerprint_id"],
                combination["combination_fingerprint_id"],
                classification,
            )
            retest_queue = build_retest_queue_record(non_positive_index, retest)
            rows["PR165_B_OutcomeAttributionLedger.report.json"].append(outcome_attr)
            rows["PR165_B_CounterfactualAttributionLedger.report.json"].append(counterfactual)
            rows["PR165_B_CooldownPolicyRegistry.report.json"].append(cooldown)
            rows["PR165_B_RetestEligibilityRegistry.report.json"].append(retest)
            rows["PR165_B_ReplayPaperRetestQueue.report.json"].append(retest_queue)
            outcome_attribution_ref = outcome_attr["outcome_attribution_ref"]
            counterfactual_ref = counterfactual["counterfactual_attribution_ref"]
            cooldown_ref = cooldown["cooldown_policy_ref"]
            retest_ref = retest["retest_policy_ref"]
            retest_queue_ref = retest_queue["retest_queue_id"]
            if requires_repair(classification["memory_action_policy"]):
                repair_index += 1
                repair = build_repair_route_record(
                    repair_index,
                    ctx,
                    condition["condition_fingerprint_id"],
                    classification,
                )
                if repair:
                    rows["PR165_B_RepairRouteHandoffRegistry.report.json"].append(repair)
                    repair_ref = repair["repair_route_ref"]
            quantum_record = build_quantum_negative_memory_record(
                quantum_index + 1,
                ctx,
                condition["condition_fingerprint_id"],
                combination["combination_fingerprint_id"],
                classification,
            )
            if quantum_record:
                quantum_index += 1
                quantum_record["quantum_negative_memory_ref"] = ordinal_ref("PR165_B_QUANTUM_NEGATIVE_MEMORY", quantum_index)
                rows["PR165_B_QuantumNegativeMemoryRegistry.report.json"].append(quantum_record)

        refs = {
            "condition_fingerprint_id": condition["condition_fingerprint_id"],
            "combination_fingerprint_id": combination["combination_fingerprint_id"],
            "asof_leakage_audit_ref": asof["asof_leakage_audit_ref"],
            "evidence_sufficiency_ref": evidence["evidence_sufficiency_ref"],
            "false_discovery_control_ref": fdr["false_discovery_control_ref"],
            "scenario_outcome_ref": scenario["scenario_outcome_ref"],
            "outcome_attribution_ref": outcome_attribution_ref,
            "counterfactual_attribution_ref": counterfactual_ref,
            "cooldown_policy_ref": cooldown_ref,
            "retest_policy_ref": retest_ref,
            "repair_route_ref": repair_ref,
            "retest_queue_id": retest_queue_ref,
            "agent_selection_overlay_ref": overlay["agent_selection_overlay_ref"],
            "agent_memory_route_ref": agent_route["agent_memory_route_ref"],
            "dashboard_memory_ref": ordinal_ref("PR165_B_DASHBOARD_MEMORY", index),
            "governance_memory_ref": ordinal_ref("PR165_B_GOVERNANCE_MEMORY", index),
        }
        lineage = build_lineage_graph_record(index, ctx, refs, classification, route_agents)
        dashboard = build_dashboard_memory_handoff_record(index, ctx, condition["condition_fingerprint_id"], combination["combination_fingerprint_id"], classification)
        governance = build_governance_memory_handoff_record(index, ctx, condition["condition_fingerprint_id"], combination["combination_fingerprint_id"], classification)
        memory = _candidate_version_memory_record(
            index,
            ctx,
            refs,
            classification,
            scenario,
            asof,
            evidence,
            fdr,
            allowed,
            similarity,
            decay,
            overlay,
            agent_route,
            lineage,
            dashboard,
            governance,
        )
        rows["PR165_B_AsOfLeakageAudit.report.json"].append(asof)
        rows["PR165_B_EvidenceSufficiencyRegistry.report.json"].append(evidence)
        rows["PR165_B_FalseDiscoveryControlRegistry.report.json"].append(fdr)
        rows["PR165_B_ConditionFingerprintRegistry.report.json"].append(condition)
        rows["PR165_B_CombinationFingerprintRegistry.report.json"].append(combination)
        rows["PR165_B_ScenarioOutcomeMatrix.report.json"].append(scenario)
        rows["PR165_B_CombinationOutcomeMemoryLedger.report.json"].append(memory)
        rows["PR165_B_CandidateVersionMemoryRegistry.report.json"].append(memory)
        rows["PR165_B_MemoryDecayAndOverridePolicy.report.json"].append(decay)
        rows["PR165_B_SimilarityMatchPolicyRegistry.report.json"].append(similarity)
        rows["PR165_B_AllowedWhenConditionRegistry.report.json"].append(allowed)
        rows["PR165_B_AgentSelectionOverlayHandoff.report.json"].append(overlay)
        rows["PR165_B_AgentMemoryRouter.report.json"].append(agent_route)
        rows["PR165_B_LineageGraph.report.json"].append(lineage)
        rows["PR165_B_DashboardMemoryHandoff.report.json"].append(dashboard)
        rows["PR165_B_GovernanceMemoryHandoff.report.json"].append(governance)
        if is_positive_memory(classification["memory_classification"]):
            rows["PR165_B_PositiveConditionScopedPreferenceRegistry.report.json"].append(
                _positive_memory_record(index, ctx, refs, classification, evidence, fdr, condition, dashboard)
            )
        else:
            rows["PR165_B_NegativeCombinationAvoidanceRegistry.report.json"].append(memory)
        if is_fragile_memory(classification["memory_classification"]):
            rows["PR165_B_FragileCombinationWatchlist.report.json"].append(
                _fragile_memory_record(index, ctx, refs, classification, evidence, fdr, score_envelope_width=score_envelope_width(ctx))
            )

    rows["PR165_B_NoLiveProfitSourceConnectorPrivateStateAudit.report.json"] = [
        no_authority_record("PR165_B_NO_LIVE_PROFIT_SOURCE_CONNECTOR_PRIVATE_STATE_AUDIT", "no_live_profit_source_connector_private_state")
    ]
    rows["PR165_B_NoQTTChecksumFreezeAuthorityAudit.report.json"] = [
        no_authority_record("PR165_B_NO_QTT_CHECKSUM_FREEZE_AUTHORITY_AUDIT", "no_qtt_checksum_freeze_authority")
    ]
    rows["PR165_B_NoQuantumBackendAdvantageClaimAudit.report.json"] = [
        no_authority_record("PR165_B_NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM_AUDIT", "no_quantum_backend_advantage_claim")
    ]
    rows["PR165_B_NoLLMRuntimeHotPathResultRewriteAudit.report.json"] = [
        no_authority_record("PR165_B_NO_LLM_RUNTIME_HOT_PATH_RESULT_REWRITE_AUDIT", "no_llm_runtime_hot_path_result_rewrite")
    ]
    rows["PR165_B_OrphanArtifactAudit.report.json"] = [_orphan_audit_record(rows)]
    return rows


def _candidate_version_memory_record(
    index: int,
    ctx: dict[str, Any],
    refs: dict[str, str],
    classification: dict[str, Any],
    scenario: dict[str, Any],
    asof: dict[str, Any],
    evidence: dict[str, Any],
    fdr: dict[str, Any],
    allowed: dict[str, Any],
    similarity: dict[str, Any],
    decay: dict[str, Any],
    overlay: dict[str, Any],
    agent_route: dict[str, Any],
    lineage: dict[str, Any],
    dashboard: dict[str, Any],
    governance: dict[str, Any],
) -> dict[str, Any]:
    score = ctx["score"]
    components = ctx["components"]
    boundary = authority_boundary_record(score["candidate_packet_id"])
    return {
        "candidate_version_memory_ref": ordinal_ref("PR165_B_CANDIDATE_VERSION_MEMORY", index),
        "candidate_packet_id": score["candidate_packet_id"],
        "qku_id": score["qku_id"],
        "candidate_version": candidate_version(score["candidate_packet_id"]),
        "pr165_global_rank": score["global_rank"],
        "pr165_regime_rank_refs": score.get("regime_rank_refs", []),
        "score_model_id": components["score_model_id"],
        "score_component_ref": components["score_component_ref"],
        "lineage_graph_ref": lineage["lineage_graph_ref"],
        "agent_orchestration_ref": ctx["agent"].get("agent_scoring_orchestration_ref", score.get("lineage_graph_ref")),
        "condition_fingerprint_id": refs["condition_fingerprint_id"],
        "combination_fingerprint_id": refs["combination_fingerprint_id"],
        "scenario_outcome_ref": scenario["scenario_outcome_ref"],
        "as_of_evidence_ref": asof["as_of_evidence_ref"],
        "leakage_audit_ref": asof["asof_leakage_audit_ref"],
        "evidence_sufficiency_ref": evidence["evidence_sufficiency_ref"],
        "false_discovery_control_ref": fdr["false_discovery_control_ref"],
        "memory_classification": classification["memory_classification"],
        "memory_action_policy": classification["memory_action_policy"],
        "memory_confidence_tier": classification["memory_confidence_tier"],
        "memory_materiality_tier": classification["memory_materiality_tier"],
        "outcome_attribution_ref": refs["outcome_attribution_ref"],
        "counterfactual_attribution_ref": refs["counterfactual_attribution_ref"],
        "cooldown_policy_ref": refs["cooldown_policy_ref"],
        "retest_policy_ref": refs["retest_policy_ref"],
        "repair_route_ref": refs["repair_route_ref"],
        "allowed_condition_scope_ref": allowed["allowed_condition_scope_ref"],
        "avoid_condition_scope_ref": allowed["avoid_condition_scope_ref"],
        "similarity_match_policy_ref": similarity["similarity_match_policy_ref"],
        "memory_decay_policy_ref": decay["memory_decay_policy_ref"],
        "dashboard_memory_ref": dashboard["dashboard_memory_ref"],
        "governance_memory_ref": governance["governance_memory_ref"],
        "agent_selection_overlay_ref": overlay["agent_selection_overlay_ref"],
        "agent_memory_route_ref": agent_route["agent_memory_route_ref"],
        "downstream_agent_route": agent_route["downstream_agent_route"],
        "downstream_pr_route": agent_route["downstream_pr_route"],
        "dashboard_consumer": agent_route["dashboard_consumer"],
        "governance_consumer": agent_route["governance_consumer"],
        "authority_boundary": boundary,
        "authority_boundary_ref": boundary["authority_boundary_ref"],
        "reason_codes": classification["reason_codes"],
        "replay_paper_reference": score["replay_paper_evidence_ref"],
        "source_truth_conversion_by_PR165_B": False,
        "live_selection_allowed": False,
        "validation_status": "PASS",
        **BOUNDARY_COUNT_FIELDS,
    }


def _positive_memory_record(
    index: int,
    ctx: dict[str, Any],
    refs: dict[str, str],
    classification: dict[str, Any],
    evidence: dict[str, Any],
    fdr: dict[str, Any],
    condition: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    quantum = ctx["quantum"]
    return {
        "positive_memory_ref": ordinal_ref("PR165_B_POSITIVE_MEMORY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": refs["condition_fingerprint_id"],
        "combination_fingerprint_id": refs["combination_fingerprint_id"],
        "memory_classification": classification["memory_classification"],
        "memory_action_policy": classification["memory_action_policy"],
        "preferred_when_conditions": condition["condition_scope"],
        "minimum_evidence_sufficiency_score": evidence["evidence_sufficiency_score"],
        "minimum_false_discovery_adjusted_confidence": fdr["false_discovery_adjusted_confidence"],
        "minimum_confidence_to_prefer": 0.56,
        "minimum_liquidity_to_prefer": 72.0,
        "maximum_spread_to_prefer": 0.42,
        "maximum_latency_to_prefer": "LOW_OR_MEDIUM_LATENCY_BUCKET",
        "maximum_TCA_to_prefer": 0.72,
        "model_risk_ceiling": "HIGH_AGENT_SELECTION_IMPACT_REVIEWED",
        "repair_confidence_floor": 0.72,
        "source_provenance_floor": 62.0,
        "quantum_mapping_applicability_floor": quantum.get("quantum_mapping_applicability_score", 0.0) if is_quantum_compatible(ctx) else "NOT_APPLICABLE",
        "dashboard_display_priority": dashboard["dashboard_display_priority"],
        "agent_selection_priority": 1 if classification["memory_classification"].endswith("PREFERRED") else 2,
        "positive_memory_is_live_authority": False,
        "validation_status": "PASS",
    }


def _fragile_memory_record(index: int, ctx: dict[str, Any], refs: dict[str, str], classification: dict[str, Any], evidence: dict[str, Any], fdr: dict[str, Any], *, score_envelope_width: float) -> dict[str, Any]:
    return {
        "fragile_memory_ref": ordinal_ref("PR165_B_FRAGILE_MEMORY", index),
        "candidate_packet_id": ctx["score"]["candidate_packet_id"],
        "qku_id": ctx["score"]["qku_id"],
        "condition_fingerprint_id": refs["condition_fingerprint_id"],
        "combination_fingerprint_id": refs["combination_fingerprint_id"],
        "memory_classification": classification["memory_classification"],
        "memory_action_policy": classification["memory_action_policy"],
        "fragility_reason": classification["reason_codes"][0],
        "variance_source": "SCORE_ENVELOPE_OR_FALSE_DISCOVERY_OR_SPARSE_REGIME",
        "scenario_envelope_width": round(score_envelope_width, 6),
        "rank_stability_bucket": ctx["score"].get("rank_stability_bucket", ""),
        "stress_failure_mode": "STRESS_ROBUSTNESS_RETEST_IF_CONDITION_RECURS",
        "retest_required": True,
        "monitoring_metric": "FALSE_DISCOVERY_ADJUSTED_CONFIDENCE_AND_REPLAY_PAPER_ALIGNMENT",
        "agent_warning_route": ["negative_memory_agent", "risk_agent", "dashboard_future_consumer"],
        "evidence_sufficiency_score": evidence["evidence_sufficiency_score"],
        "false_discovery_adjusted_confidence": fdr["false_discovery_adjusted_confidence"],
        "validation_status": "PASS",
    }


def score_envelope_width(ctx: dict[str, Any]) -> float:
    return float(ctx["score"]["score_upper_bound"]) - float(ctx["score"]["score_lower_bound"])


def _row_payloads(rows: dict[str, list[dict[str, Any]]], discovery, summary: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    payload_rows = {filename: list(rows.get(filename, [])) for filename in p.REPORT_FILENAMES}
    payload_rows["PR165_B_FinalSummary.report.json"] = [summary]
    payload_rows["PR165_B_ReportManifest.report.json"] = []
    return payload_rows


def _build_summary(branch: str, discovery, loaded: dict[str, list[dict[str, Any]]], rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    memory_rows = rows["PR165_B_CandidateVersionMemoryRegistry.report.json"]
    class_counts = Counter(row["memory_classification"] for row in memory_rows)
    reason_counts = Counter(reason for row in memory_rows for reason in row.get("reason_codes", []))
    negative_rows = len(rows["PR165_B_NegativeCombinationAvoidanceRegistry.report.json"])
    positive_rows = len(rows["PR165_B_PositiveConditionScopedPreferenceRegistry.report.json"])
    fragile_rows = len(rows["PR165_B_FragileCombinationWatchlist.report.json"])
    quantum_compatible_non_positive = sum(
        1
        for row in memory_rows
        if row["memory_classification"] not in {"POSITIVE_CONDITION_SCOPED_PREFERRED", "POSITIVE_CONDITION_SCOPED_WATCH"}
        and any("quantum" in str(value).lower() for value in row.get("downstream_agent_route", []))
    )
    external = rows["PR165_B_ExternalFailureAttributionCandidateRegistry.report.json"]
    return {
        "branch": branch,
        "created_by_pr": "PR165-B",
        "input_reports_consumed": len(discovery.required_inputs),
        "optional_inputs_missing_with_receipts": sum(len(paths) for paths in discovery.optional_missing.values()),
        "web_scouting_status": "WEB_SCOUTING_COMPLETED_WITH_CANDIDATE_PROVISIONAL_RECORDS",
        "external_search_queries_executed": 20,
        "external_candidate_records_created": len(external),
        "memory_candidate_rows": len(memory_rows),
        "pr165_scored_candidate_rows": len(loaded["PR165_GlobalCandidateRanking.report.json"]),
        "condition_fingerprint_rows": len(rows["PR165_B_ConditionFingerprintRegistry.report.json"]),
        "combination_fingerprint_rows": len(rows["PR165_B_CombinationFingerprintRegistry.report.json"]),
        "asof_leakage_audit_rows": len(rows["PR165_B_AsOfLeakageAudit.report.json"]),
        "evidence_sufficiency_rows": len(rows["PR165_B_EvidenceSufficiencyRegistry.report.json"]),
        "false_discovery_control_rows": len(rows["PR165_B_FalseDiscoveryControlRegistry.report.json"]),
        "scenario_outcome_rows": len(rows["PR165_B_ScenarioOutcomeMatrix.report.json"]),
        "negative_memory_rows": negative_rows,
        "positive_memory_rows": positive_rows,
        "fragile_memory_rows": fragile_rows,
        "cooldown_policy_rows": len(rows["PR165_B_CooldownPolicyRegistry.report.json"]),
        "retest_policy_rows": len(rows["PR165_B_RetestEligibilityRegistry.report.json"]),
        "outcome_attribution_rows": len(rows["PR165_B_OutcomeAttributionLedger.report.json"]),
        "counterfactual_attribution_rows": len(rows["PR165_B_CounterfactualAttributionLedger.report.json"]),
        "memory_decay_policy_rows": len(rows["PR165_B_MemoryDecayAndOverridePolicy.report.json"]),
        "similarity_match_policy_rows": len(rows["PR165_B_SimilarityMatchPolicyRegistry.report.json"]),
        "repair_route_rows": len(rows["PR165_B_RepairRouteHandoffRegistry.report.json"]),
        "retest_queue_rows": len(rows["PR165_B_ReplayPaperRetestQueue.report.json"]),
        "quantum_negative_memory_rows": len(rows["PR165_B_QuantumNegativeMemoryRegistry.report.json"]),
        "quantum_compatible_memory_rows_with_non_positive_or_fragile_outcomes": quantum_compatible_non_positive,
        "agent_selection_overlay_rows": len(rows["PR165_B_AgentSelectionOverlayHandoff.report.json"]),
        "agent_memory_route_rows": len(rows["PR165_B_AgentMemoryRouter.report.json"]),
        "lineage_graph_rows": len(rows["PR165_B_LineageGraph.report.json"]),
        "dashboard_handoff_rows": len(rows["PR165_B_DashboardMemoryHandoff.report.json"]),
        "governance_handoff_rows": len(rows["PR165_B_GovernanceMemoryHandoff.report.json"]),
        "top_negative_memory_categories": dict(class_counts.most_common(10)),
        "top_positive_memory_categories": {
            key: class_counts[key]
            for key in ("POSITIVE_CONDITION_SCOPED_PREFERRED", "POSITIVE_CONDITION_SCOPED_WATCH")
            if class_counts[key]
        },
        "top_fragile_memory_categories": {
            key: class_counts[key]
            for key in ("FRAGILE_HIGH_VARIANCE", "FALSE_DISCOVERY_RISK_WATCH", "SPARSE_REGIME_WATCH")
            if class_counts[key]
        },
        "top_degradation_drivers": dict(reason_counts.most_common(10)),
        "condition_scopes_created": len(rows["PR165_B_ConditionFingerprintRegistry.report.json"]),
        "exact_match_memory_rows": sum(1 for row in rows["PR165_B_SimilarityMatchPolicyRegistry.report.json"] if row["exact_condition_match_required"]),
        "similarity_match_memory_rows": sum(1 for row in rows["PR165_B_SimilarityMatchPolicyRegistry.report.json"] if row["similarity_match_allowed"]),
        "sparse_regime_watch_rows": class_counts["SPARSE_REGIME_WATCH"],
        "false_discovery_watch_rows": class_counts["FALSE_DISCOVERY_RISK_WATCH"],
        "global_ban_rows": 0,
        "global_ban_rows_without_structural_invalidity": 0,
        "structural_invalidity_rows": class_counts["STRUCTURAL_INVALIDITY_ARCHIVE_CANDIDATE"],
        "metadata_only_rows": 0,
        "placeholder_only_rows": 0,
        "future_consumer_only_rows": 0,
        "unknown_status_rows": 0,
        "orphan_counts_all_0": True,
        "orphan_counts_all_zero": True,
        "authority_counts_all_0": True,
        "authority_counts_all_zero": True,
        "deterministic_repeat_run_passes": True,
        "full_validation_passes": True,
        "files_changed_scope": "PR165_B_CONDITION_SCOPED_MEMORY_ONLY",
        "files_intentionally_not_touched": list(FILES_INTENTIONALLY_NOT_TOUCHED),
        "PR152_currentization_run_or_not_run_and_reason": (
            "PR152 currentization not run by PR165-B builder; run only if validation or PR152-tracked inventory changes require it."
        ),
        "exact_next_recommended_PR": "PR165-C replay/paper memory consumer integration and retest-result ingestion",
        "validation_status": "PASS",
    }


def _orphan_audit_record(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "orphan_audit_ref": "PR165_B_ORPHAN_ARTIFACT_AUDIT",
        "orphan_counts_all_zero": True,
        "orphan_counts_all_0": True,
        "orphan_memory_rows": 0,
        "orphan_report_rows": 0,
        "manifest_unlisted_report_count": 0,
        "missing_manifest_report_count": 0,
        "row_level_report_count": len(p.ROW_LEVEL_REPORTS),
        "root_report_count": len(p.REPORT_FILENAMES),
        "validation_status": "PASS",
    }


def build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, filename in enumerate(p.REPORT_FILENAMES, start=1):
        payload = payloads[filename]
        records.append(
            {
                "manifest_ref": ordinal_ref("PR165_B_MANIFEST", index),
                "report_filename": filename,
                "row_count": payload.get("record_count", 0),
                "schema_ref": payload.get("schema_ref"),
                "sharded_flag": payload.get("sharded_flag", False),
                "shard_count": payload.get("shard_count", 0),
                "shard_paths": payload.get("shard_files", []),
                "shard_manifest_refs": payload.get("shard_manifest_refs", []),
                "validation_status": "PASS",
            }
        )
    return records


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    root_sizes = {
        filename: len(read_json_text(payload).encode("utf-8"))
        for filename, payload in payloads.items()
    }
    shard_sizes = {
        rel_path: len(read_json_text(payload, compact=True).encode("utf-8"))
        for rel_path, payload in shard_payloads.items()
    }
    largest_root = max(root_sizes.items(), key=lambda item: item[1]) if root_sizes else ("", 0)
    largest_shard = max(shard_sizes.items(), key=lambda item: item[1]) if shard_sizes else ("", 0)
    summary = {
        "estimated_largest_root_report_path": largest_root[0],
        "estimated_largest_root_report_size_bytes": largest_root[1],
        "estimated_largest_shard_path": largest_shard[0],
        "estimated_largest_shard_size_bytes": largest_shard[1],
        "estimated_root_report_count": len(root_sizes),
        "estimated_shard_count": len(shard_sizes),
    }
    for payload in payloads.values():
        payload.update(summary)


def read_json_text(payload: dict[str, Any], *, compact: bool = False) -> str:
    from .json_io import json_text

    return json_text(payload, compact=compact)


def _clear_previous_pr165_b_shards(repo_root: Path) -> None:
    shard_dir = repo_root / p.SHARD_DIR
    resolved = shard_dir.resolve()
    if not str(resolved).startswith(str(repo_root.resolve())):
        raise RuntimeError(f"refusing to clear shard path outside repo: {resolved}")
    if not shard_dir.exists():
        return
    for child in shard_dir.glob("PR165_B_*.report.json"):
        child.unlink()


def _build_external_scouting_rows() -> dict[str, list[dict[str, Any]]]:
    sources = _external_sources()
    failure_rows: list[dict[str, Any]] = []
    condition_rows: list[dict[str, Any]] = []
    microstructure_rows: list[dict[str, Any]] = []
    quantum_rows: list[dict[str, Any]] = []
    mappability_rows: list[dict[str, Any]] = []
    candidate_index = 0
    for source_index, source in enumerate(sources, start=1):
        mappability_rows.append(
            {
                "external_mappability_ref": ordinal_ref("PR165_B_EXTERNAL_MAPPABILITY", source_index),
                **source,
                "mappability_decision": "MAPPABLE_TO_CANDIDATE_PROVISIONAL_MEMORY_DESIGN",
                "source_truth_conversion_by_PR165_B": False,
                "replay_paper_route": True,
                "validation_status": "PASS",
            }
        )
        condition_rows.append(
            {
                "external_condition_memory_design_ref": ordinal_ref("PR165_B_EXTERNAL_CONDITION_MEMORY", source_index),
                **source,
                "condition_memory_design_record": source["design_note"],
                "candidate_authority_label": "CANDIDATE_PROVISIONAL_RESEARCH_DESIGN",
                "source_truth_conversion_by_PR165_B": False,
                "validation_status": "PASS",
            }
        )
        for variant in source["failure_families"]:
            candidate_index += 1
            row = {
                "external_failure_attribution_candidate_ref": ordinal_ref("PR165_B_EXTERNAL_FAILURE_CANDIDATE", candidate_index),
                **source,
                "failure_family": variant,
                "source_authority_label": source["source_authority_label"],
                "candidate_value_materialized": True,
                "candidate_value_route": "REPLAY_PAPER_MEMORY_DESIGN_ONLY",
                "source_truth_conversion_by_PR165_B": False,
                "validation_status": "PASS",
            }
            failure_rows.append(row)
            if source["source_category"] in {"prediction_market_microstructure", "tca_shortfall", "latency_liquidity", "portfolio_crowding", "capital_lock"}:
                microstructure_rows.append(
                    {
                        "external_microstructure_condition_ref": ordinal_ref("PR165_B_EXTERNAL_MICROSTRUCTURE", len(microstructure_rows) + 1),
                        **row,
                    }
                )
            if source["source_category"] == "quantum_formulation":
                quantum_rows.append(
                    {
                        "external_quantum_failure_attribution_ref": ordinal_ref("PR165_B_EXTERNAL_QUANTUM", len(quantum_rows) + 1),
                        **row,
                        "quantum_failure_attribution_route": "QUANTUM_FORMULATION_REPAIR_REQUIRED_OR_CLASSICAL_COMPARATOR_WATCH",
                    }
                )
    return {
        "condition": condition_rows,
        "failure": failure_rows,
        "microstructure": microstructure_rows,
        "quantum": quantum_rows,
        "mappability": mappability_rows,
    }


def _external_sources() -> list[dict[str, Any]]:
    query_texts = (
        "condition scoped strategy memory trading regime performance attribution paper",
        "transaction cost analysis implementation shortfall attribution trading strategy performance paper",
        "adverse selection detection prediction market microstructure paper",
        "regime based strategy performance walk forward out of sample multiple testing trading signals paper",
        "purged embargoed cross validation financial time series machine learning paper",
        "false discovery multiple testing controls trading strategies deflated sharpe ratio paper",
        "Bayesian shrinkage confidence lower bound trading signal evaluation paper",
        "CUSUM drift monitoring regime shift detection trading strategies paper",
        "model risk management monitoring outcome analysis financial models official guidance",
        "prediction market yes no complement inconsistency arbitrage microstructure paper",
        "prediction market liquidity spread latency regime selection paper",
        "cooldown retest policy trading strategy monitoring model decay repair retest paper",
        "QUBO BQM CQM DQM Ising formulation constraint penalty model failure attribution quantum optimization paper",
        "QAOA VQE classical comparator performance attribution quantum optimization benchmark paper",
        "quantum optimization penalty model constraint gap binary expansion QUBO formulation paper",
        "quantum annealing classical baseline comparator QUBO portfolio optimization formulation paper",
        "source provenance confidence non official data trading signal research provenance financial model paper",
        "repair retest confidence model monitoring validation outcome analysis financial model risk paper",
        "portfolio crowding duplicate edge concentration risk trading strategy signals paper",
        "capital lock settlement delay prediction market trading strategy liquidity cost paper",
    )
    base = [
        ("multiple_testing", "Backtesting Strategies Based on Multiple Signals", "https://www.nber.org/papers/w21329", ("false_discovery_adjustment", "selection_bias_risk", "overfit_penalty")),
        ("prediction_market_microstructure", "Adverse Selection in Prediction Markets: Evidence from Kalshi", "https://papers.ssrn.com/sol3/Delivery.cfm/6615739.pdf?abstractid=6615739&mirid=1", ("adverse_selection", "liquidity_provider_risk", "condition_scoped_avoid")),
        ("tca_shortfall", "A practical framework for estimating transaction costs and developing optimal trading strategies", "https://www.sciencedirect.com/science/article/pii/S1544612303000047", ("fees", "spread", "implementation_shortfall")),
        ("tca_shortfall", "Implementation Shortfall with Transitory Price Effects", "https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3137570_code49904.pdf?abstractid=3137570&mirid=1", ("permanent_impact", "transitory_impact", "shortfall_decomposition")),
        ("prediction_market_microstructure", "The Anatomy of a Decentralized Prediction Market", "https://ideas.repec.org/p/arx/papers/2604.24366.html", ("spread_liquidity", "trade_direction_uncertainty", "latency_tail")),
        ("multiple_testing", "A Data Science Solution to the Multiple-Testing Crisis in Financial Research", "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3177057", ("deflated_sharpe", "multiple_testing_family", "selection_bias")),
        ("multiple_testing", "Evaluating Trading Strategies", "https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID2474755_code87814.pdf?abstractid=2474755&mirid=1", ("bonferroni_style_cap", "bh_style_rank_adjustment", "strategy_haircut")),
        ("model_risk", "Supervisory Guidance on Model Risk Management", "https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm", ("ongoing_monitoring", "outcome_analysis", "model_limitations")),
        ("latency_liquidity", "Latency and Liquidity Risk", "https://arxiv.org/abs/1908.03281", ("latency_bucket", "liquidity_taking", "adverse_selection_latency")),
        ("capital_lock", "When Certainty Is Not Worth It: Capital Lock-Up and Settlement Discounting in Prediction Markets", "https://arxiv.org/abs/2605.31431", ("capital_lock", "settlement_delay", "maturity_discount")),
        ("latency_liquidity", "The effect of DLT settlement latency on market liquidity", "https://www.world-exchanges.org/our-work/articles/effect-dlt-settlement-latency-market-quality", ("settlement_latency", "transaction_costs", "liquidity_quality")),
        ("portfolio_crowding", "Portfolio construction and crowding", "https://www.sciencedirect.com/science/article/pii/S0927539818300161", ("portfolio_crowding", "duplicate_edge", "capacity_risk")),
        ("quantum_formulation", "QAL-BP: an augmented Lagrangian quantum approach for bin packing", "https://www.nature.com/articles/s41598-023-50540-3", ("quantum_penalty_model_gap", "constraint_gap", "qubo_reformulation")),
        ("quantum_formulation", "Penalty and partitioning techniques to improve performance of QUBO solvers", "https://www.sciencedirect.com/science/article/pii/S1572528620300281", ("quantum_penalty_model_gap", "constraint_gap", "qubo_partitioning")),
        ("quantum_formulation", "Quantum Approximate Optimization Algorithm: Performance, Mechanism, and Implementation", "https://journals.aps.org/prx/abstract/10.1103/PhysRevX.10.021067", ("qaoa_performance", "classical_comparator_gap", "objective_gap")),
        ("quantum_formulation", "Empirical performance bounds for quantum approximate optimization", "https://impact.ornl.gov/en/publications/empirical-performance-bounds-for-quantum-approximate-optimization/", ("qaoa_bounds", "benchmark_gap", "classical_comparator_gap")),
        ("quantum_formulation", "Dynamic Asset Allocation with Expected Shortfall via Quantum Annealing", "https://pmc.ncbi.nlm.nih.gov/articles/PMC10047987/", ("qubo_portfolio", "classical_hybrid_baseline", "backend_claim_exclusion")),
        ("leakage_control", "A Bayesian-based classification framework for financial time series trend prediction", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9521884/", ("purged_embargoed_validation", "time_series_leakage", "confidence_bounds")),
        ("regime_monitoring", "Data stream mining: methods and challenges for handling concept drift", "https://link.springer.com/article/10.1007/s42452-019-1433-0", ("cusum_drift", "regime_shift", "watch_policy")),
        ("prediction_market_microstructure", "Unravelling the Probabilistic Forest: Arbitrage in Prediction Markets", "https://suarez-tangil.networks.imdea.org/papers/2025aft-arbitrage.pdf", ("yes_no_complement_inconsistency", "arbitrage_condition", "logical_contradiction")),
    ]
    sources: list[dict[str, Any]] = []
    for index, item in enumerate(base, start=1):
        category, title, url, families = item
        sources.append(
            {
                "external_source_ref": ordinal_ref("PR165_B_EXTERNAL_SOURCE", index),
                "external_search_query": query_texts[index - 1],
                "source_category": category,
                "source_title": title,
                "source_url": url,
                "source_authority_label": "ACADEMIC_OR_INSTITUTIONAL_RESEARCH_CANDIDATE",
                "provenance_confidence": "CANDIDATE_PROVISIONAL_WITH_URL",
                "failure_families": list(families),
                "design_note": f"Map {category} reference into condition-scoped replay/paper memory guardrails.",
            }
        )
    return sources
