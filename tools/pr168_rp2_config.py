#!/usr/bin/env python3
"""Central constants for PR168-RP2-MAP2."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
SHARD_ROOT = GENERATED_ROOT / "rp2p"

TOOL_NAME = "tools/build_pr168_rp2_map2.py"
VALIDATE_TOOL_NAME = "tools/validate_pr168_rp2_map2.py"
REPORT_VERSION = "PR168-RP2-MAP2-v4.0"
CREATED_AT_UTC = "2026-06-22T00:00:00Z"
BRANCH_NAME = "pr168-rp2-map2-gfp2r-replay-paper-recompute"
PR235_MERGE_COMMIT = "156b8d741d92f84a72e2469906c5ed87c282cd05"

PREFERRED_MAX_PATH = 180
WARN_PATH_1 = 180
WARN_PATH_2 = 200
FAIL_PATH = 240

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
    "quantum_backend_execution_flag": False,
    "quantum_advantage_claim_flag": False,
    "qtt_sha_or_atomicrows_hash_authority_flag": False,
}

DOWNSTREAM_PRS = [
    "PR168-RANK2",
    "PR165-B",
    "PR167",
    "DATA1B",
    "GFP2R",
    "PR162E-Q",
]

VALIDATOR_REFS = [
    "tools/pr168_rp2_validator.py",
    "tools/validate_pr168_rp2_map2.py",
]
TEST_REFS = ["tests/pr168_rp2"]

ROUTES = {
    "map2": {
        "owning_agent": "qku_formula_materialization_agent",
        "consumer_agents": [
            "formula_execution_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "governance_validation_agent",
        ],
    },
    "formula": {
        "owning_agent": "formula_onboarding_agent",
        "consumer_agents": [
            "qku_formula_materialization_agent",
            "formula_execution_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "quantum_optimizer_agent",
        ],
    },
    "replay": {
        "owning_agent": "replay_paper_agent",
        "consumer_agents": [
            "ranking_scoring_agent",
            "risk_tca_capacity_agent",
            "dashboard_operator_agent",
        ],
    },
    "risk": {
        "owning_agent": "risk_tca_capacity_agent",
        "consumer_agents": [
            "replay_paper_agent",
            "ranking_scoring_agent",
            "governance_validation_agent",
        ],
    },
    "ranking": {
        "owning_agent": "ranking_scoring_agent",
        "consumer_agents": [
            "replay_paper_agent",
            "risk_tca_capacity_agent",
            "quantum_optimizer_agent",
            "dashboard_operator_agent",
        ],
    },
    "quantum": {
        "owning_agent": "quantum_optimizer_agent",
        "consumer_agents": [
            "ranking_scoring_agent",
            "governance_validation_agent",
            "dashboard_operator_agent",
        ],
    },
    "agent": {
        "owning_agent": "governance_validation_agent",
        "consumer_agents": [
            "replay_paper_agent",
            "ranking_scoring_agent",
            "dashboard_operator_agent",
        ],
    },
    "operator": {
        "owning_agent": "dashboard_operator_agent",
        "consumer_agents": [
            "governance_validation_agent",
            "market_data_acquisition_agent",
            "qku_formula_materialization_agent",
        ],
    },
    "source_evidence": {
        "owning_agent": "source_evidence_agent",
        "consumer_agents": [
            "market_data_acquisition_agent",
            "governance_validation_agent",
            "dashboard_operator_agent",
        ],
    },
}

REPORT_ALIASES: "OrderedDict[str, str]" = OrderedDict(
    [
        ("PR168_RP2_InputDiscovery", "PR168_RP2_Input.report.json"),
        ("PR168_RP2_GFP2RHandoffConsumptionAudit", "PR168_RP2_HandoffAudit.report.json"),
        ("PR168_RP2_AllowedDataFamilyAndAuthorityContract", "PR168_RP2_DataAuth.report.json"),
        ("PR168_RP2_MAP2_InputPromotionUniverse", "PR168_RP2_MAP2_Universe.report.json"),
        ("PR168_RP2_MAP2_CanonicalQKUFormulaBindingPromotion", "PR168_RP2_MAP2_Bind.report.json"),
        ("PR168_RP2_MAP2_ExactRepairedIdentityLedger", "PR168_RP2_MAP2_ExactID.report.json"),
        ("PR168_RP2_MAP2_ProvisionalIdentityPreservationLedger", "PR168_RP2_MAP2_ProvID.report.json"),
        ("PR168_RP2_MAP2_BindingFailureRepairQueue", "PR168_RP2_MAP2_BindFail.report.json"),
        ("PR168_RP2_MAP2_EconomicCandidateDeduplicationLedger", "PR168_RP2_MAP2_Dedupe.report.json"),
        ("PR168_RP2_MAP2_FutureFormulaOnboardingRegistrySeed", "PR168_RP2_MAP2_OnboardSeed.report.json"),
        ("PR168_RP2_ReplayPaperInputLock", "PR168_RP2_InputLock.report.json"),
        ("PR168_RP2_CandidateOrderIntentUniverse", "PR168_RP2_OrderIntent.report.json"),
        ("PR168_RP2_OrderPolicyVariantLedger", "PR168_RP2_OrderPolicy.report.json"),
        ("PR168_RP2_OrderPolicyDeduplicationAudit", "PR168_RP2_OrderDedupe.report.json"),
        ("PR168_RP2_ExactVsProvisionalReplayPaperUniverse", "PR168_RP2_IDUniverse.report.json"),
        ("PR168_RP2_ReplayExecutionLedger", "PR168_RP2_ReplayExec.report.json"),
        ("PR168_RP2_ReplayFillSimulationLedger", "PR168_RP2_ReplayFill.report.json"),
        ("PR168_RP2_ReplayPnLEvidenceLedger", "PR168_RP2_ReplayPnL.report.json"),
        ("PR168_RP2_ReplayInputGapAndRepairQueue", "PR168_RP2_ReplayGaps.report.json"),
        ("PR168_RP2_PaperOrderIntentLedger", "PR168_RP2_PaperIntent.report.json"),
        ("PR168_RP2_PaperFillSimulationLedger", "PR168_RP2_PaperFill.report.json"),
        ("PR168_RP2_PaperPortfolioLedger", "PR168_RP2_PaperPort.report.json"),
        ("PR168_RP2_PaperPnLEvidenceLedger", "PR168_RP2_PaperPnL.report.json"),
        ("PR168_RP2_PaperReceiptAudit", "PR168_RP2_PaperReceipts.report.json"),
        ("PR168_RP2_TCADecompositionLedger", "PR168_RP2_TCA.report.json"),
        ("PR168_RP2_FillProbabilityAndPartialFillLedger", "PR168_RP2_FillProb.report.json"),
        ("PR168_RP2_LatencyStalenessDecayLedger", "PR168_RP2_Latency.report.json"),
        ("PR168_RP2_CapacityCrowdingLimitLedger", "PR168_RP2_Capacity.report.json"),
        ("PR168_RP2_ImplementationShortfallCandidateLedger", "PR168_RP2_ImplShortfall.report.json"),
        ("PR168_RP2_ScenarioLadderReplayPaperLedger", "PR168_RP2_Scenarios.report.json"),
        ("PR168_RP2_ScenarioSensitivityMatrix", "PR168_RP2_SensMatrix.report.json"),
        ("PR168_RP2_ThinBookWideSpreadStressLedger", "PR168_RP2_BookStress.report.json"),
        ("PR168_RP2_StaleDataLatencyStressLedger", "PR168_RP2_StaleStress.report.json"),
        ("PR168_RP2_NoTradeBaselineComparisonLedger", "PR168_RP2_NoTrade.report.json"),
        ("PR168_RP2_CalibrationAndLCBReadinessLedger", "PR168_RP2_CalibLCB.report.json"),
        ("PR168_RP2_OverfitFDRTrialFamilyLedger", "PR168_RP2_FDR.report.json"),
        ("PR168_RP2_PurgedWalkForwardCPCVSeed", "PR168_RP2_CPCV.report.json"),
        ("PR168_RP2_DeflatedSharpeAndMultipleTestingSeed", "PR168_RP2_DSR.report.json"),
        ("PR168_RP2_PortfolioMarginalUtilityLedger", "PR168_RP2_Portfolio.report.json"),
        ("PR168_RP2_RegimeConditionedOutcomeLedger", "PR168_RP2_Regime.report.json"),
        ("PR168_RP2_To_PR165B_ConditionScopedMemoryRows", "PR168_RP2_ToPR165B.report.json"),
        ("PR168_RP2_CorrelationConcentrationCrowdingLedger", "PR168_RP2_CorrCrowd.report.json"),
        ("PR168_RP2_ReplayPaperDivergenceLedger", "PR168_RP2_Divergence.report.json"),
        ("PR168_RP2_ReplayPaperEvidenceClassification", "PR168_RP2_EvidenceClass.report.json"),
        ("PR168_RP2_ValidVsArtificialRejectionLedger", "PR168_RP2_Rejections.report.json"),
        ("PR168_RP2_RepairRetestQueue", "PR168_RP2_RetestQueue.report.json"),
        ("PR168_RP2_NegativeToPositiveRecoveryReplayPaperQueue", "PR168_RP2_RecoveryQueue.report.json"),
        ("PR168_RP2_WeakCandidateRepairDiagnosis", "PR168_RP2_WeakDiag.report.json"),
        ("PR168_RP2_OrderPolicyRepairVariantLedger", "PR168_RP2_PolicyRepair.report.json"),
        ("PR168_RP2_RetestPriorityScoringLedger", "PR168_RP2_RetestScore.report.json"),
        ("PR168_RP2_QuantumReplayPaperCandidateStackMap", "PR168_RP2_QStack.report.json"),
        ("PR168_RP2_QuantumObjectiveCoefficientConstraintLedger", "PR168_RP2_QObj.report.json"),
        ("PR168_RP2_QuantumScenarioConstraintLedger", "PR168_RP2_QScenario.report.json"),
        ("PR168_RP2_ClassicalFallbackComparatorReplayPaperLedger", "PR168_RP2_QFallback.report.json"),
        ("PR168_RP2_QuantumInterpretBackReplayPaperMap", "PR168_RP2_QInterpret.report.json"),
        ("PR168_RP2_To_PR168_RANK2_ReplayPaperEvidenceRows", "PR168_RP2_ToRANK2Evidence.report.json"),
        ("PR168_RP2_To_PR168_RANK2_NoTradeComparisonRows", "PR168_RP2_ToRANK2NoTrade.report.json"),
        ("PR168_RP2_To_PR167_OpenTradeSimulatorFeedbackRows", "PR168_RP2_ToPR167.report.json"),
        ("PR168_RP2_To_DATA1B_DataRepairQueue", "PR168_RP2_ToDATA1B.report.json"),
        ("PR168_RP2_To_GFP2R_FormulaRepairQueue", "PR168_RP2_ToGFP2RFormula.report.json"),
        ("PR168_RP2_To_GFP2R_MAP2_BindingRepairQueue", "PR168_RP2_ToGFP2RMAP2.report.json"),
        ("PR168_RP2_To_PR162E_Q_QuantumMappingRepairQueue", "PR168_RP2_ToPR162EQ.report.json"),
        ("PR168_RP2_AgentRoutingAndNoOrphanProof", "PR168_RP2_AgentNoOrphan.report.json"),
        ("PR168_RP2_DAGUpstreamDownstreamOrchestration", "PR168_RP2_DAG.report.json"),
        ("PR168_RP2_EveryValueUpstreamDownstreamCrosswalk", "PR168_RP2_ValueXwalk.report.json"),
        ("PR168_RP2_AgentConsumableReplayPaperLedger", "PR168_RP2_AgentLedger.report.json"),
        ("PR168_RP2_EndpointAssumptionDriftHandoff", "PR168_RP2_Drift.report.json"),
        ("PR168_RP2_OperatorActionMatrix", "PR168_RP2_Actions.report.json"),
        ("PR168_RP2_ReportEssentialityAndDeduplicationAudit", "PR168_RP2_ReportAudit.report.json"),
        ("PR168_RP2_FinalSummary", "PR168_RP2_Final.report.json"),
        ("PR168_RP2_EdgeAlphaCaptureReadinessMatrix", "PR168_RP2_EdgeAlpha.report.json"),
        ("PR168_RP2_ScenarioSpecificBestFormulaEvidenceSurface", "PR168_RP2_BestFormula.report.json"),
        ("PR168_RP2_FormulaPluginOnboardingContractRegistry", "PR168_RP2_FormulaContracts.report.json"),
        ("PR168_RP2_CentralizedRegistryArchitectureAudit", "PR168_RP2_CentralRegistry.report.json"),
        ("PR168_RP2_FormulaComputabilityRouteLedger", "PR168_RP2_FormulaRoutes.report.json"),
        ("PR168_RP2_RetestVariantFactoryLedger", "PR168_RP2_RetestFactory.report.json"),
        ("PR168_RP2_ConnectorConsumerNonAuthorityRoutingLedger", "PR168_RP2_ConnectorRoutes.report.json"),
        ("PR168_RP2_FileAliasLedger", "PR168_RP2_FileAliases.report.json"),
        ("PR168_RP2_PathLengthAudit", "PR168_RP2_PathAudit.report.json"),
        ("PR168_RP2_MissingAgentCrosswalkBlocker", "PR168_RP2_MissingAgents.report.json"),
        ("PR168_RP2_MissingGFP2RArtifactsBlocker", "PR168_RP2_MissingGFP2R.report.json"),
        ("PR168_RP2_OnlineVerificationNetworkUnavailableReceipt", "PR168_RP2_NetworkGap.report.json"),
        ("PR168_RP2_NoReplayPaperCandidatePossibleRootCause", "PR168_RP2_NoCandidates.report.json"),
    ]
)

ROW_SHARDS = OrderedDict(
    [
        ("map2_promote", "map2_promote.jsonl"),
        ("map2_dedupe", "map2_dedupe.jsonl"),
        ("formula_onboard", "formula_onboard.jsonl"),
        ("input_locks", "input_locks.jsonl"),
        ("order_intents", "order_intents.jsonl"),
        ("replay_exec", "replay_exec.jsonl"),
        ("paper_exec", "paper_exec.jsonl"),
        ("tca", "tca.jsonl"),
        ("scenarios", "scenarios.jsonl"),
        ("divergence", "divergence.jsonl"),
        ("rank2_rows", "rank2_rows.jsonl"),
        ("memory_rows", "memory_rows.jsonl"),
        ("q_stack", "q_stack.jsonl"),
        ("actions", "actions.jsonl"),
        ("formula_contracts", "formula_contracts.jsonl"),
        ("edge_alpha", "edge_alpha.jsonl"),
        ("retest_variants", "retest_variants.jsonl"),
        ("connector_routes", "connector_routes.jsonl"),
    ]
)

ORDER_POLICIES = [
    "NO_TRADE_BASELINE",
    "TAKER_CROSS_AT_BEST_AVAILABLE",
    "MAKER_JOIN_BEST_BID_OR_ASK",
    "MAKER_IMPROVE_BY_ONE_TICK_IF_ALLOWED",
    "PASSIVE_WAIT_THEN_CANCEL",
    "PASSIVE_WAIT_THEN_CROSS_IF_EDGE_REMAINS",
    "CANCEL_REPLACE_ON_STALE_BOOK",
    "REDUCED_SIZE_FOR_DEPTH",
    "BOTH_SIDE_HYPOTHESIS_YES_NO_ONLY_WHEN_FORMULA_ALLOWS",
]

INTENT_POLICIES = [policy for policy in ORDER_POLICIES if not policy.startswith("BOTH_SIDE")]

ORDER_SIZE_BUCKETS = {
    "size_bucket_tiny": 1.0,
    "size_bucket_small": 5.0,
    "size_bucket_depth_capped": 10.0,
}

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
    "FORMULA_INPUT_REPAIR_PENDING",
]

COMPUTABILITY_ROUTES = [
    "COMPUTABLE_NOW_REPLAY_PAPER_CANDIDATE",
    "COMPUTABLE_AFTER_MAP2_BINDING_REPAIR",
    "COMPUTABLE_AFTER_FORMULA_INPUT_REPAIR",
    "COMPUTABLE_AFTER_DATA_REQUIREMENT_REPAIR",
    "COMPUTABLE_AFTER_SOURCE_EVIDENCE_REVIEW",
    "COMPUTABLE_AFTER_AUTH_OR_SUBSCRIPTION_SETUP",
    "RESEARCH_ONLY_CANDIDATE",
    "STRUCTURALLY_NOT_COMPUTABLE_WITH_PROOF",
]

OFFICIAL_DOC_URLS = [
    "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
    "https://docs.kalshi.com/api-reference/market/get-trades",
    "https://docs.kalshi.com/getting_started/historical_data",
    "https://docs.polymarket.com/api-reference/market-data/get-order-book",
    "https://docs.polymarket.com/api-reference/markets/get-prices-history",
    "https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets",
    "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
    "https://docs.dwavequantum.com/en/latest/concepts/models.html",
]

REQUIRED_GFP2R_REPORTS = [
    "PR168_GFP2R_FinalSummary.report.json",
    "PR168_GFP2R_InputDiscovery.report.json",
    "PR168_GFP2R_DATA1AConsumptionAudit.report.json",
    "PR168_GFP2R_AllowedDataFamilyContractConsumption.report.json",
    "PR168_GFP2R_QKUFormulaMappingRepairLedger.report.json",
    "PR168_GFP2R_DataConsumerToQKUFormulaBridge.report.json",
    "PR168_GFP2R_ExactCandidateComputeEligibility.report.json",
    "PR168_GFP2R_ProvisionalDataConsumerComputeEligibility.report.json",
    "PR168_GFP2R_CandidateFormulaExecutionLedger.report.json",
    "PR168_GFP2R_ProvisionalDataConsumerComputeLedger.report.json",
    "PR168_GFP2R_CandidateNumericEvidenceLedger.report.json",
    "PR168_GFP2R_To_PR168_RP2_CandidateFormulaRecomputeRows.report.json",
    "PR168_GFP2R_To_PR168_RANK2_CandidateRankingRows.report.json",
    "PR168_GFP2R_AgentRoutingAndNoOrphanProof.report.json",
    "PR168_GFP2R_EveryValueUpstreamDownstreamCrosswalk.report.json",
]

REQUIRED_GFP2R_SHARDS = [
    "pr168_gfp2r_candidate_compute/rp2_handoff_rows.jsonl",
    "pr168_gfp2r_candidate_compute/rp2_handoff_rows.manifest.json",
    "pr168_gfp2r_candidate_compute/formula_execution_rows.jsonl",
    "pr168_gfp2r_candidate_compute/provisional_compute_rows.jsonl",
    "pr168_gfp2r_candidate_compute/candidate_numeric_evidence_rows.jsonl",
    "pr168_gfp2r_candidate_compute/break_even_threshold_rows.jsonl",
    "pr168_gfp2r_candidate_compute/mapping_repair_rows.jsonl",
    "pr168_gfp2r_candidate_compute/rank2_handoff_rows.jsonl",
]

REQUIRED_DATA1A_REPORTS = [
    "PR168_DATA1A_FinalSummary.report.json",
    "PR168_DATA1A_GFP2RAllowedDataFamilyContract.report.json",
    "PR168_DATA1A_HistoricalFullBookTruthLedger.report.json",
    "PR168_DATA1A_AgentRoutingAndNoOrphanProof.report.json",
]

REQUIRED_DATA1_REPORTS = [
    "PR168_DATA1_FinalSummary.report.json",
    "PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse.report.json",
    "PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch.report.json",
    "PR168_DATA1_NormalizedMarketDataFeatureRegistry.report.json",
]

REQUIRED_AGENT_REPORTS = [
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
]


def report_path(report_id: str) -> Path:
    return GENERATED_ROOT / REPORT_ALIASES[report_id]


def shard_path(key: str) -> Path:
    return SHARD_ROOT / ROW_SHARDS[key]


def generated_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def authority_flags() -> dict[str, bool]:
    return dict(AUTHORITY_FALSE_FLAGS)


def route_defaults(
    route_key: str,
    *,
    upstream_refs: list[str] | None = None,
    gfp2r_refs: list[str] | None = None,
    map2_refs: list[str] | None = None,
    data1a_refs: list[str] | None = None,
    data1_refs: list[str] | None = None,
    formula_refs: list[str] | None = None,
    qku_refs: list[str] | None = None,
    order_intent_refs: list[str] | None = None,
    replay_refs: list[str] | None = None,
    paper_refs: list[str] | None = None,
    scenario_refs: list[str] | None = None,
    tca_refs: list[str] | None = None,
    no_trade_refs: list[str] | None = None,
    quantum_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    numeric_evidence_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    computed_from_refs: list[str] | None = None,
    authority_class: str = "PR168_RP2_CANDIDATE_ONLY_NON_PROOF",
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    repair_route_if_gap: str | None = None,
) -> dict[str, Any]:
    route = ROUTES[route_key]
    return {
        "upstream_input_refs": list(upstream_refs or []),
        "upstream_refs": list(upstream_refs or []),
        "GFP2R_refs": list(gfp2r_refs or []),
        "MAP2_refs_if_any": list(map2_refs or []),
        "DATA1A_refs": list(data1a_refs or []),
        "DATA1_refs": list(data1_refs or []),
        "formula_refs": list(formula_refs or []),
        "qku_refs_if_available": list(qku_refs or []),
        "order_intent_refs": list(order_intent_refs or []),
        "replay_refs": list(replay_refs or []),
        "paper_refs": list(paper_refs or []),
        "scenario_refs": list(scenario_refs or []),
        "TCA_refs": list(tca_refs or []),
        "no_trade_refs": list(no_trade_refs or []),
        "quantum_refs": list(quantum_refs or []),
        "row_shard_refs_if_any": list(row_shard_refs or []),
        "numeric_evidence_refs": list(numeric_evidence_refs or []),
        "data_provenance_refs": list(provenance_refs or []),
        "computed_from_refs": list(computed_from_refs or []),
        "owning_agent": route["owning_agent"],
        "consumer_agents": list(route["consumer_agents"]),
        "downstream_consumers": list(route["consumer_agents"]),
        "downstream_pr_refs": list(DOWNSTREAM_PRS),
        "validator_refs": list(VALIDATOR_REFS),
        "test_refs": list(TEST_REFS),
        "no_orphan_status": "NO_ORPHAN_ROUTED",
        "terminal_by_nature_flag": terminal_by_nature_flag,
        "terminal_reason_code": terminal_reason_code,
        "repair_route_if_gap": repair_route_if_gap,
        "authority_class": authority_class,
        **authority_flags(),
    }
