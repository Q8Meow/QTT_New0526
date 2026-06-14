"""Constants for PR166-SF-R2 report generation and validation."""

from __future__ import annotations

from pathlib import Path
import re

PR_ID = "PR166-SF-R2"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-sf-r2-targeted-conversion-repair-retest"
CREATED_AT_UTC = "2026-06-14T00:00:00Z"
AUTHORITY_CLASS = "PR166_SF_R2_REPLAY_PAPER_TARGETED_CONVERSION_REPAIR_RETEST_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_SF_R2_AUTHORITY_BOUNDARY::REPLAY_PAPER_REPAIR_RETEST_ONLY_"
    "NO_LIVE_SOURCE_TRUTH_CONNECTOR_BINDING_PROFIT_QUANTUM_BACKEND_QTT_SHA_OR_ATOMICROWS_HASH"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
BUILDER_REF = "tools/build_pr166_sf_r2_targeted_conversion_repair_retest.py"
MANIFEST_REF = "PR166_SF_R2_ReportManifest.report.json"
NOT_APPLICABLE_ID = "NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"
DEFAULT_SHARD_ROW_TARGET = 1000

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr166_sf_r2_shards"
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr166_sf_r2_targeted_conversion_repair_retest"
)

UPSTREAM_PR_REFS: tuple[str, ...] = (
    "PR166-SM2",
    "PR166-S2",
    "PR166-SF",
    "PR165-D2",
    "PR166-S",
    "PR166-SM",
    "PR165-D",
    "PR165-C",
    "PR165-B",
    "PR165",
    "PR164",
)

DOWNSTREAM_PR_REFS: tuple[str, ...] = (
    "PR166-SM3",
    "PR166-SM_REFRESH_V3",
    "PR166-Q",
    "PR162E-Q",
    "PR162D-R3",
    "PR162E",
    "PR162F",
    "PR165-D3",
    "PR165-D_SELECTION_REFRESH_V3",
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
    "PR166-SF-R3",
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

RETEST_SCORE_WEIGHTS = {
    "normalized_repaired_net_edge_after_costs": 0.20,
    "edge_lower_confidence_bound": 0.13,
    "result_confidence_score": 0.10,
    "fill_realism_score": 0.09,
    "probability_calibration_score": 0.08,
    "before_after_uplift_score": 0.07,
    "break_even_gap_closure_score": 0.06,
    "repair_feasibility_score": 0.06,
    "capacity_score": 0.05,
    "marginal_utility_score": 0.05,
    "quantum_comparator_readiness_score": 0.04,
    "champion_challenger_stability_score": 0.04,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.05,
    "residual_cost_drag_ratio": -0.04,
    "latency_drag_ratio": -0.03,
    "liquidity_drag_ratio": -0.03,
    "adverse_selection_ratio": -0.03,
    "crowding_penalty": -0.03,
    "correlation_cluster_penalty": -0.03,
    "settlement_sensitivity_score": -0.02,
    "rank_instability_adjustment": -0.02,
}

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_SF_R2_InputAudit.report.json",
    "PR166_SF_R2_ShardInputAudit.report.json",
    "PR166_SF_R2_OptionalInputs.report.json",
    "PR166_SF_R2_RowCountLedger.report.json",
    "PR166_SF_R2_RepairPolicy.report.json",
    "PR166_SF_R2_RepairUniverse.report.json",
    "PR166_SF_R2_HandoffIntake.report.json",
    "PR166_SF_R2_AllNegIntake.report.json",
    "PR166_SF_R2_RepairPriority.report.json",
    "PR166_SF_R2_BreakEvenGap.report.json",
    "PR166_SF_R2_RepairFeasibility.report.json",
    "PR166_SF_R2_CostRepair.report.json",
    "PR166_SF_R2_FillRepair.report.json",
    "PR166_SF_R2_CalibRepair.report.json",
    "PR166_SF_R2_ParamRepair.report.json",
    "PR166_SF_R2_FormulaQKURepair.report.json",
    "PR166_SF_R2_AltExecRepair.report.json",
    "PR166_SF_R2_QuantumRepair.report.json",
    "PR166_SF_R2_RepairActionLedger.report.json",
    "PR166_SF_R2_RepairedPacketRegistry.report.json",
    "PR166_SF_R2_ComputablePayloadLedger.report.json",
    "PR166_SF_R2_MaterializedValueLedger.report.json",
    "PR166_SF_R2_RetestPolicy.report.json",
    "PR166_SF_R2_RetestUniverse.report.json",
    "PR166_SF_R2_EpisodePlan.report.json",
    "PR166_SF_R2_OrderIntentLedger.report.json",
    "PR166_SF_R2_FillLedger.report.json",
    "PR166_SF_R2_NoFillLedger.report.json",
    "PR166_SF_R2_TCALedger.report.json",
    "PR166_SF_R2_ImplShortfall.report.json",
    "PR166_SF_R2_NetEdgeLedger.report.json",
    "PR166_SF_R2_EdgeLCBRegistry.report.json",
    "PR166_SF_R2_ConfidenceRegistry.report.json",
    "PR166_SF_R2_CalibrationLedger.report.json",
    "PR166_SF_R2_Microstructure.report.json",
    "PR166_SF_R2_LatLiqImpact.report.json",
    "PR166_SF_R2_SettlementLedger.report.json",
    "PR166_SF_R2_AdverseSelection.report.json",
    "PR166_SF_R2_CapacityCrowding.report.json",
    "PR166_SF_R2_OverfitFDR.report.json",
    "PR166_SF_R2_RankStability.report.json",
    "PR166_SF_R2_BeforeAfter.report.json",
    "PR166_SF_R2_ConversionAttribution.report.json",
    "PR166_SF_R2_PosConversion.report.json",
    "PR166_SF_R2_StillNegative.report.json",
    "PR166_SF_R2_TerminalRows.report.json",
        "PR166_SF_R2_RepairFailure.report.json",
        "PR166_SF_R2_RetestBoostResult.report.json",
        "PR166_SF_R2_ChampionRegistry.report.json",
    "PR166_SF_R2_ChallengerRegistry.report.json",
    "PR166_SF_R2_RegimeMemory.report.json",
    "PR166_SF_R2_MarginalUtility.report.json",
    "PR166_SF_R2_DiversityLedger.report.json",
    "PR166_SF_R2_QuantumPriority.report.json",
    "PR166_SF_R2_QuantumStructure.report.json",
    "PR166_SF_R2_PR166QHandoff.report.json",
    "PR166_SF_R2_PR166SM3Handoff.report.json",
    "PR166_SF_R2_PR165D3Handoff.report.json",
    "PR166_SF_R2_PR167Handoff.report.json",
    "PR166_SF_R2_R3GapHandoff.report.json",
    "PR166_SF_R2_ExternalSignals.report.json",
        "PR166_SF_R2_SearchReceipt.report.json",
        "PR166_SF_R2_AgentDutyLedger.report.json",
        "PR166_SF_R2_AgentTaskQueue.report.json",
    "PR166_SF_R2_AgentKPIAudit.report.json",
    "PR166_SF_R2_DashboardHandoff.report.json",
    "PR166_SF_R2_GovernanceHandoff.report.json",
    "PR166_SF_R2_CommanderHandoff.report.json",
    "PR166_SF_R2_MarketIndex.report.json",
    "PR166_SF_R2_PlanCrosswalk.report.json",
    "PR166_SF_R2_CmdActionMatrix.report.json",
    "PR166_SF_R2_RouteTriageMatrix.report.json",
    "PR166_SF_R2_ConnectorRouting.report.json",
    "PR166_SF_R2_ProvenanceLedger.report.json",
    "PR166_SF_R2_ThresholdPolicy.report.json",
    "PR166_SF_R2_FileConnAudit.report.json",
    "PR166_SF_R2_ValueConnAudit.report.json",
    "PR166_SF_R2_AuthorityAudit.report.json",
    "PR166_SF_R2_NoProfitAudit.report.json",
    "PR166_SF_R2_OrphanAudit.report.json",
    "PR166_SF_R2_StatusDriftAudit.report.json",
    "PR166_SF_R2_ReportManifest.report.json",
    "PR166_SF_R2_FinalSummary.report.json",
    "PR166_SF_R2_RepairFrontier.report.json",
    "PR166_SF_R2_RepairAblation.report.json",
    "PR166_SF_R2_RepairSensitivity.report.json",
    "PR166_SF_R2_ConvProof.report.json",
    "PR166_SF_R2_CostFloor.report.json",
    "PR166_SF_R2_FillProbModel.report.json",
    "PR166_SF_R2_CalibUpliftProof.report.json",
    "PR166_SF_R2_ParamBoundAudit.report.json",
    "PR166_SF_R2_QuantumObjectiveMap.report.json",
    "PR166_SF_R2_HoldoutReplay.report.json",
    "PR166_SF_R2_PositiveCapacity.report.json",
    "PR166_SF_R2_RepairPortfolio.report.json",
    "PR166_SF_R2_ConversionFrontier.report.json",
    "PR166_SF_R2_LaunchCandidateFilter.report.json",
    "PR166_SF_R2_RuntimeSafetyHandoff.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR166_SF_R2_InputAudit.report.json",
        "PR166_SF_R2_ShardInputAudit.report.json",
        "PR166_SF_R2_OptionalInputs.report.json",
        "PR166_SF_R2_RowCountLedger.report.json",
        "PR166_SF_R2_RepairPolicy.report.json",
        "PR166_SF_R2_RetestPolicy.report.json",
        "PR166_SF_R2_ExternalSignals.report.json",
        "PR166_SF_R2_SearchReceipt.report.json",
        "PR166_SF_R2_AgentDutyLedger.report.json",
        "PR166_SF_R2_AgentTaskQueue.report.json",
        "PR166_SF_R2_AgentKPIAudit.report.json",
        "PR166_SF_R2_DashboardHandoff.report.json",
        "PR166_SF_R2_GovernanceHandoff.report.json",
        "PR166_SF_R2_CommanderHandoff.report.json",
        "PR166_SF_R2_MarketIndex.report.json",
        "PR166_SF_R2_PlanCrosswalk.report.json",
        "PR166_SF_R2_CmdActionMatrix.report.json",
        "PR166_SF_R2_RouteTriageMatrix.report.json",
        "PR166_SF_R2_ConnectorRouting.report.json",
        "PR166_SF_R2_ProvenanceLedger.report.json",
        "PR166_SF_R2_ThresholdPolicy.report.json",
        "PR166_SF_R2_FileConnAudit.report.json",
        "PR166_SF_R2_ValueConnAudit.report.json",
        "PR166_SF_R2_AuthorityAudit.report.json",
        "PR166_SF_R2_NoProfitAudit.report.json",
        "PR166_SF_R2_OrphanAudit.report.json",
        "PR166_SF_R2_StatusDriftAudit.report.json",
        "PR166_SF_R2_ChampionRegistry.report.json",
        "PR166_SF_R2_ReportManifest.report.json",
        "PR166_SF_R2_FinalSummary.report.json",
        "PR166_SF_R2_RuntimeSafetyHandoff.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(name for name in REPORT_FILENAMES if name not in SUMMARY_REPORTS)

REQUIRED_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_SM2_FinalSummary.report.json",
    "PR166_SM2_ReportManifest.report.json",
    "PR166_SM2_PR166SFR2Handoff.report.json",
    "PR166_SM2_AllNegConvPlan.report.json",
    "PR166_SM2_RepairPriority.report.json",
    "PR166_SM2_RetestBoostQueue.report.json",
    "PR166_SM2_BreakEvenGap.report.json",
    "PR166_SM2_CostCutLedger.report.json",
    "PR166_SM2_FillBoostLedger.report.json",
    "PR166_SM2_CalibBoostLedger.report.json",
    "PR166_SM2_ParamUpliftLedger.report.json",
    "PR166_SM2_EdgeUpliftLedger.report.json",
    "PR166_SM2_ConversionMath.report.json",
    "PR166_SM2_ConversionAgentQueue.report.json",
    "PR166_SM2_ConvertibleQueue.report.json",
    "PR166_SM2_QuantumPriority.report.json",
    "PR166_SM2_QuantumStructure.report.json",
    "PR166_SM2_PosSeedLedger.report.json",
    "PR166_SM2_PosDriverLedger.report.json",
    "PR166_SM2_PosExpansion.report.json",
    "PR166_SM2_ScoreRegistry.report.json",
    "PR166_SM2_MemoryLedger.report.json",
    "PR166_SM2_TCALedger.report.json",
    "PR166_SM2_CostRootLedger.report.json",
    "PR166_SM2_CalibrationLedger.report.json",
    "PR166_SM2_Microstructure.report.json",
    "PR166_SM2_CapacityCrowding.report.json",
    "PR166_SM2_OverfitFDRLedger.report.json",
    "PR166_SM2_RankStabilityLedger.report.json",
    "PR166_SM2_AgentDutyLedger.report.json",
    "PR166_SM2_AgentTaskQueue.report.json",
    "PR166_SM2_AgentKPIAudit.report.json",
    "PR166_SM2_CmdActionMatrix.report.json",
    "PR166_SM2_RouteTriageMatrix.report.json",
    "PR166_SM2_PlanCrosswalk.report.json",
    "PR166_SM2_ConnectorRouting.report.json",
    "PR166_SM2_AuthorityAudit.report.json",
    "PR166_SM2_NoProfitAudit.report.json",
    "PR166_SM2_OrphanAudit.report.json",
    "PR166_S2_FinalSummary.report.json",
    "PR166_S2_ReportManifest.report.json",
    "PR166_S2_NetEdgeResultLedger.report.json",
    "PR166_S2_TCAResultLedger.report.json",
    "PR166_S2_CostAttribLedger.report.json",
    "PR166_S2_ImplShortfallLedger.report.json",
    "PR166_S2_FillLedger.report.json",
    "PR166_S2_NoFillLedger.report.json",
    "PR166_S2_CalibrationLedger.report.json",
    "PR166_S2_MicrostructureLedger.report.json",
    "PR166_S2_LatLiqImpactLedger.report.json",
    "PR166_S2_AdverseSelectionLedger.report.json",
    "PR166_S2_SettlementLedger.report.json",
    "PR166_S2_EdgeLCBRegistry.report.json",
    "PR166_S2_ConfidenceRegistry.report.json",
    "PR166_S2_RankAggregationLedger.report.json",
    "PR166_S2_EdgeAttributionLedger.report.json",
    "PR166_S2_EdgeDecayLedger.report.json",
    "PR166_S2_AltExecPathLedger.report.json",
    "PR166_S2_QuantumHandoff.report.json",
    "PR166_S2_PR166SFFeedback.report.json",
    "PR166_S2_PR167SimHandoff.report.json",
    "PR166_S2_AgentDutyLedger.report.json",
    "PR166_S2_AgentKPIAudit.report.json",
    "PR166_S2_AgentTaskQueue.report.json",
    "PR166_S2_CommandActionMatrix.report.json",
    "PR166_S2_RouteTriageMatrix.report.json",
    "PR166_S2_ConnectorRefRouting.report.json",
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
    "PR165_D2_RouteTriageMatrix.report.json",
    "PR165_D2_RepairAwareSelectionQueue.report.json",
    "PR165_D2_QuantumCandidatePriorityV2.report.json",
    "PR166_S_FinalSummary.report.json",
    "PR166_S_ReportManifest.report.json",
    "PR166_S_ResultAttributionLedger.report.json",
    "PR166_S_ResultConfidenceRegistry.report.json",
    "PR166_S_ExecutionCostLedger.report.json",
    "PR166_SM_FinalSummary.report.json",
    "PR166_SM_ReportManifest.report.json",
    "PR166_SM_RefreshedScoreRegistry.report.json",
    "PR166_SM_RefreshedMemoryLedger.report.json",
)

OPTIONAL_INPUT_PATTERNS: tuple[str, ...] = (
    "PR164_*.report.json",
    "PR165_*.report.json",
    "PR165_B_*.report.json",
    "PR165_C_*.report.json",
    "PR165_D_*.report.json",
)

EXPECTED_COUNTS = {
    "PR166_SM2_PR166SFR2Handoff.report.json": 3213,
    "PR166_SM2_AllNegConvPlan.report.json": 3213,
    "PR166_SM2_BreakEvenGap.report.json": 3213,
    "PR166_SM2_CostCutLedger.report.json": 3213,
    "PR166_SM2_FillBoostLedger.report.json": 3213,
    "PR166_SM2_CalibBoostLedger.report.json": 3213,
    "PR166_SM2_ParamUpliftLedger.report.json": 3213,
    "PR166_SM2_QuantumPriority.report.json": 559,
    "PR166_SM2_PosExpansion.report.json": 32,
    "PR166_S2_NetEdgeResultLedger.report.json": 3215,
    "PR166_S2_FillLedger.report.json": 3032,
    "PR166_S2_NoFillLedger.report.json": 183,
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
        "mapped_component": "fill_model_price_quantity_spread_slippage_controls",
    },
    {
        "source_family": "KALSHI_BINARY_ORDERBOOK",
        "source_url": "https://docs.kalshi.com/getting_started/orderbook_responses",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "yes_no_bid_symmetry_binary_orderbook_semantics",
    },
    {
        "source_family": "QISKIT_OPTIMIZATION_QUBO_CONVERTER",
        "source_url": "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "quadratic_program_to_qubo_structure_without_backend_execution",
    },
    {
        "source_family": "D_WAVE_OCEAN_MODEL_FAMILIES",
        "source_url": "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "bqm_cqm_dqm_qubo_ising_model_family_routing",
    },
    {
        "source_family": "SCIKIT_LEARN_PROBABILITY_CALIBRATION",
        "source_url": "https://scikit-learn.org/stable/modules/calibration.html",
        "source_authority": "TECHNICAL_REFERENCE_CANDIDATE_PROVISIONAL",
        "mapped_component": "calibration_brier_log_loss_repair_reference",
    },
    {
        "source_family": "BAILEY_LOPEZ_DE_PRADO_DEFLATED_SHARPE",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551",
        "source_authority": "RESEARCH_CANDIDATE_PROVISIONAL",
        "mapped_component": "multiple_testing_false_discovery_overfit_control",
    },
    {
        "source_family": "APACHE_AIRFLOW_DAG_DEPENDENCIES",
        "source_url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html",
        "source_authority": "OFFICIAL_CANDIDATE_PROVISIONAL",
        "mapped_component": "upstream_downstream_dag_orchestration_receipts",
    },
)


def _schema_name(report_filename: str) -> str:
    stem = report_filename.removesuffix(".report.json")
    stem = stem.replace("PR166_SF_R2_", "pr166_sf_r2_")
    stem = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", stem)
    stem = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", stem)
    stem = stem.replace("__", "_").lower()
    return f"{stem}.schema.json"


REPORT_SCHEMA_REFS = {name: _schema_name(name) for name in REPORT_FILENAMES}
SCHEMA_FILENAMES: tuple[str, ...] = (
    "pr166_sf_r2_common.schema.json",
    *(REPORT_SCHEMA_REFS[name] for name in REPORT_FILENAMES),
)
