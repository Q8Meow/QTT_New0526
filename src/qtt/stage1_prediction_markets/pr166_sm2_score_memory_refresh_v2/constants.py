"""Constants for PR166-SM2 report generation and validation."""

from __future__ import annotations

from pathlib import Path
import re

PR_ID = "PR166-SM2"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-sm2-score-memory-refresh-v2"
CREATED_AT_UTC = "2026-06-13T00:00:00Z"
AUTHORITY_CLASS = "PR166_SM2_REPLAY_PAPER_SCORE_MEMORY_REFRESH_V2_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_SM2_AUTHORITY_BOUNDARY::SCORE_MEMORY_REFRESH_V2_"
    "REPLAY_PAPER_ONLY_NO_LIVE_SOURCE_TRUTH_CONNECTOR_BINDING_PROFIT_OR_QUANTUM_BACKEND"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_sm2_score_memory_refresh_v2.py"
BUILDER_REF = "tools/build_pr166_sm2_score_memory_refresh_v2.py"
MANIFEST_REF = "PR166_SM2_ReportManifest.report.json"
NOT_APPLICABLE_ID = "NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"
DEFAULT_SHARD_ROW_TARGET = 1000

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr166_sm2_shards"
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2"
)

UPSTREAM_PR_REFS: tuple[str, ...] = (
    "PR166-S2",
    "PR166-SF",
    "PR166-S",
    "PR166-SM",
    "PR165-D2",
    "PR165-D",
    "PR165-C",
    "PR165-B",
    "PR165",
    "PR164",
)

DOWNSTREAM_PR_REFS: tuple[str, ...] = (
    "PR165-D3",
    "PR165-D_SELECTION_REFRESH_V3",
    "PR166-SF-R2",
    "PR166-Q",
    "PR162E-Q",
    "PR162D-R3",
    "PR162E",
    "PR162F",
    "PR167",
    "PR168",
    "PR169",
    "PR170",
    "PR171",
    "PR172",
    "PR173",
    "PR174",
    "PR175",
    "PR176",
    "PR177",
    "PR178",
    "PR179",
    "PR180",
    "PR181",
    "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
    "TERMINAL_BY_NATURE_WITH_REASON",
)

FUTURE_CONNECTOR_PR_REFS: tuple[str, ...] = (
    "PR174",
    "PR175",
    "PR176",
    "PR177",
    "PR178",
    "PR179",
    "PR180",
    "PR181",
)

SCORE_WEIGHTS = {
    "normalized_replay_paper_net_edge_after_costs": 0.18,
    "edge_lower_confidence_bound": 0.12,
    "result_confidence_score": 0.09,
    "fill_realism_score": 0.08,
    "calibration_score": 0.08,
    "condition_regime_match_score": 0.07,
    "tca_quality_score": 0.06,
    "evidence_depth_score": 0.05,
    "capacity_score": 0.05,
    "diversification_score": 0.05,
    "marginal_utility_score": 0.05,
    "quantum_comparator_readiness_score": 0.04,
    "positive_family_similarity_score": 0.04,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.05,
    "shrinkage_penalty": -0.04,
    "cost_drag_ratio": -0.04,
    "latency_drag_ratio": -0.04,
    "liquidity_drag_ratio": -0.03,
    "adverse_selection_ratio": -0.03,
    "crowding_penalty": -0.03,
    "correlation_cluster_penalty": -0.03,
    "settlement_sensitivity_score": -0.02,
    "rank_instability_adjustment": -0.02,
}

POSITIVE_EXPANSION_WEIGHTS = {
    "positive_seed_driver_match_score": 0.16,
    "positive_family_similarity_score": 0.13,
    "counterfactual_net_edge_gap_reduction_score": 0.12,
    "repair_feasibility_score": 0.10,
    "fill_realism_improvement_potential": 0.09,
    "calibration_improvement_potential": 0.08,
    "tca_root_cause_repairability_score": 0.08,
    "parameter_sensitivity_stability_score": 0.07,
    "orthogonal_edge_score": 0.06,
    "quantum_comparator_readiness_score": 0.05,
    "capacity_score": 0.05,
    "diversification_score": 0.05,
    "marginal_utility_score": 0.05,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.04,
    "shrinkage_penalty": -0.03,
    "crowding_penalty": -0.03,
    "correlation_cluster_penalty": -0.03,
    "selection_pressure_penalty": -0.03,
}

CONVERTIBLE_NEGATIVE_WEIGHTS = {
    "break_even_gap_closeness_score": 0.18,
    "dominant_root_cause_repairability_score": 0.14,
    "cost_drag_reduction_feasibility_score": 0.11,
    "fill_probability_improvement_score": 0.10,
    "calibration_improvement_potential": 0.09,
    "positive_family_similarity_score": 0.08,
    "evidence_depth_score": 0.07,
    "capacity_score": 0.06,
    "marginal_utility_score": 0.06,
    "quantum_comparator_readiness_score": 0.05,
    "false_discovery_risk_adjustment": -0.06,
    "overfit_risk_adjustment": -0.05,
    "shrinkage_penalty": -0.04,
    "crowding_penalty": -0.03,
    "selection_pressure_penalty": -0.03,
}

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_SM2_InputAudit.report.json",
    "PR166_SM2_ShardInputAudit.report.json",
    "PR166_SM2_OptionalInputs.report.json",
    "PR166_SM2_RowCountLedger.report.json",
    "PR166_SM2_RefreshPolicy.report.json",
    "PR166_SM2_ResultIntake.report.json",
    "PR166_SM2_HandoffIntake.report.json",
    "PR166_SM2_ResultQuality.report.json",
    "PR166_SM2_ScoreNormPolicy.report.json",
    "PR166_SM2_ScoreRegistry.report.json",
    "PR166_SM2_MemoryLedger.report.json",
    "PR166_SM2_RankDeltaRegistry.report.json",
    "PR166_SM2_RankAggregation.report.json",
    "PR166_SM2_PosEdgeRegistry.report.json",
    "PR166_SM2_NegEdgeRegistry.report.json",
    "PR166_SM2_NoFillMemory.report.json",
    "PR166_SM2_TCALedger.report.json",
    "PR166_SM2_CostRootLedger.report.json",
    "PR166_SM2_EdgeLCBRegistry.report.json",
    "PR166_SM2_ConfidenceRegistry.report.json",
    "PR166_SM2_CalibrationLedger.report.json",
    "PR166_SM2_Microstructure.report.json",
    "PR166_SM2_LatLiqImpact.report.json",
    "PR166_SM2_AdverseSelection.report.json",
    "PR166_SM2_SettlementLedger.report.json",
    "PR166_SM2_CapacityCrowding.report.json",
    "PR166_SM2_DiversityLedger.report.json",
    "PR166_SM2_OverfitFDRLedger.report.json",
    "PR166_SM2_RankStabilityLedger.report.json",
    "PR166_SM2_RegimeMemoryLedger.report.json",
    "PR166_SM2_CondWinnerRegistry.report.json",
    "PR166_SM2_CondLoserRegistry.report.json",
    "PR166_SM2_PosPrefLedger.report.json",
    "PR166_SM2_NegAvoidLedger.report.json",
    "PR166_SM2_FragileWatchlist.report.json",
    "PR166_SM2_ChampionRegistry.report.json",
    "PR166_SM2_ChallengerRegistry.report.json",
    "PR166_SM2_MarginalUtility.report.json",
    "PR166_SM2_EdgeDecayLedger.report.json",
    "PR166_SM2_AltExecMemory.report.json",
    "PR166_SM2_TTRiskLedger.report.json",
    "PR166_SM2_LatentEdgeLedger.report.json",
    "PR166_SM2_Counterfactual.report.json",
    "PR166_SM2_PosExpansion.report.json",
    "PR166_SM2_ConvertibleQueue.report.json",
    "PR166_SM2_FamilyRegistry.report.json",
    "PR166_SM2_RepairPriority.report.json",
    "PR166_SM2_PR166SFR2Handoff.report.json",
    "PR166_SM2_PR166QHandoff.report.json",
    "PR166_SM2_PR167Handoff.report.json",
    "PR166_SM2_PR165D3Handoff.report.json",
    "PR166_SM2_R3GapHandoff.report.json",
    "PR166_SM2_QuantumPriority.report.json",
    "PR166_SM2_QuantumStructure.report.json",
    "PR166_SM2_SelectionReady.report.json",
    "PR166_SM2_NextSelectionQueue.report.json",
    "PR166_SM2_ExternalSignals.report.json",
    "PR166_SM2_SearchReceipt.report.json",
    "PR166_SM2_AgentDutyLedger.report.json",
    "PR166_SM2_AgentTaskQueue.report.json",
    "PR166_SM2_AgentKPIAudit.report.json",
    "PR166_SM2_DashboardHandoff.report.json",
    "PR166_SM2_GovernanceHandoff.report.json",
    "PR166_SM2_CommanderHandoff.report.json",
    "PR166_SM2_MarketMemIndex.report.json",
    "PR166_SM2_PlanCrosswalk.report.json",
    "PR166_SM2_CmdActionMatrix.report.json",
    "PR166_SM2_RouteTriageMatrix.report.json",
    "PR166_SM2_ConnectorRouting.report.json",
    "PR166_SM2_ProvenanceLedger.report.json",
    "PR166_SM2_MemorySupersession.report.json",
    "PR166_SM2_ModelDriftLedger.report.json",
    "PR166_SM2_ThresholdPolicy.report.json",
    "PR166_SM2_FileConnAudit.report.json",
    "PR166_SM2_ValueConnAudit.report.json",
    "PR166_SM2_AuthorityAudit.report.json",
    "PR166_SM2_NoProfitAudit.report.json",
    "PR166_SM2_OrphanAudit.report.json",
    "PR166_SM2_StatusDriftAudit.report.json",
    "PR166_SM2_ReportManifest.report.json",
    "PR166_SM2_FinalSummary.report.json",
    "PR166_SM2_PosSeedLedger.report.json",
    "PR166_SM2_PosDriverLedger.report.json",
    "PR166_SM2_ExpansionPolicy.report.json",
    "PR166_SM2_ConversionMath.report.json",
    "PR166_SM2_BreakEvenGap.report.json",
    "PR166_SM2_ShrinkageLedger.report.json",
    "PR166_SM2_AblationLedger.report.json",
    "PR166_SM2_OrthogonalEdge.report.json",
    "PR166_SM2_SelectionPressure.report.json",
    "PR166_SM2_EvidenceDepth.report.json",
    "PR166_SM2_ExternalDedupe.report.json",
    "PR166_SM2_MemoryDAGLedger.report.json",
    "PR166_SM2_ScoreExplainLedger.report.json",
    "PR166_SM2_AllNegConvPlan.report.json",
    "PR166_SM2_EdgeUpliftLedger.report.json",
    "PR166_SM2_CostCutLedger.report.json",
    "PR166_SM2_FillBoostLedger.report.json",
    "PR166_SM2_CalibBoostLedger.report.json",
    "PR166_SM2_ParamUpliftLedger.report.json",
    "PR166_SM2_RetestBoostQueue.report.json",
    "PR166_SM2_ConversionAgentQueue.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR166_SM2_InputAudit.report.json",
        "PR166_SM2_ShardInputAudit.report.json",
        "PR166_SM2_OptionalInputs.report.json",
        "PR166_SM2_RowCountLedger.report.json",
        "PR166_SM2_RefreshPolicy.report.json",
        "PR166_SM2_ScoreNormPolicy.report.json",
        "PR166_SM2_ExternalSignals.report.json",
        "PR166_SM2_SearchReceipt.report.json",
        "PR166_SM2_AgentDutyLedger.report.json",
        "PR166_SM2_AgentKPIAudit.report.json",
        "PR166_SM2_DashboardHandoff.report.json",
        "PR166_SM2_GovernanceHandoff.report.json",
        "PR166_SM2_CommanderHandoff.report.json",
        "PR166_SM2_PlanCrosswalk.report.json",
        "PR166_SM2_CmdActionMatrix.report.json",
        "PR166_SM2_ThresholdPolicy.report.json",
        "PR166_SM2_FileConnAudit.report.json",
        "PR166_SM2_AuthorityAudit.report.json",
        "PR166_SM2_NoProfitAudit.report.json",
        "PR166_SM2_OrphanAudit.report.json",
        "PR166_SM2_StatusDriftAudit.report.json",
        "PR166_SM2_ReportManifest.report.json",
        "PR166_SM2_FinalSummary.report.json",
        "PR166_SM2_ExpansionPolicy.report.json",
        "PR166_SM2_ExternalDedupe.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(name for name in REPORT_FILENAMES if name not in SUMMARY_REPORTS)

REQUIRED_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_S2_FinalSummary.report.json",
    "PR166_S2_ReportManifest.report.json",
    "PR166_S2_InputAudit.report.json",
    "PR166_S2_InputRegistry.report.json",
    "PR166_S2_RowCountLedger.report.json",
    "PR166_S2_ShardInputAudit.report.json",
    "PR166_S2_NetEdgeResultLedger.report.json",
    "PR166_S2_EdgeLCBRegistry.report.json",
    "PR166_S2_ConfidenceRegistry.report.json",
    "PR166_S2_AttributionLedger.report.json",
    "PR166_S2_TCAResultLedger.report.json",
    "PR166_S2_CostAttribLedger.report.json",
    "PR166_S2_ImplShortfallLedger.report.json",
    "PR166_S2_FillLedger.report.json",
    "PR166_S2_NoFillLedger.report.json",
    "PR166_S2_NoFillReasonLedger.report.json",
    "PR166_S2_CalibrationLedger.report.json",
    "PR166_S2_MicrostructureLedger.report.json",
    "PR166_S2_LatLiqImpactLedger.report.json",
    "PR166_S2_AdverseSelectionLedger.report.json",
    "PR166_S2_SettlementLedger.report.json",
    "PR166_S2_WinnerRegistry.report.json",
    "PR166_S2_LoserRegistry.report.json",
    "PR166_S2_CondMemoryLedger.report.json",
    "PR166_S2_PosPrefLedger.report.json",
    "PR166_S2_NegMemoryLedger.report.json",
    "PR166_S2_ChampChallengerLedger.report.json",
    "PR166_S2_MarginalUtilityLedger.report.json",
    "PR166_S2_DiversificationLedger.report.json",
    "PR166_S2_CapacityCrowdingLedger.report.json",
    "PR166_S2_OverfitFDRLedger.report.json",
    "PR166_S2_RankStabilityLedger.report.json",
    "PR166_S2_RankAggregationLedger.report.json",
    "PR166_S2_EdgeAttributionLedger.report.json",
    "PR166_S2_EdgeDecayLedger.report.json",
    "PR166_S2_AltExecPathLedger.report.json",
    "PR166_S2_TTRiskLedger.report.json",
    "PR166_S2_QuantumHandoff.report.json",
    "PR166_S2_PR166SM2Handoff.report.json",
    "PR166_S2_PR166SFFeedback.report.json",
    "PR166_S2_R3GapHandoff.report.json",
    "PR166_S2_PR167SimHandoff.report.json",
    "PR166_S2_AgentDutyLedger.report.json",
    "PR166_S2_AgentKPIAudit.report.json",
    "PR166_S2_AgentTaskQueue.report.json",
    "PR166_S2_CommandActionMatrix.report.json",
    "PR166_S2_ConnectorRefRouting.report.json",
    "PR166_S2_RouteTriageMatrix.report.json",
    "PR166_S2_MarketResultIndex.report.json",
    "PR166_S2_MasterPlanCrosswalk.report.json",
    "PR166_SF_FinalSummary.report.json",
    "PR166_SF_ReportManifest.report.json",
    "PR166_SF_RepairedCandidateRetestQueue.report.json",
    "PR166_SF_RetestReadinessRegistry.report.json",
    "PR166_SF_RepairedPayloadRegistry.report.json",
    "PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json",
    "PR166_SF_QKUTradabilityLedger.report.json",
    "PR166_SF_QuantumRepairRouter.report.json",
    "PR166_SF_AgentDutyLedger.report.json",
    "PR166_SF_AgentRepairTaskQueue.report.json",
    "PR166_SF_CommandActionMatrix.report.json",
    "PR166_SF_ConnectorRefRouting.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
    "PR165_D2_AgentTaskQueue.report.json",
    "PR165_D2_CommandActionMatrix.report.json",
    "PR165_D2_FinalSummary.report.json",
    "PR165_D2_ReportManifest.report.json",
    "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
    "PR165_D2_RouteTriageMatrix.report.json",
    "PR165_D2_RepairAwareSelectionQueue.report.json",
    "PR165_D2_QuantumCandidatePriorityV2.report.json",
    "PR166_S_FinalSummary.report.json",
    "PR166_S_ReportManifest.report.json",
    "PR166_S_ResultAttributionLedger.report.json",
    "PR166_S_ResultConfidenceRegistry.report.json",
    "PR166_S_ExecutionCostLedger.report.json",
    "PR166_S_FeeModelLedger.report.json",
    "PR166_S_SpreadModelLedger.report.json",
    "PR166_S_SlippageModelLedger.report.json",
    "PR166_S_LatencyModelLedger.report.json",
    "PR166_S_LiquidityModelLedger.report.json",
    "PR166_S_MarketImpactModelLedger.report.json",
    "PR166_S_SettlementAssumptionLedger.report.json",
    "PR166_SM_FinalSummary.report.json",
    "PR166_SM_ReportManifest.report.json",
    "PR166_SM_RefreshedScoreRegistry.report.json",
    "PR166_SM_RefreshedMemoryLedger.report.json",
    "PR166_SM_NetEdgeRankDeltaRegistry.report.json",
    "PR166_SM_ConditionScopedWinnerRegistry.report.json",
    "PR166_SM_ConditionScopedLoserRegistry.report.json",
)

OPTIONAL_INPUT_PATTERNS: tuple[str, ...] = (
    "PR164_*.report.json",
    "PR165_*.report.json",
    "PR165_B_*.report.json",
    "PR165_C_*.report.json",
    "PR165_D_*.report.json",
)

EXPECTED_COUNTS = {
    "PR166_S2_PR166SM2Handoff.report.json": 3215,
    "PR166_S2_NetEdgeResultLedger.report.json": 3215,
    "PR166_S2_PR166SFFeedback.report.json": 3213,
    "PR166_S2_QuantumHandoff.report.json": 559,
    "PR166_S2_PR167SimHandoff.report.json": 2,
    "PR166_SF_RepairedCandidateRetestQueue.report.json": 6502,
    "PR165_D2_AgentRosterDiscoveryAudit.report.json": 8,
    "PR165_D2_AgentDutySourceCrosswalk.report.json": 8,
}

EXTERNAL_REFERENCE_ROWS: tuple[dict[str, str], ...] = (
    {
        "source_family": "QUANTCONNECT_LEAN_REALITY_MODELING",
        "source_url": "https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "fills_slippage_fees_settlement_capacity_reality_modeling",
    },
    {
        "source_family": "QUANTCONNECT_LEAN_TRADE_FILLS",
        "source_url": "https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/key-concepts",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "fill_model_spread_slippage_price_quantity_controls",
    },
    {
        "source_family": "KALSHI_BINARY_ORDERBOOK",
        "source_url": "https://docs.kalshi.com/getting_started/orderbook_responses",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "yes_no_bid_symmetry_price_complement_orderbook_semantics",
    },
    {
        "source_family": "KALSHI_MARKET_ORDERBOOK_API",
        "source_url": "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "binary_market_depth_reference_without_connector_binding",
    },
    {
        "source_family": "QISKIT_OPTIMIZATION_QUADRATIC_PROGRAM",
        "source_url": "https://qiskit-community.github.io/qiskit-optimization/tutorials/01_quadratic_program.html",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "quadratic_program_variables_objectives_constraints",
    },
    {
        "source_family": "QISKIT_OPTIMIZATION_QUBO_CONVERTER",
        "source_url": "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "qubo_conversion_compatibility_classical_comparator_structure",
    },
    {
        "source_family": "D_WAVE_OCEAN_DIMOD_MODELS",
        "source_url": "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "bqm_cqm_dqm_qubo_ising_model_family",
    },
    {
        "source_family": "APACHE_AIRFLOW_DAG_DEPENDENCIES",
        "source_url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "upstream_downstream_dag_task_dependency_receipts",
    },
    {
        "source_family": "BAILEY_LOPEZ_DE_PRADO_DEFLATED_SHARPE",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551",
        "source_authority": "RESEARCH_CANDIDATE_PROVISIONAL",
        "mapped_component": "selection_bias_multiple_testing_deflated_score_proxy",
    },
    {
        "source_family": "SCIKIT_LEARN_PROBABILITY_CALIBRATION",
        "source_url": "https://scikit-learn.org/stable/modules/calibration.html",
        "source_authority": "TECHNICAL_REFERENCE_CANDIDATE_PROVISIONAL",
        "mapped_component": "probability_calibration_brier_log_loss_discipline",
    },
)


def _schema_name(report_filename: str) -> str:
    stem = report_filename.removesuffix(".report.json")
    stem = stem.replace("PR166_SM2_", "pr166_sm2_")
    stem = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", stem)
    stem = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", stem)
    stem = stem.replace("__", "_").lower()
    return f"{stem}.schema.json"


REPORT_SCHEMA_REFS = {name: _schema_name(name) for name in REPORT_FILENAMES}
SCHEMA_FILENAMES: tuple[str, ...] = (
    "pr166_sm2_common.schema.json",
    *(REPORT_SCHEMA_REFS[name] for name in REPORT_FILENAMES),
)
