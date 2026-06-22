#!/usr/bin/env python3
"""Central constants for PR168-RP3 MAP3 replay/paper evidence."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
SHARD_ROOT = GENERATED_ROOT / "rp3"

TOOL_NAME = "tools/build_pr168_rp3.py"
VALIDATE_TOOL_NAME = "tools/validate_pr168_rp3.py"
REPORT_VERSION = "PR168-RP3-v4.0"
CREATED_AT_UTC = "2026-06-22T00:00:00Z"
BRANCH_NAME = "pr168-rp3-map3-formula-replay-paper-evidence"
PR237_MERGE_COMMIT = "6da7567d2b74572ae64e217bf5c22888ba883c43"
LATEST_MAIN_RUN_ID = "27951480144"

PREFERRED_MAX_PATH = 180
WARN_PATH = 200
FAIL_PATH = 240

EXPECTED_TOTAL_FORMULA_COUNT = 47
EXPECTED_COMPUTABLE_FORMULA_COUNT = 35
EXPECTED_EXPRESSION_REPAIR_COUNT = 7
EXPECTED_SOURCE_REVIEW_COUNT = 5
EXPECTED_DATA_REPAIR_COUNT = 0

AUTHORITY_FALSE_FLAGS = {
    "manual_edit_allowed_flag": False,
    "live_authority_created_flag": False,
    "profit_evidence_created_flag": False,
    "source_truth_acceptance_created_flag": False,
    "connector_semantic_binding_created_flag": False,
    "private_state_access_created_flag": False,
    "cash_access_created_flag": False,
    "order_authority_created_flag": False,
    "live_order_authority_flag": False,
    "private_cash_receipt_created_flag": False,
    "live_order_receipt_created_flag": False,
    "quantum_backend_execution_flag": False,
    "quantum_advantage_claim_flag": False,
    "qtt_sha_or_atomicrows_hash_authority_flag": False,
    "champion_allowed_flag": False,
    "live_candidate_allowed_flag": False,
}

DOWNSTREAM_PRS = [
    "PR168-RANK2",
    "PR165-B",
    "PR167",
    "PR162E-Q",
    "DATA1B",
    "SOURCE-EVIDENCE-REVIEW",
]

VALIDATOR_REFS = [
    "tools/pr168_rp3_validator.py",
    "tools/validate_pr168_rp3.py",
]
TEST_REFS = ["tests/pr168_rp3"]

ROUTES = {
    "formula": {
        "owning_agent": "formula_replay_paper_agent",
        "consumer_agents": [
            "formula_execution_agent",
            "replay_paper_agent",
            "rank2_evidence_agent",
            "governance_validation_agent",
        ],
    },
    "market": {
        "owning_agent": "market_instantiation_agent",
        "consumer_agents": [
            "formula_execution_agent",
            "replay_paper_agent",
            "risk_tca_capacity_agent",
            "rank2_evidence_agent",
        ],
    },
    "execution": {
        "owning_agent": "replay_paper_agent",
        "consumer_agents": [
            "risk_tca_capacity_agent",
            "rank2_evidence_agent",
            "dashboard_operator_agent",
        ],
    },
    "risk": {
        "owning_agent": "risk_tca_capacity_agent",
        "consumer_agents": [
            "replay_paper_agent",
            "rank2_evidence_agent",
            "model_risk_agent",
            "governance_validation_agent",
        ],
    },
    "rank2": {
        "owning_agent": "rank2_evidence_agent",
        "consumer_agents": [
            "model_risk_agent",
            "quantum_optimizer_agent",
            "memory_condition_agent",
            "dashboard_operator_agent",
        ],
    },
    "repair": {
        "owning_agent": "formula_repair_agent",
        "consumer_agents": [
            "source_evidence_review_agent",
            "DATA1B_repair_agent",
            "rank2_evidence_agent",
            "governance_validation_agent",
        ],
    },
    "quantum": {
        "owning_agent": "quantum_optimizer_agent",
        "consumer_agents": [
            "rank2_evidence_agent",
            "governance_validation_agent",
            "dashboard_operator_agent",
        ],
    },
    "agent": {
        "owning_agent": "governance_validation_agent",
        "consumer_agents": [
            "formula_execution_agent",
            "replay_paper_agent",
            "rank2_evidence_agent",
            "dashboard_operator_agent",
        ],
    },
    "operator": {
        "owning_agent": "dashboard_operator_agent",
        "consumer_agents": [
            "governance_validation_agent",
            "formula_repair_agent",
            "market_data_acquisition_agent",
        ],
    },
    "source": {
        "owning_agent": "source_evidence_review_agent",
        "consumer_agents": [
            "market_instantiation_agent",
            "formula_repair_agent",
            "governance_validation_agent",
        ],
    },
}

ORDER_POLICIES = [
    "NO_TRADE_BASELINE",
    "TAKER_CROSS_AT_BEST_AVAILABLE",
    "MAKER_JOIN_BEST_BID_OR_ASK",
    "MAKER_IMPROVE_BY_ONE_TICK_IF_ALLOWED",
    "PASSIVE_WAIT_THEN_CANCEL",
    "PASSIVE_WAIT_THEN_CROSS_IF_EDGE_REMAINS",
    "CANCEL_REPLACE_ON_STALE_BOOK_NONLIVE",
    "REDUCED_SIZE_FOR_DEPTH",
    "BOTH_SIDE_HYPOTHESIS_YES_NO_ONLY_WHEN_FORMULA_ALLOWS",
]

ORDER_SIZE_BUCKETS = OrderedDict(
    [
        ("size_bucket_tiny", 1.0),
        ("size_bucket_small", 5.0),
        ("size_bucket_depth_capped", 10.0),
    ]
)

SCENARIO_FAMILIES = [
    "BASE_OBSERVED",
    "NO_TRADE_BASELINE",
    "WIDE_SPREAD_PLUS_1C",
    "WIDE_SPREAD_PLUS_2C",
    "THIN_BOOK_50_PERCENT_DEPTH",
    "THIN_BOOK_25_PERCENT_DEPTH",
    "LATENCY_DELAY_SHORT",
    "LATENCY_DELAY_MEDIUM",
    "LATENCY_DELAY_LONG",
    "STALE_DATA_TTL_BREACH",
    "FEE_INCREASE_SCENARIO",
    "PARTIAL_FILL_50_PERCENT",
    "NO_FILL_SCENARIO",
    "ADVERSE_SELECTION_SHORT_HORIZON_MOVE",
    "PROBABILITY_MODEL_MISSING",
    "HISTORICAL_FULL_BOOK_MISSING",
    "CAPACITY_DEPTH_LIMIT",
    "SOURCE_ACCEPTANCE_PENDING",
    "FORMULA_EXPRESSION_REPAIR_PENDING",
]

EVIDENCE_TIERS = [
    "ACCEPTED_REAL_REPLAY_OR_CURRENT_MARKET_DATA",
    "PUBLIC_CURRENT_ORDERBOOK_CANDIDATE",
    "PUBLIC_FORWARD_L2_AFTER_CAPTURE_START_CANDIDATE",
    "PUBLIC_HISTORICAL_TRADE_CANDLE_PRICE_HISTORY_CANDIDATE",
    "MAP3_FORMULA_CONTRACT_CANDIDATE",
    "SOURCE_EVIDENCE_CANDIDATE_PENDING_REVIEW",
    "PROXY_DEFAULT_REPAIR_REQUIRED",
    "SYNTHETIC_SHAPE_TEST_ONLY_NON_PROOF",
    "UNKNOWN_OR_MISSING_REPAIR_REQUIRED",
]

ALLOWED_OUTPUT_STATES = {
    "REPLAY_POSITIVE_AFTER_COSTS_NON_PROOF",
    "REPLAY_NEGATIVE_AFTER_COSTS_NON_PROOF",
    "REPLAY_NEUTRAL_AFTER_COSTS_NON_PROOF",
    "PAPER_POSITIVE_AFTER_COSTS_NON_PROOF",
    "PAPER_NEGATIVE_AFTER_COSTS_NON_PROOF",
    "PAPER_NEUTRAL_AFTER_COSTS_NON_PROOF",
    "CANDIDATE_BEATS_NO_TRADE_NON_PROOF",
    "NO_TRADE_BEATS_CANDIDATE_NON_PROOF",
    "REPLAY_PAPER_DIVERGENCE_REPAIR_REQUIRED",
    "TCA_INPUT_GAP_REPAIR_REQUIRED",
    "FILL_INPUT_GAP_REPAIR_REQUIRED",
    "LATENCY_INPUT_GAP_REPAIR_REQUIRED",
    "CAPACITY_INPUT_GAP_REPAIR_REQUIRED",
    "CALIBRATION_SAMPLE_GAP_REPAIR_REQUIRED",
    "SOURCE_EVIDENCE_ACCEPTANCE_REQUIRED",
    "FORMULA_EXPRESSION_REPAIR_REQUIRED",
    "HISTORICAL_FULL_BOOK_DEPENDENT_REPAIR_REQUIRED",
    "RANK2_READY_CANDIDATE_NON_PROOF",
    "PR165B_MEMORY_READY_CANDIDATE_NON_PROOF",
    "QUANTUM_STACK_READY_CANDIDATE_NON_PROOF",
}

FORBIDDEN_STATE_VALUES = {
    "REAL_POSITIVE",
    "REAL_NEGATIVE",
    "REAL_NO_TRADE_DOMINANT",
    "CHAMPION",
    "LIVE_CANDIDATE",
    "PROFIT_PROOF",
    "SOURCE_TRUTH_ACCEPTED_BY_RP3",
    "CONNECTOR_BOUND_BY_RP3",
    "PRIVATE_STATE_CONFIRMED_BY_RP3",
    "CASH_ACCESS_CREATED_BY_RP3",
    "ORDER_AUTHORITY_CREATED_BY_RP3",
    "QUANTUM_BACKEND_EXECUTED_BY_RP3",
    "QUANTUM_ADVANTAGE_PROVEN_BY_RP3",
    "QTT_SHA_OR_ATOMICROWS_HASH_AUTHORITY",
}

COMPUTABLE_ROUTE = "COMPUTABLE_NOW_REPLAY_PAPER_CANDIDATE"
EXPRESSION_REPAIR_ROUTE = "COMPUTABLE_AFTER_FORMULA_INPUT_REPAIR"
SOURCE_REVIEW_ROUTE = "COMPUTABLE_AFTER_SOURCE_EVIDENCE_REVIEW"

REQUIRED_MAP3_REPORTS = [
    "PR168_MAP3_FinalSummary.report.json",
    "PR168_MAP3_FileAliases.report.json",
    "PR168_MAP3_PathAudit.report.json",
    "PR168_MAP3_PluginContracts.report.json",
    "PR168_MAP3_BindingRegistry.report.json",
    "PR168_MAP3_DataReqs.report.json",
    "PR168_MAP3_UnitNorms.report.json",
    "PR168_MAP3_ComputeRoutes.report.json",
    "PR168_MAP3_FormulaDryRun.report.json",
    "PR168_MAP3_FormulaFactory.report.json",
    "PR168_MAP3_FormulaMaterialization.report.json",
    "PR168_MAP3_QMap.report.json",
    "PR168_MAP3_QObjective.report.json",
    "PR168_MAP3_QFallback.report.json",
    "PR168_MAP3_ToRP2.report.json",
    "PR168_MAP3_ToRANK2.report.json",
    "PR168_MAP3_ToPR165B.report.json",
    "PR168_MAP3_ToPR162EQ.report.json",
    "PR168_MAP3_ToDATA1B.report.json",
    "PR168_MAP3_SourceReview.report.json",
    "PR168_MAP3_AgentDAG.report.json",
    "PR168_MAP3_EveryValue.report.json",
]

REQUIRED_AGENT_REPORTS = [
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
]

REPORT_ALIASES: "OrderedDict[str, str]" = OrderedDict(
    [
        ("PR168_RP3_InputDiscovery", "PR168_RP3_Input.report.json"),
        ("PR168_RP3_MAP3FormulaUniverseConsumption", "PR168_RP3_FormulaUniverse.report.json"),
        ("PR168_RP3_FormulaCountTruthLedger", "PR168_RP3_FormulaCountTruth.report.json"),
        ("PR168_RP3_ReplayPaperFormulaEligibilityLedger", "PR168_RP3_FormulaEligibility.report.json"),
        ("PR168_RP3_ReplayPaperInputLockLedger", "PR168_RP3_InputLocks.report.json"),
        ("PR168_RP3_FormulaExecutionPlanLedger", "PR168_RP3_FormulaExecPlan.report.json"),
        ("PR168_RP3_FormulaInputGapAndRepairQueue", "PR168_RP3_FormulaInputGaps.report.json"),
        ("PR168_RP3_UnitNormalizationReceiptLedger", "PR168_RP3_UnitNorm.report.json"),
        ("PR168_RP3_ReplayExecutionLedger", "PR168_RP3_ReplayRows.report.json"),
        ("PR168_RP3_ReplayNumericPnLEvidenceLedger", "PR168_RP3_ReplayPnL.report.json"),
        ("PR168_RP3_ReplayInputGapRepairQueue", "PR168_RP3_ReplayGaps.report.json"),
        ("PR168_RP3_PaperOrderIntentLedger", "PR168_RP3_PaperIntents.report.json"),
        ("PR168_RP3_PaperExecutionLedger", "PR168_RP3_PaperRows.report.json"),
        ("PR168_RP3_PaperNumericPnLEvidenceLedger", "PR168_RP3_PaperPnL.report.json"),
        ("PR168_RP3_PaperReceiptAudit", "PR168_RP3_PaperReceipts.report.json"),
        ("PR168_RP3_TCADecompositionLedger", "PR168_RP3_TCA.report.json"),
        ("PR168_RP3_FillProbabilityAndPartialFillLedger", "PR168_RP3_Fill.report.json"),
        ("PR168_RP3_LatencyStalenessDecayLedger", "PR168_RP3_Latency.report.json"),
        ("PR168_RP3_CapacityCrowdingLimitLedger", "PR168_RP3_Capacity.report.json"),
        ("PR168_RP3_CalibrationAndLCBReadinessLedger", "PR168_RP3_CalibLCB.report.json"),
        ("PR168_RP3_OverfitFDRTrialFamilyLedger", "PR168_RP3_FDR.report.json"),
        ("PR168_RP3_PortfolioMarginalUtilityLedger", "PR168_RP3_Portfolio.report.json"),
        ("PR168_RP3_RegimeConditionedOutcomeLedger", "PR168_RP3_Regime.report.json"),
        ("PR168_RP3_ScenarioLadderReplayPaperLedger", "PR168_RP3_Scenarios.report.json"),
        ("PR168_RP3_NoTradeBaselineComparisonLedger", "PR168_RP3_NoTrade.report.json"),
        ("PR168_RP3_FormulaScenarioRegimeComparisonLedger", "PR168_RP3_FormulaCompare.report.json"),
        ("PR168_RP3_FormulaSelectionSurfaceForRANK2", "PR168_RP3_SelectSurface.report.json"),
        ("PR168_RP3_To_PR168_RANK2_EvidenceExpansionRows", "PR168_RP3_RANK2Rows.report.json"),
        ("PR168_RP3_To_PR168_RANK2_NoTradeComparisonRows", "PR168_RP3_RANK2NoTrade.report.json"),
        ("PR168_RP3_NonComputableFormulaRepairQueue", "PR168_RP3_FormulaRepair.report.json"),
        ("PR168_RP3_SourceEvidenceReviewQueue", "PR168_RP3_SourceReview.report.json"),
        ("PR168_RP3_ExpressionRepairQueue", "PR168_RP3_ExpressionRepair.report.json"),
        ("PR168_RP3_To_DATA1B_DataRepairQueue", "PR168_RP3_DATA1BRepair.report.json"),
        ("PR168_RP3_WeakCandidateRepairDiagnosis", "PR168_RP3_WeakDiag.report.json"),
        ("PR168_RP3_RetestVariantFactoryLedger", "PR168_RP3_RetestFactory.report.json"),
        ("PR168_RP3_RecoveryQueue", "PR168_RP3_RecoveryQueue.report.json"),
        ("PR168_RP3_ValidVsArtificialRejectionLedger", "PR168_RP3_ValidVsArtificial.report.json"),
        ("PR168_RP3_QuantumReplayPaperCandidateStackMap", "PR168_RP3_QStack.report.json"),
        ("PR168_RP3_QuantumObjectiveCoefficientConstraintLedger", "PR168_RP3_QObjective.report.json"),
        ("PR168_RP3_QuantumScenarioConstraintLedger", "PR168_RP3_QConstraints.report.json"),
        ("PR168_RP3_ClassicalFallbackComparatorLedger", "PR168_RP3_QFallback.report.json"),
        ("PR168_RP3_QuantumInterpretBackMap", "PR168_RP3_QInterpret.report.json"),
        ("PR168_RP3_To_PR165B_ConditionScopedMemoryRows", "PR168_RP3_ToPR165B.report.json"),
        ("PR168_RP3_To_PR167_OpenTradeSimulatorFeedbackRows", "PR168_RP3_ToPR167.report.json"),
        ("PR168_RP3_To_PR162E_Q_QuantumMappingRows", "PR168_RP3_ToPR162EQ.report.json"),
        ("PR168_RP3_To_DATA1B_HandoffRows", "PR168_RP3_ToDATA1B.report.json"),
        ("PR168_RP3_DashboardSummary", "PR168_RP3_Dashboard.report.json"),
        ("PR168_RP3_AgentRoutingAndNoOrphanDAG", "PR168_RP3_AgentDAG.report.json"),
        ("PR168_RP3_EveryValueUpstreamDownstreamCrosswalk", "PR168_RP3_EveryValue.report.json"),
        ("PR168_RP3_OperatorActionMatrix", "PR168_RP3_Operator.report.json"),
        ("PR168_RP3_EndpointAssumptionDriftHandoff", "PR168_RP3_EndpointDrift.report.json"),
        ("PR168_RP3_FileAliasRegistry", "PR168_RP3_FileAliases.report.json"),
        ("PR168_RP3_PathAudit", "PR168_RP3_PathAudit.report.json"),
        ("PR168_RP3_FinalSummary", "PR168_RP3_FinalSummary.report.json"),
        ("PR168_RP3_FormulaExecutionReceiptLedger", "PR168_RP3_FormulaExecReceipt.report.json"),
        ("PR168_RP3_NumericCoverageLedger", "PR168_RP3_NumCoverage.report.json"),
        ("PR168_RP3_FormulaToPnLMapLedger", "PR168_RP3_FormulaToPnLMap.report.json"),
        ("PR168_RP3_EvidenceTierLedger", "PR168_RP3_EvidenceTier.report.json"),
        ("PR168_RP3_ProbabilityModelAudit", "PR168_RP3_ProbModelAudit.report.json"),
        ("PR168_RP3_CostInputAudit", "PR168_RP3_CostAudit.report.json"),
        ("PR168_RP3_FillModelAudit", "PR168_RP3_FillAudit.report.json"),
        ("PR168_RP3_RealProofBlockerLedger", "PR168_RP3_RealProofBlocker.report.json"),
        ("PR168_RP3_SparseEvidenceMatrix", "PR168_RP3_SparseMatrix.report.json"),
        ("PR168_RP3_ModelRiskLedger", "PR168_RP3_ModelRisk.report.json"),
        ("PR168_RP3_TrialFDRLedger", "PR168_RP3_TrialFDR.report.json"),
        ("PR168_RP3_CalibrationScoreLedger", "PR168_RP3_CalibScore.report.json"),
        ("PR168_RP3_LCBGapLedger", "PR168_RP3_LCBGaps.report.json"),
        ("PR168_RP3_StackDedupeLedger", "PR168_RP3_StackDedupe.report.json"),
        ("PR168_RP3_RankSurface", "PR168_RP3_RankSurface.report.json"),
        ("PR168_RP3_ChampionChallengerSeedLedger", "PR168_RP3_ChampionChallengerSeed.report.json"),
        ("PR168_RP3_MarginalUtilitySelectionLedger", "PR168_RP3_MarginalUtilitySelect.report.json"),
        ("PR168_RP3_RegimeFormulaSurface", "PR168_RP3_RegimeFormulaSurface.report.json"),
        ("PR168_RP3_AsOfTimeBarrierLedger", "PR168_RP3_AsOfBarrier.report.json"),
        ("PR168_RP3_NoLookaheadLeakageAudit", "PR168_RP3_NoLookahead.report.json"),
        ("PR168_RP3_ReplayClockLedger", "PR168_RP3_ReplayClock.report.json"),
        ("PR168_RP3_ResolutionLeakageGuard", "PR168_RP3_ResolutionGuard.report.json"),
        ("PR168_RP3_LifecycleSettlementAudit", "PR168_RP3_LifecycleAudit.report.json"),
        ("PR168_RP3_ExpectedVsRealizedPnL", "PR168_RP3_ExpectedVsRealized.report.json"),
        ("PR168_RP3_VenuePayoffNormalizationAudit", "PR168_RP3_VenueNorm.report.json"),
        ("PR168_RP3_BinaryPayoffParityLedger", "PR168_RP3_BinaryParity.report.json"),
        ("PR168_RP3_FeeTickSizeLedger", "PR168_RP3_FeeTickSize.report.json"),
        ("PR168_RP3_PayoffNormalizationLedger", "PR168_RP3_PayoffNorm.report.json"),
        ("PR168_RP3_StackComposerLedger", "PR168_RP3_StackComposer.report.json"),
        ("PR168_RP3_StackExecutionReceiptLedger", "PR168_RP3_StackExec.report.json"),
        ("PR168_RP3_FormulaStackBuilderLedger", "PR168_RP3_FormulaStackBuilder.report.json"),
        ("PR168_RP3_SuccessMetricsLedger", "PR168_RP3_SuccessMetrics.report.json"),
        ("PR168_RP3_StackAttributionLedger", "PR168_RP3_StackAttribution.report.json"),
        ("PR168_RP3_StackAblationLedger", "PR168_RP3_StackAblation.report.json"),
        ("PR168_RP3_StackRepairLedger", "PR168_RP3_StackRepair.report.json"),
        ("PR168_RP3_StackRankSurface", "PR168_RP3_StackRankSurface.report.json"),
        ("PR168_RP3_StackRANK2Rows", "PR168_RP3_StackRANK2Rows.report.json"),
        ("PR168_RP3_FormulaAttributionLedger", "PR168_RP3_FormulaAttribution.report.json"),
        ("PR168_RP3_FormulaContributionLedger", "PR168_RP3_FormulaContribution.report.json"),
        ("PR168_RP3_AblationLedger", "PR168_RP3_Ablation.report.json"),
        ("PR168_RP3_MarginalFormulaUtilityLedger", "PR168_RP3_MarginalFormulaUtility.report.json"),
        ("PR168_RP3_NegativeRecoveryLedger", "PR168_RP3_NegativeRecoveryLedger.report.json"),
        ("PR168_RP3_FormulaQualityLedger", "PR168_RP3_FormulaQuality.report.json"),
        ("PR168_RP3_TacticalNegativeRepairMatrix", "PR168_RP3_TacticalRepair.report.json"),
        ("PR168_RP3_RepairRetestCandidateStacks", "PR168_RP3_RepairRetestStacks.report.json"),
        ("PR168_RP3_FailureCauseAttribution", "PR168_RP3_FailureAttribution.report.json"),
        ("PR168_RP3_QStackSelect", "PR168_RP3_QStackSelect.report.json"),
        ("PR168_RP3_QStackCoefficients", "PR168_RP3_QStackCoefficients.report.json"),
        ("PR168_RP3_QStackFallback", "PR168_RP3_QStackFallback.report.json"),
        ("PR168_RP3_MarketInstantiationLedger", "PR168_RP3_MarketInstantiation.report.json"),
        ("PR168_RP3_OnlineVerifyCoverage", "PR168_RP3_OnlineVerifyCoverage.report.json"),
        ("PR168_RP3_WebSourceUse", "PR168_RP3_WebSourceUse.report.json"),
    ]
)

ROW_SHARDS: "OrderedDict[str, str]" = OrderedDict(
    [
        ("formula_universe", "formula_universe_rows.jsonl"),
        ("formula_eligibility", "formula_eligibility_rows.jsonl"),
        ("input_locks", "input_lock_rows.jsonl"),
        ("formula_execution", "formula_execution_rows.jsonl"),
        ("replay", "replay_rows.jsonl"),
        ("paper", "paper_rows.jsonl"),
        ("tca", "tca_rows.jsonl"),
        ("fill", "fill_rows.jsonl"),
        ("latency_capacity", "latency_capacity_rows.jsonl"),
        ("calibration_fdr", "calibration_fdr_rows.jsonl"),
        ("portfolio_regime", "portfolio_regime_rows.jsonl"),
        ("scenario", "scenario_rows.jsonl"),
        ("no_trade", "no_trade_rows.jsonl"),
        ("formula_compare", "formula_compare_rows.jsonl"),
        ("rank2_handoff", "rank2_handoff_rows.jsonl"),
        ("formula_repair", "formula_repair_rows.jsonl"),
        ("retest_variant", "retest_variant_rows.jsonl"),
        ("quantum_stack", "quantum_stack_rows.jsonl"),
        ("memory", "memory_rows.jsonl"),
        ("operator_action", "operator_action_rows.jsonl"),
        ("formula_exec_receipt", "formula_exec_receipt_rows.jsonl"),
        ("formula_to_pnl_map", "formula_to_pnl_map_rows.jsonl"),
        ("evidence_tier", "evidence_tier_rows.jsonl"),
        ("numeric_coverage", "numeric_coverage_rows.jsonl"),
        ("probability_model_audit", "probability_model_audit_rows.jsonl"),
        ("cost_audit", "cost_audit_rows.jsonl"),
        ("fill_audit", "fill_audit_rows.jsonl"),
        ("real_proof_blocker", "real_proof_blocker_rows.jsonl"),
        ("model_risk", "model_risk_rows.jsonl"),
        ("rank_surface", "rank_surface_rows.jsonl"),
        ("sparse_matrix", "sparse_matrix_rows.jsonl"),
        ("asof_barrier", "asof_barrier_rows.jsonl"),
        ("no_lookahead", "no_lookahead_rows.jsonl"),
        ("venue_norm", "venue_norm_rows.jsonl"),
        ("expected_realized", "expected_realized_rows.jsonl"),
        ("formula_stack", "formula_stack_rows.jsonl"),
        ("stack_attribution", "stack_attribution_rows.jsonl"),
        ("stack_ablation", "stack_ablation_rows.jsonl"),
        ("tactical_repair", "tactical_repair_rows.jsonl"),
        ("q_stack_select", "q_stack_select_rows.jsonl"),
        ("market_instantiation", "market_instantiation_rows.jsonl"),
        ("formula_contribution", "formula_contribution_rows.jsonl"),
        ("formula_stack_builder", "formula_stack_builder_rows.jsonl"),
        ("negative_recovery", "negative_recovery_rows.jsonl"),
        ("formula_quality", "formula_quality_rows.jsonl"),
        ("success_metrics", "success_metrics_rows.jsonl"),
        ("online_verify", "online_verify_rows.jsonl"),
        ("agent_dag", "agent_dag_rows.jsonl"),
        ("every_value", "every_value_rows.jsonl"),
        ("failure_attribution", "failure_attribution_rows.jsonl"),
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
    map3_refs: list[str] | None = None,
    rp2_refs: list[str] | None = None,
    gfp2r_refs: list[str] | None = None,
    data1a_refs: list[str] | None = None,
    data1_refs: list[str] | None = None,
    formula_refs: list[str] | None = None,
    formula_contract_refs: list[str] | None = None,
    qku_refs: list[str] | None = None,
    order_intent_refs: list[str] | None = None,
    replay_refs: list[str] | None = None,
    paper_refs: list[str] | None = None,
    scenario_refs: list[str] | None = None,
    tca_refs: list[str] | None = None,
    no_trade_refs: list[str] | None = None,
    quantum_refs: list[str] | None = None,
    computed_from_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    numeric_evidence_refs: list[str] | None = None,
    market_instantiation_refs: list[str] | None = None,
    stack_refs: list[str] | None = None,
    contribution_refs: list[str] | None = None,
    recovery_refs: list[str] | None = None,
    formula_quality_refs: list[str] | None = None,
    authority_class: str = "REPLAY_PAPER_CANDIDATE_NON_PROOF",
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    repair_route_if_gap: str | None = None,
) -> dict[str, Any]:
    route = ROUTES[route_key]
    return {
        "upstream_input_refs": list(upstream_refs or []),
        "upstream_refs": list(upstream_refs or []),
        "MAP3_refs": list(map3_refs or []),
        "RP2_refs_if_reused": list(rp2_refs or []),
        "GFP2R_refs": list(gfp2r_refs or []),
        "DATA1A_refs": list(data1a_refs or []),
        "DATA1_refs": list(data1_refs or []),
        "formula_refs": list(formula_refs or []),
        "formula_contract_refs": list(formula_contract_refs or []),
        "qku_refs_if_available": list(qku_refs or []),
        "order_intent_refs": list(order_intent_refs or []),
        "replay_refs": list(replay_refs or []),
        "paper_refs": list(paper_refs or []),
        "scenario_refs": list(scenario_refs or []),
        "TCA_refs": list(tca_refs or []),
        "no_trade_refs": list(no_trade_refs or []),
        "quantum_refs": list(quantum_refs or []),
        "computed_from_refs": list(computed_from_refs or []),
        "row_shard_refs_if_any": list(row_shard_refs or []),
        "numeric_evidence_refs": list(numeric_evidence_refs or []),
        "data_provenance_refs": list(computed_from_refs or []),
        "market_instantiation_refs_if_any": list(market_instantiation_refs or []),
        "stack_refs_if_any": list(stack_refs or []),
        "contribution_refs_if_any": list(contribution_refs or []),
        "recovery_refs_if_any": list(recovery_refs or []),
        "formula_quality_refs_if_any": list(formula_quality_refs or []),
        "owning_agent": route["owning_agent"],
        "consumer_agents": list(route["consumer_agents"]),
        "downstream_consumers": list(route["consumer_agents"]),
        "downstream_pr_refs": list(DOWNSTREAM_PRS),
        "validator_refs": list(VALIDATOR_REFS),
        "test_refs": list(TEST_REFS),
        "no_orphan_status": "NO_ORPHAN",
        "terminal_by_nature_flag": terminal_by_nature_flag,
        "terminal_reason_code": terminal_reason_code,
        "terminal_reason_if_terminal": terminal_reason_code,
        "repair_route_if_gap": repair_route_if_gap,
        "authority_class": authority_class,
        **authority_flags(),
    }
