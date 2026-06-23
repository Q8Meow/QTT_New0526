#!/usr/bin/env python3
"""Central constants for PR168-RANK3 RP3 evidence-backed stack ranking."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
SHARD_ROOT = GENERATED_ROOT / "rank3"

TOOL_NAME = "tools/build_pr168_rank3.py"
VALIDATE_TOOL_NAME = "tools/validate_pr168_rank3.py"
REPORT_VERSION = "PR168-RANK3-v4.0"
CREATED_AT_UTC = "2026-06-22T00:00:00Z"
BRANCH_NAME = "pr168-rank3-rp3-evidence-stack-ranking"
PR238_MERGE_COMMIT = "3b2be0cea9846ad5e858978bffd7df6be96256f6"
LATEST_MAIN_RUN_ID = "27983624772"

PREFERRED_MAX_PATH = 180
WARN_PATH = 200
FAIL_PATH = 240

EXPECTED_RP3_COMPUTABLE_FORMULA_COUNT = 35
EXPECTED_RP3_CANONICAL_FORMULA_COUNT = 47
EXPECTED_RP3_EXPRESSION_REPAIR_COUNT = 7
EXPECTED_RP3_SOURCE_REVIEW_COUNT = 5
EXPECTED_RP3_DATA_REPAIR_COUNT = 0
EXPECTED_RP3_TOP_LEVEL_REPORT_COUNT = 106
EXPECTED_RP3_ROW_SHARD_FAMILY_COUNT = 50
EXPECTED_RP3_TARGETED_TEST_COUNT = 56

AUTHORITY_CLASS = "RANK3_REPLAY_PAPER_CANDIDATE_NON_PROOF"

AUTHORITY_FALSE_FLAGS = {
    "manual_edit_allowed_flag": False,
    "live_authority_created_flag": False,
    "profit_evidence_created_flag": False,
    "source_truth_acceptance_created_flag": False,
    "connector_semantic_binding_created_flag": False,
    "connector_binding_created_flag": False,
    "private_state_access_created_flag": False,
    "cash_access_created_flag": False,
    "private_state_or_cash_access_created_flag": False,
    "order_authority_created_flag": False,
    "live_order_authority_flag": False,
    "private_cash_receipt_created_flag": False,
    "live_order_receipt_created_flag": False,
    "quantum_backend_execution_flag": False,
    "quantum_advantage_claim_flag": False,
    "qtt_sha_or_atomicrows_hash_authority_flag": False,
    "champion_allowed_flag": False,
    "live_candidate_allowed_flag": False,
    "profit_evidence_flag": False,
}

FORBIDDEN_STATE_VALUES = {
    "REAL_POSITIVE",
    "REAL_NEGATIVE",
    "REAL_NO_TRADE_DOMINANT",
    "CHAMPION",
    "LIVE_CANDIDATE",
    "LIVE_READY",
    "PROFIT_PROOF",
    "SOURCE_TRUTH_ACCEPTED_BY_RANK3",
    "CONNECTOR_BOUND_BY_RANK3",
    "PRIVATE_STATE_CONFIRMED_BY_RANK3",
    "CASH_ACCESS_CREATED_BY_RANK3",
    "ORDER_AUTHORITY_CREATED_BY_RANK3",
    "QUANTUM_BACKEND_EXECUTED_BY_RANK3",
    "QUANTUM_ADVANTAGE_PROVEN_BY_RANK3",
    "QTT_SHA_OR_ATOMICROWS_HASH_AUTHORITY",
}

DOWNSTREAM_PRS = [
    "PR168-RANK4",
    "PR168-RP4",
    "PR165-B",
    "PR162E-Q",
    "PR166-Q",
    "DATA1B",
    "SOURCE-PROVENANCE",
    "DASHBOARD-OPERATOR",
]

VALIDATOR_REFS = [VALIDATE_TOOL_NAME, "tools/pr168_rank3_validator.py"]
TEST_REFS = ["tests/pr168_rank3"]

ROUTES = {
    "input": {
        "owning_agent": "rank3_input_consumption_agent",
        "consumer_agents": ["rank3_ranking_agent", "governance_validation_agent"],
    },
    "repair": {
        "owning_agent": "rank3_pre_rank_repair_agent",
        "consumer_agents": ["MAP4_formula_repair_agent", "RP4_retest_agent", "source_provenance_agent", "DATA1B_repair_agent"],
    },
    "source": {
        "owning_agent": "source_provenance_agent",
        "consumer_agents": ["rank3_ranking_agent", "RP4_retest_agent", "dashboard_operator_agent"],
    },
    "rank": {
        "owning_agent": "rank3_ranking_agent",
        "consumer_agents": ["RANK4_selection_agent", "RP4_retest_agent", "portfolio_risk_agent"],
    },
    "risk": {
        "owning_agent": "rank3_risk_model_agent",
        "consumer_agents": ["rank3_ranking_agent", "RANK4_selection_agent", "DATA1B_repair_agent"],
    },
    "portfolio": {
        "owning_agent": "rank3_portfolio_agent",
        "consumer_agents": ["RANK4_selection_agent", "PR165B_memory_agent", "dashboard_operator_agent"],
    },
    "memory": {
        "owning_agent": "PR165B_memory_agent",
        "consumer_agents": ["rank3_ranking_agent", "RP4_retest_agent", "dashboard_operator_agent"],
    },
    "quantum": {
        "owning_agent": "quantum_optimizer_agent",
        "consumer_agents": ["PR162E_Q_mapping_agent", "PR166_Q_comparator_agent", "RANK4_selection_agent"],
    },
    "handoff": {
        "owning_agent": "rank3_handoff_agent",
        "consumer_agents": ["RANK4_selection_agent", "RP4_retest_agent", "PR165B_memory_agent", "DATA1B_repair_agent"],
    },
    "agent": {
        "owning_agent": "governance_validation_agent",
        "consumer_agents": ["rank3_ranking_agent", "dashboard_operator_agent", "operator_review_agent"],
    },
    "operator": {
        "owning_agent": "dashboard_operator_agent",
        "consumer_agents": ["operator_review_agent", "governance_validation_agent"],
    },
}

REPORT_ALIASES: "OrderedDict[str, str]" = OrderedDict(
    (name.removesuffix(".report.json"), name)
    for name in [
        "PR168_RANK3_Input.report.json",
        "PR168_RANK3_RP3ItemAccounting.report.json",
        "PR168_RANK3_RP3ReportInventory.report.json",
        "PR168_RANK3_RP3ShardFamilyIndex.report.json",
        "PR168_RANK3_UpstreamValidationHistory.report.json",
        "PR168_RANK3_EvidenceUniverse.report.json",
        "PR168_RANK3_EvidenceCompleteness.report.json",
        "PR168_RANK3_RP3Consumption.report.json",
        "PR168_RANK3_MissingEvidence.report.json",
        "PR168_RANK3_ExpressionRepairAttempt.report.json",
        "PR168_RANK3_ExpressionRepairResolution.report.json",
        "PR168_RANK3_RepairedFormulaExecReceipt.report.json",
        "PR168_RANK3_RepairedFormulaToPnLMap.report.json",
        "PR168_RANK3_RepairedFormulaMiniReplay.report.json",
        "PR168_RANK3_RepairedFormulaRankEligibility.report.json",
        "PR168_RANK3_SourceProvenanceAttempt.report.json",
        "PR168_RANK3_SourceProvenanceResolution.report.json",
        "PR168_RANK3_SourceCandidateUse.report.json",
        "PR168_RANK3_SourceProvenancePenalty.report.json",
        "PR168_RANK3_SourceProvenanceRepair.report.json",
        "PR168_RANK3_RepairBeforeRankPromotion.report.json",
        "PR168_RANK3_MiniRP3Recompute.report.json",
        "PR168_RANK3_NoTradeUniverse.report.json",
        "PR168_RANK3_NoTradeCompetition.report.json",
        "PR168_RANK3_NoTradeDominance.report.json",
        "PR168_RANK3_FeatureMatrix.report.json",
        "PR168_RANK3_NormalizedScores.report.json",
        "PR168_RANK3_ComponentScores.report.json",
        "PR168_RANK3_EvidenceTierWeights.report.json",
        "PR168_RANK3_SparseMatrix.report.json",
        "PR168_RANK3_RankScoreLineage.report.json",
        "PR168_RANK3_ExecutionAdjustedRank.report.json",
        "PR168_RANK3_LCBRank.report.json",
        "PR168_RANK3_TCARank.report.json",
        "PR168_RANK3_FillLatencyCapacityRank.report.json",
        "PR168_RANK3_FDRModelRiskRank.report.json",
        "PR168_RANK3_RobustUtility.report.json",
        "PR168_RANK3_HurdleGateAudit.report.json",
        "PR168_RANK3_RankStabilityStress.report.json",
        "PR168_RANK3_EvidenceReliabilityCalibration.report.json",
        "PR168_RANK3_PairwiseDominance.report.json",
        "PR168_RANK3_ParetoFrontier.report.json",
        "PR168_RANK3_TournamentRank.report.json",
        "PR168_RANK3_RobustMinimax.report.json",
        "PR168_RANK3_EvidenceShrinkage.report.json",
        "PR168_RANK3_ScenarioRank.report.json",
        "PR168_RANK3_RegimeRank.report.json",
        "PR168_RANK3_PortfolioRank.report.json",
        "PR168_RANK3_MarginalUtility.report.json",
        "PR168_RANK3_Diversification.report.json",
        "PR168_RANK3_CrowdingCapacity.report.json",
        "PR168_RANK3_CandidateBatchAssembly.report.json",
        "PR168_RANK3_FormulaContributionUse.report.json",
        "PR168_RANK3_StackAttributionUse.report.json",
        "PR168_RANK3_AblationUse.report.json",
        "PR168_RANK3_LearningFeedback.report.json",
        "PR168_RANK3_AgentLearningMemory.report.json",
        "PR168_RANK3_AgentLearningFeatureDelta.report.json",
        "PR168_RANK3_RetestCooldown.report.json",
        "PR168_RANK3_MemoryWritePlan.report.json",
        "PR168_RANK3_RankTiers.report.json",
        "PR168_RANK3_ChallengerSeeds.report.json",
        "PR168_RANK3_ChampionCandidateSeeds.report.json",
        "PR168_RANK3_SelectionAudit.report.json",
        "PR168_RANK3_RealProofBlocker.report.json",
        "PR168_RANK3_WeakNegativeRepair.report.json",
        "PR168_RANK3_NoTradeDominatedRepair.report.json",
        "PR168_RANK3_FragilityRepair.report.json",
        "PR168_RANK3_DataSourceRepair.report.json",
        "PR168_RANK3_RP4RetestQueue.report.json",
        "PR168_RANK3_RepairPriorityRanking.report.json",
        "PR168_RANK3_RepairExpectedImpact.report.json",
        "PR168_RANK3_RepairEV.report.json",
        "PR168_RANK3_QRankObjective.report.json",
        "PR168_RANK3_QRankConstraints.report.json",
        "PR168_RANK3_QRankCoefficients.report.json",
        "PR168_RANK3_QRankFallback.report.json",
        "PR168_RANK3_QRankInterpret.report.json",
        "PR168_RANK3_QBatchSelectionProof.report.json",
        "PR168_RANK3_ToRANK4.report.json",
        "PR168_RANK3_ToRP4.report.json",
        "PR168_RANK3_ToPR165B.report.json",
        "PR168_RANK3_ToPR162EQ.report.json",
        "PR168_RANK3_ToDATA1B.report.json",
        "PR168_RANK3_ToSourceProvenance.report.json",
        "PR168_RANK3_Dashboard.report.json",
        "PR168_RANK3_AgentDAG.report.json",
        "PR168_RANK3_EveryValue.report.json",
        "PR168_RANK3_Operator.report.json",
        "PR168_RANK3_OnlineVerifyCoverage.report.json",
        "PR168_RANK3_WebSourceUse.report.json",
        "PR168_RANK3_EndpointDrift.report.json",
        "PR168_RANK3_FileAliases.report.json",
        "PR168_RANK3_PathAudit.report.json",
        "PR168_RANK3_FinalSummary.report.json",
    ]
)

ROW_SHARDS: "OrderedDict[str, str]" = OrderedDict(
    [
        ("rp3_item_accounting", "rp3_item_accounting_rows.jsonl"),
        ("rp3_report_inventory", "rp3_report_inventory_rows.jsonl"),
        ("rp3_shard_family", "rp3_shard_family_rows.jsonl"),
        ("upstream_validation_history", "upstream_validation_history_rows.jsonl"),
        ("expression_repair_attempt", "expression_repair_attempt_rows.jsonl"),
        ("expression_repair_resolution", "expression_repair_resolution_rows.jsonl"),
        ("repaired_formula_exec_receipt", "repaired_formula_exec_receipt_rows.jsonl"),
        ("repaired_formula_to_pnl", "repaired_formula_to_pnl_rows.jsonl"),
        ("repaired_formula_mini_replay", "repaired_formula_mini_replay_rows.jsonl"),
        ("repaired_formula_rank_eligibility", "repaired_formula_rank_eligibility_rows.jsonl"),
        ("source_provenance_attempt", "source_provenance_attempt_rows.jsonl"),
        ("source_provenance_resolution", "source_provenance_resolution_rows.jsonl"),
        ("source_candidate_use", "source_candidate_use_rows.jsonl"),
        ("source_provenance_penalty", "source_provenance_penalty_rows.jsonl"),
        ("source_provenance_repair", "source_provenance_repair_rows.jsonl"),
        ("mini_rp3_recompute", "mini_rp3_recompute_rows.jsonl"),
        ("evidence_universe", "evidence_universe_rows.jsonl"),
        ("evidence_completeness", "evidence_completeness_rows.jsonl"),
        ("rp3_consumption", "rp3_consumption_rows.jsonl"),
        ("missing_evidence", "missing_evidence_rows.jsonl"),
        ("no_trade_competition", "no_trade_competition_rows.jsonl"),
        ("feature_matrix", "feature_matrix_rows.jsonl"),
        ("normalized_score", "normalized_score_rows.jsonl"),
        ("component_score", "component_score_rows.jsonl"),
        ("evidence_tier_weight", "evidence_tier_weight_rows.jsonl"),
        ("sparse_matrix", "sparse_matrix_rows.jsonl"),
        ("rank_score_lineage", "rank_score_lineage_rows.jsonl"),
        ("execution_adjusted_rank", "execution_adjusted_rank_rows.jsonl"),
        ("lcb_rank", "lcb_rank_rows.jsonl"),
        ("tca_rank", "tca_rank_rows.jsonl"),
        ("fill_latency_capacity_rank", "fill_latency_capacity_rank_rows.jsonl"),
        ("fdr_model_risk", "fdr_model_risk_rows.jsonl"),
        ("hurdle_gate", "hurdle_gate_rows.jsonl"),
        ("rank_stability_stress", "rank_stability_stress_rows.jsonl"),
        ("evidence_reliability", "evidence_reliability_rows.jsonl"),
        ("pairwise_dominance", "pairwise_dominance_rows.jsonl"),
        ("pareto_frontier", "pareto_frontier_rows.jsonl"),
        ("tournament_rank", "tournament_rank_rows.jsonl"),
        ("robust_minimax", "robust_minimax_rows.jsonl"),
        ("evidence_shrinkage", "evidence_shrinkage_rows.jsonl"),
        ("scenario_rank", "scenario_rank_rows.jsonl"),
        ("regime_rank", "regime_rank_rows.jsonl"),
        ("portfolio_rank", "portfolio_rank_rows.jsonl"),
        ("marginal_utility", "marginal_utility_rows.jsonl"),
        ("candidate_batch", "candidate_batch_rows.jsonl"),
        ("learning_feedback", "learning_feedback_rows.jsonl"),
        ("agent_memory", "agent_memory_rows.jsonl"),
        ("rank_tier", "rank_tier_rows.jsonl"),
        ("challenger_seed", "challenger_seed_rows.jsonl"),
        ("champion_candidate_seed", "champion_candidate_seed_rows.jsonl"),
        ("repair_route", "repair_route_rows.jsonl"),
        ("repair_priority", "repair_priority_rows.jsonl"),
        ("q_rank", "q_rank_rows.jsonl"),
        ("downstream_handoff", "downstream_handoff_rows.jsonl"),
        ("every_value", "every_value_rows.jsonl"),
        ("operator_action", "operator_action_rows.jsonl"),
        ("online_verify", "online_verify_rows.jsonl"),
    ]
)


def generated_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def report_path(report_id: str) -> Path:
    return GENERATED_ROOT / REPORT_ALIASES[report_id]


def shard_path(key: str) -> Path:
    return SHARD_ROOT / ROW_SHARDS[key]


def authority_flags() -> dict[str, bool]:
    return dict(AUTHORITY_FALSE_FLAGS)


def route_defaults(
    route_key: str,
    *,
    upstream_refs: list[str] | None = None,
    rp3_refs: list[str] | None = None,
    map3_refs: list[str] | None = None,
    data1_refs: list[str] | None = None,
    data1a_refs: list[str] | None = None,
    gfp2r_refs: list[str] | None = None,
    rp2_refs: list[str] | None = None,
    formula_refs: list[str] | None = None,
    stack_refs: list[str] | None = None,
    market_instantiation_refs: list[str] | None = None,
    formula_exec_receipt_refs: list[str] | None = None,
    formula_to_pnl_refs: list[str] | None = None,
    replay_refs: list[str] | None = None,
    paper_refs: list[str] | None = None,
    tca_refs: list[str] | None = None,
    fill_refs: list[str] | None = None,
    latency_refs: list[str] | None = None,
    capacity_refs: list[str] | None = None,
    scenario_refs: list[str] | None = None,
    no_trade_refs: list[str] | None = None,
    contribution_refs: list[str] | None = None,
    quality_refs: list[str] | None = None,
    recovery_refs: list[str] | None = None,
    pre_rank_repair_refs: list[str] | None = None,
    expression_repair_resolution_refs: list[str] | None = None,
    source_provenance_resolution_refs: list[str] | None = None,
    mini_rp3_recompute_refs: list[str] | None = None,
    quantum_refs: list[str] | None = None,
    computed_from_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    rank_evidence_refs: list[str] | None = None,
    data_provenance_refs: list[str] | None = None,
    source_provenance_refs: list[str] | None = None,
    authority_class: str = AUTHORITY_CLASS,
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    repair_route_if_gap: str | None = None,
) -> dict[str, Any]:
    route = ROUTES[route_key]
    return {
        "upstream_input_refs": list(upstream_refs or []),
        "upstream_refs": list(upstream_refs or []),
        "RP3_refs": list(rp3_refs or []),
        "MAP3_refs": list(map3_refs or []),
        "DATA1_refs": list(data1_refs or []),
        "DATA1A_refs": list(data1a_refs or []),
        "GFP2R_refs": list(gfp2r_refs or []),
        "RP2_refs_if_any": list(rp2_refs or []),
        "formula_refs": list(formula_refs or []),
        "stack_refs": list(stack_refs or []),
        "stack_refs_if_any": list(stack_refs or []),
        "market_instantiation_refs": list(market_instantiation_refs or []),
        "formula_exec_receipt_refs": list(formula_exec_receipt_refs or []),
        "formula_to_pnl_refs": list(formula_to_pnl_refs or []),
        "replay_refs": list(replay_refs or []),
        "paper_refs": list(paper_refs or []),
        "TCA_refs": list(tca_refs or []),
        "fill_refs": list(fill_refs or []),
        "latency_refs": list(latency_refs or []),
        "capacity_refs": list(capacity_refs or []),
        "scenario_refs": list(scenario_refs or []),
        "no_trade_refs": list(no_trade_refs or []),
        "contribution_refs": list(contribution_refs or []),
        "quality_refs": list(quality_refs or []),
        "recovery_refs": list(recovery_refs or []),
        "pre_rank_repair_refs": list(pre_rank_repair_refs or []),
        "expression_repair_resolution_refs": list(expression_repair_resolution_refs or []),
        "source_provenance_resolution_refs": list(source_provenance_resolution_refs or []),
        "mini_rp3_recompute_refs": list(mini_rp3_recompute_refs or []),
        "quantum_refs": list(quantum_refs or []),
        "computed_from_refs": list(computed_from_refs or []),
        "row_shard_refs_if_any": list(row_shard_refs or []),
        "rank_evidence_refs": list(rank_evidence_refs or []),
        "data_provenance_refs": list(data_provenance_refs or computed_from_refs or []),
        "source_provenance_refs_if_any": list(source_provenance_refs or []),
        "owning_agent": route["owning_agent"],
        "consumer_agents": list(route["consumer_agents"]),
        "downstream_consumers": list(route["consumer_agents"]),
        "downstream_pr_refs": list(DOWNSTREAM_PRS),
        "validator_refs": list(VALIDATOR_REFS),
        "test_refs": list(TEST_REFS),
        "authority_class": authority_class,
        "no_orphan_status": "NO_ORPHAN",
        "terminal_by_nature_flag": terminal_by_nature_flag,
        "terminal_reason_code": terminal_reason_code,
        "terminal_reason_if_terminal": terminal_reason_code,
        "repair_route_if_gap": repair_route_if_gap,
        **authority_flags(),
    }
