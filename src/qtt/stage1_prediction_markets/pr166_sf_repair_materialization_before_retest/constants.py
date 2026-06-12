"""Constants for PR166-SF report generation and validation."""

from __future__ import annotations

import re
from pathlib import Path

PR_ID = "PR166-SF"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-sf-repair-materialization-before-retest"
CREATED_AT_UTC = "2026-06-12T00:00:00Z"
AUTHORITY_CLASS = "PR166_SF_REPAIR_MATERIALIZATION_REPLAY_PAPER_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_SF_AUTHORITY_BOUNDARY::REPAIR_MATERIALIZATION_REPLAY_PAPER_ONLY_"
    "NO_LIVE_SOURCE_TRUTH_CONNECTOR_BINDING_OR_QUANTUM_BACKEND"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_sf_repair_materialization_before_retest.py"
BUILDER_REF = "tools/build_pr166_sf_repair_materialization_before_retest.py"
MANIFEST_REF = "PR166_SF_ReportManifest.report.json"
REPAIR_POLICY_REF = "PR166_SF_REPAIR_POLICY::EXECUTION_ADJUSTED_MATERIALIZATION_V1"
REPAIR_THRESHOLD_POLICY_REF = "PR166_SF_REPAIR_THRESHOLD_POLICY::UPSTREAM_DISTRIBUTION_DERIVED_V1"
AUTHORITY_AUDIT_REF = "PR166_SF_AuthorityBoundaryAudit.report.json"
NO_PROFIT_AUDIT_REF = "PR166_SF_NoProfitEvidenceAudit.report.json"
NOT_APPLICABLE_ID = "NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"
DEFAULT_SHARD_ROW_TARGET = 1000

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr166_sf_shards"
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "pr166_sf_repair_materialization_before_retest"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/"
    "pr166_sf_repair_materialization_before_retest"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr166_sf_repair_materialization_before_retest"
)

UPSTREAM_PR_REFS = (
    "PR165",
    "PR165-B",
    "PR165-C",
    "PR165-D",
    "PR165-D2",
    "PR166-S",
    "PR166-SM",
    "PR164",
)
DOWNSTREAM_PR_REFS = (
    "PR166-S2",
    "PR166-S_RETEST_LOOP_V2",
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
FUTURE_CONNECTOR_PR_REFS = (
    "PR174",
    "PR175",
    "PR176",
    "PR177",
    "PR178",
    "PR179",
    "PR180",
    "PR181",
)

REPAIR_PREVIEW_WEIGHTS = {
    "repair_delta_net_edge_normalized": 0.20,
    "post_repair_preview_edge_lcb": 0.12,
    "repair_confidence_score": 0.10,
    "repair_evidence_depth_score": 0.09,
    "field_materialization_completeness_score": 0.08,
    "formula_algorithm_repair_score": 0.07,
    "tca_term_repair_score": 0.07,
    "microstructure_repair_score": 0.06,
    "probability_edge_repair_score": 0.05,
    "quantum_mapping_readiness_after_repair": 0.05,
    "marginal_utility_score": 0.04,
    "capacity_score_after_repair": 0.04,
    "scenario_transferability_after_repair": 0.03,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.05,
    "repair_uncertainty_penalty": -0.04,
    "rank_instability_adjustment": -0.04,
    "crowding_penalty_after_repair": -0.03,
    "correlation_cluster_penalty_after_repair": -0.03,
}
RETEST_READINESS_WEIGHTS = {
    "post_repair_preview_edge_lcb": 0.18,
    "repair_confidence_score": 0.12,
    "repair_evidence_depth_score": 0.10,
    "qku_tradability_readiness_score": 0.09,
    "point_in_time_no_leakage_score": 0.08,
    "materialization_actuality_score": 0.08,
    "repair_verification_pass_score": 0.07,
    "fill_probability_score": 0.07,
    "capacity_score_after_repair": 0.06,
    "marginal_utility_score": 0.05,
    "quantum_mapping_readiness_after_repair": 0.05,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.04,
    "repair_uncertainty_penalty": -0.04,
    "correlation_cluster_penalty_after_repair": -0.03,
    "source_disagreement_penalty": -0.03,
}

REQUIRED_INPUT_REPORTS: tuple[str, ...] = (
    "PR165_D2_FinalSummary.report.json",
    "PR165_D2_ReportManifest.report.json",
    "PR165_D2_InputConsumptionAudit.report.json",
    "PR165_D2_RepairAwareSelectionQueue.report.json",
    "PR165_D2_RouteTriageMatrix.report.json",
    "PR165_D2_ReplayPaperRetestBatchV2.report.json",
    "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json",
    "PR165_D2_TCADecompositionSelectionLedger.report.json",
    "PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json",
    "PR165_D2_MicrostructureFeatureLedger.report.json",
    "PR165_D2_ScoreComponentProvenanceLedger.report.json",
    "PR165_D2_SelectionExclusionReasonLedger.report.json",
    "PR165_D2_QuantumCandidatePriorityV2.report.json",
    "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
    "PR165_D2_AgentTaskQueue.report.json",
    "PR165_D2_CommandActionMatrix.report.json",
    "PR165_D2_MasterPlanSectionCrosswalk.report.json",
    "PR165_D2_MarketSpecificSelectionIndex.report.json",
    "PR165_D2_ExternalSelectionSignalCandidateRegistry.report.json",
    "PR165_D2_ExternalInstitutionalSignalCoverageAudit.report.json",
    "PR166_SM_FinalSummary.report.json",
    "PR166_SM_ReportManifest.report.json",
    "PR166_SM_RefreshedScoreRegistry.report.json",
    "PR166_SM_RefreshedMemoryLedger.report.json",
    "PR166_SM_NetEdgeRankDeltaRegistry.report.json",
    "PR166_SM_RepairPriorityRegistry.report.json",
    "PR166_SM_FieldMaterializationCandidateRegistry.report.json",
    "PR166_SM_FailureRepairRouteHandoffToPR166SF.report.json",
    "PR166_SM_SelectionReadinessForPR165D2.report.json",
    "PR166_SM_QuantumPriorityAfterReplayPaperRegistry.report.json",
    "PR166_SM_QuantumMappingCandidateReadiness.report.json",
    "PR166_SM_AgentTaskQueue.report.json",
    "PR166_SM_AgentScoreMemoryRefreshContract.report.json",
    "PR166_SM_AuthorityBoundaryAudit.report.json",
    "PR166_SM_OrphanArtifactAudit.report.json",
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
    "PR166_S_PointInTimeExecutionAudit.report.json",
    "PR166_S_NoLookaheadAudit.report.json",
    "PR166_S_QuantumAdvisoryPassthrough.report.json",
    "PR165_FinalSummary.report.json",
    "PR165_ReportManifest.report.json",
    "PR165_B_ConditionFingerprintRegistry.report.json",
    "PR165_B_CombinationFingerprintRegistry.report.json",
    "PR165_B_ScenarioOutcomeMatrix.report.json",
    "PR165_C_ComputableArtifactPayloadRegistry.report.json",
    "PR165_C_ComputableQKUFormulaActionRegistry.report.json",
    "PR165_C_FormulaTestVectorRegistry.report.json",
    "PR165_C_ConditionRegimeFeatureMatrix.report.json",
    "PR165_D_FinalSummary.report.json",
    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
    "PR165_D_SelectionScoreRegistry.report.json",
    "PR165_D_QuantumSelectionRouter.report.json",
)
OPTIONAL_INPUT_GLOBS = ("PR164_*.report.json", "AGENTS.md")

EXPECTED_ROW_COUNTS = {
    "PR165_D2_FinalSummary.report.json": 1,
    "PR165_D2_RepairAwareSelectionQueue.report.json": 3985,
    "PR165_D2_RouteTriageMatrix.report.json": 4485,
    "PR165_D2_ReplayPaperRetestBatchV2.report.json": 298,
    "PR165_D2_NetEdgeAdjustedCandidateRanking.report.json": 3985,
    "PR165_D2_TCADecompositionSelectionLedger.report.json": 3985,
    "PR165_D2_PredictionMarketProbabilityEdgeLedger.report.json": 3985,
    "PR165_D2_MicrostructureFeatureLedger.report.json": 3985,
    "PR165_D2_ScoreComponentProvenanceLedger.report.json": 91655,
    "PR165_D2_SelectionExclusionReasonLedger.report.json": 3687,
    "PR165_D2_QuantumCandidatePriorityV2.report.json": 6502,
    "PR165_D2_QKUFormulaAlgorithmComputabilityRouting.report.json": 6502,
    "PR165_D2_AgentRosterDiscoveryAudit.report.json": 8,
    "PR165_D2_AgentDutySourceCrosswalk.report.json": 8,
    "PR166_SM_RepairPriorityRegistry.report.json": 3985,
    "PR166_SM_FieldMaterializationCandidateRegistry.report.json": 6502,
    "PR166_S_ExecutionCostLedger.report.json": 3985,
    "PR166_S_ResultConfidenceRegistry.report.json": 3985,
}

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_SF_InputConsumptionAudit.report.json",
    "PR166_SF_OptionalInputLedger.report.json",
    "PR166_SF_RowCountLedger.report.json",
    "PR166_SF_RepairPolicy.report.json",
    "PR166_SF_TargetUniverseRegistry.report.json",
    "PR166_SF_NegativeEdgeRootCauseLedger.report.json",
    "PR166_SF_TCATermLedger.report.json",
    "PR166_SF_CostDragRepairLedger.report.json",
    "PR166_SF_ProbabilityEdgeRepairLedger.report.json",
    "PR166_SF_MicrostructureRepairLedger.report.json",
    "PR166_SF_ExecCostRepairLedger.report.json",
    "PR166_SF_SettlementAdverseRepairLedger.report.json",
    "PR166_SF_FieldMaterializationRegistry.report.json",
    "PR166_SF_MissingValueFillLedger.report.json",
    "PR166_SF_FormulaQKURepairRegistry.report.json",
    "PR166_SF_RepairedPayloadRegistry.report.json",
    "PR166_SF_RepairedCandidateRetestQueue.report.json",
    "PR166_SF_RepairPreviewScoreRegistry.report.json",
    "PR166_SF_TestVectorRegistry.report.json",
    "PR166_SF_SmokeTestLedger.report.json",
    "PR166_SF_RepairOverfitControl.report.json",
    "PR166_SF_RepairCapacityControl.report.json",
    "PR166_SF_RepairChampionChallengerLedger.report.json",
    "PR166_SF_RepairMarginalUtilityQueue.report.json",
    "PR166_SF_QuantumRepairRouter.report.json",
    "PR166_SF_QuantumStructureLedger.report.json",
    "PR166_SF_ExternalRepairSignalRegistry.report.json",
    "PR166_SF_ExternalValueFillLedger.report.json",
    "PR166_SF_AgentRosterAudit.report.json",
    "PR166_SF_AgentRepairTaskQueue.report.json",
    "PR166_SF_DashboardRepairHandoff.report.json",
    "PR166_SF_GovernanceRepairHandoff.report.json",
    "PR166_SF_CommanderRepairHandoff.report.json",
    "PR166_SF_RouteTriageMatrix.report.json",
    "PR166_SF_MasterPlanSectionCrosswalk.report.json",
    "PR166_SF_MarketSpecificRepairIndex.report.json",
    "PR166_SF_CommandActionMatrix.report.json",
    "PR166_SF_PRFileConnectivityAudit.report.json",
    "PR166_SF_RowValueConnectivityAudit.report.json",
    "PR166_SF_AuthorityBoundaryAudit.report.json",
    "PR166_SF_NoProfitEvidenceAudit.report.json",
    "PR166_SF_OrphanArtifactAudit.report.json",
    "PR166_SF_StatusEnumDriftAudit.report.json",
    "PR166_SF_ReportManifest.report.json",
    "PR166_SF_FinalSummary.report.json",
    "PR166_SF_RepairThresholdPolicy.report.json",
    "PR166_SF_SourceDedupeLedger.report.json",
    "PR166_SF_QKUTradabilityLedger.report.json",
    "PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json",
    "PR166_SF_RepairSensitivityLedger.report.json",
    "PR166_SF_ParameterRobustnessLedger.report.json",
    "PR166_SF_NoLeakageRepairAudit.report.json",
    "PR166_SF_RepairDAGLedger.report.json",
    "PR166_SF_RetestReadinessRegistry.report.json",
    "PR166_SF_MaterializationAudit.report.json",
    "PR166_SF_AgentDutyLedger.report.json",
    "PR166_SF_ExternalSearchReceipt.report.json",
    "PR166_SF_ConnectorRefRouting.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR166_SF_InputConsumptionAudit.report.json",
        "PR166_SF_OptionalInputLedger.report.json",
        "PR166_SF_RowCountLedger.report.json",
        "PR166_SF_RepairPolicy.report.json",
        "PR166_SF_RepairThresholdPolicy.report.json",
        "PR166_SF_ExternalRepairSignalRegistry.report.json",
        "PR166_SF_ExternalValueFillLedger.report.json",
        "PR166_SF_AgentRosterAudit.report.json",
        "PR166_SF_AgentRepairTaskQueue.report.json",
        "PR166_SF_DashboardRepairHandoff.report.json",
        "PR166_SF_GovernanceRepairHandoff.report.json",
        "PR166_SF_CommanderRepairHandoff.report.json",
        "PR166_SF_RouteTriageMatrix.report.json",
        "PR166_SF_MasterPlanSectionCrosswalk.report.json",
        "PR166_SF_MarketSpecificRepairIndex.report.json",
        "PR166_SF_CommandActionMatrix.report.json",
        "PR166_SF_PRFileConnectivityAudit.report.json",
        "PR166_SF_RowValueConnectivityAudit.report.json",
        "PR166_SF_AuthorityBoundaryAudit.report.json",
        "PR166_SF_NoProfitEvidenceAudit.report.json",
        "PR166_SF_OrphanArtifactAudit.report.json",
        "PR166_SF_StatusEnumDriftAudit.report.json",
        "PR166_SF_ReportManifest.report.json",
        "PR166_SF_FinalSummary.report.json",
        "PR166_SF_SourceDedupeLedger.report.json",
        "PR166_SF_ExternalSearchReceipt.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(
    filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS
)


def _schema_name(filename: str) -> str:
    stem = filename.replace(".report.json", "")
    return re.sub(r"(?<!^)(?=[A-Z])", "_", stem).lower().replace("__", "_") + ".schema.json"


REPORT_SCHEMA_REFS = {filename: _schema_name(filename) for filename in REPORT_FILENAMES}
SCHEMA_FILENAMES: tuple[str, ...] = (
    "pr166_sf_common.schema.json",
    *tuple(REPORT_SCHEMA_REFS[filename] for filename in REPORT_FILENAMES),
)

SOURCE_FILENAMES: tuple[str, ...] = (
    "__init__.py",
    "authority.py",
    "constants.py",
    "enums.py",
    "io.py",
    "models.py",
    "input_consumption.py",
    "row_count_reconciliation.py",
    "optional_input_resolution.py",
    "repair_policy.py",
    "repair_threshold_policy.py",
    "target_universe.py",
    "negative_net_edge_root_cause.py",
    "tca_repair.py",
    "probability_edge_repair.py",
    "microstructure_repair.py",
    "cost_drag_repair.py",
    "field_materialization.py",
    "candidate_source_dedupe.py",
    "missing_value_candidate_fill.py",
    "formula_algorithm_qku_repair.py",
    "materialized_formula_algorithm_library.py",
    "qku_tradability_readiness.py",
    "repaired_payload.py",
    "repair_impact_preview.py",
    "repair_counterfactual_sensitivity.py",
    "repair_verification.py",
    "false_discovery_overfit.py",
    "capacity_crowding.py",
    "portfolio_diversification.py",
    "champion_challenger.py",
    "marginal_utility.py",
    "quantum_repair_readiness.py",
    "quantum_coefficient_materialization.py",
    "external_repair_intake.py",
    "agent_routing.py",
    "route_triage.py",
    "crosswalk.py",
    "market_index.py",
    "dag_orchestration.py",
    "command_action_matrix.py",
    "connectivity.py",
    "connector_ref_routing.py",
    "report_writer.py",
    "validator.py",
)

EXTERNAL_REFERENCE_ROWS = (
    {
        "source_family": "QUANTCONNECT_LEAN_REALITY_MODELING",
        "source_url": "https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/buying-power",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "capacity_and_buying_power_repair",
    },
    {
        "source_family": "QUANTCONNECT_LEAN_TRANSACTION_MODELS",
        "source_url": "https://www.quantconnect.com/docs/v1/algorithm-reference/reality-modelling",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "fee_fill_slippage_reality_modeling",
    },
    {
        "source_family": "KALSHI_ORDERBOOK",
        "source_url": "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "binary_yes_no_orderbook_symmetry",
    },
    {
        "source_family": "QISKIT_OPTIMIZATION",
        "source_url": "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "quadratic_program_qubo_ising_mapping",
    },
    {
        "source_family": "D_WAVE_OCEAN_DIMOD",
        "source_url": "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "bqm_cqm_dqm_qubo_ising_model_family",
    },
    {
        "source_family": "APACHE_AIRFLOW_DAG",
        "source_url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "dag_upstream_downstream_orchestration",
    },
    {
        "source_family": "SKLEARN_PROBABILITY_CALIBRATION",
        "source_url": "https://scikit-learn.org/stable/modules/calibration.html",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "probability_calibration_repair",
    },
    {
        "source_family": "SKLEARN_BRIER_SCORE",
        "source_url": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html",
        "official_or_non_official": "OFFICIAL",
        "mapped_component": "brier_loss_proxy",
    },
    {
        "source_family": "DEFLATED_SHARPE_FALSE_DISCOVERY",
        "source_url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf",
        "official_or_non_official": "PRIMARY_RESEARCH",
        "mapped_component": "false_discovery_overfit_control",
    },
    {
        "source_family": "ALMGREN_CHRISS_OPTIMAL_EXECUTION",
        "source_url": "https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf",
        "official_or_non_official": "PRIMARY_RESEARCH",
        "mapped_component": "market_impact_cost_frontier",
    },
)

if set(REPORT_SCHEMA_REFS) != set(REPORT_FILENAMES):  # pragma: no cover
    raise RuntimeError("PR166-SF report/schema mapping drift")
