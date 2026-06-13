"""Constants for PR166-S2 replay/paper retest loop v2."""

from __future__ import annotations

import re
from pathlib import Path

PR_ID = "PR166-S2"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-s2-replay-paper-retest-loop-v2"
CREATED_AT_UTC = "2026-06-12T12:00:00Z"
AUTHORITY_CLASS = "PR166_S2_REPLAY_PAPER_RETEST_LOOP_V2_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_S2_AUTHORITY_BOUNDARY::REPLAY_PAPER_RETEST_LOOP_V2_"
    "NO_LIVE_SOURCE_TRUTH_CONNECTOR_BINDING_PROFIT_OR_QUANTUM_BACKEND"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_s2_replay_paper_retest_loop_v2.py"
BUILDER_REF = "tools/build_pr166_s2_replay_paper_retest_loop_v2.py"
MANIFEST_REF = "PR166_S2_ReportManifest.report.json"
AUTHORITY_AUDIT_REF = "PR166_S2_AuthorityBoundaryAudit.report.json"
NO_PROFIT_AUDIT_REF = "PR166_S2_NoProfitEvidenceAudit.report.json"
NOT_APPLICABLE_ID = "NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"
DEFAULT_SHARD_ROW_TARGET = 1000

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr166_s2_shards"
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets.pr166_s2_replay_paper_retest_loop_v2"
)

UPSTREAM_PR_REFS = (
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
DOWNSTREAM_PR_REFS = (
    "PR166-SM2",
    "PR166-SM_REFRESH_V2",
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

RETEST_SCORE_WEIGHTS = {
    "normalized_replay_paper_net_edge_after_costs": 0.24,
    "edge_lower_confidence_bound": 0.13,
    "result_confidence_score": 0.10,
    "fill_realism_score": 0.09,
    "probability_calibration_score": 0.08,
    "point_in_time_no_leakage_score": 0.07,
    "capacity_score": 0.06,
    "scenario_transferability_score": 0.05,
    "marginal_utility_score": 0.05,
    "quantum_comparator_readiness_score": 0.04,
    "champion_challenger_stability_score": 0.04,
    "false_discovery_risk_adjustment": -0.05,
    "overfit_risk_adjustment": -0.05,
    "cost_drag_ratio": -0.04,
    "latency_drag_ratio": -0.04,
    "liquidity_drag_ratio": -0.03,
    "adverse_selection_ratio": -0.03,
    "crowding_penalty": -0.03,
    "correlation_cluster_penalty": -0.03,
    "settlement_sensitivity_score": -0.02,
    "rank_instability_adjustment": -0.02,
}

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_S2_InputAudit.report.json",
    "PR166_S2_OptionalInputLedger.report.json",
    "PR166_S2_RowCountLedger.report.json",
    "PR166_S2_RetestPolicy.report.json",
    "PR166_S2_InputRegistry.report.json",
    "PR166_S2_RetestUniverse.report.json",
    "PR166_S2_EpisodePlan.report.json",
    "PR166_S2_ScenarioSchedule.report.json",
    "PR166_S2_EventStreamLedger.report.json",
    "PR166_S2_OrderIntentLedger.report.json",
    "PR166_S2_FillLedger.report.json",
    "PR166_S2_NoFillLedger.report.json",
    "PR166_S2_StateLedger.report.json",
    "PR166_S2_TCAResultLedger.report.json",
    "PR166_S2_ImplShortfallLedger.report.json",
    "PR166_S2_CostAttribLedger.report.json",
    "PR166_S2_NetEdgeResultLedger.report.json",
    "PR166_S2_EdgeLCBRegistry.report.json",
    "PR166_S2_ConfidenceRegistry.report.json",
    "PR166_S2_AttributionLedger.report.json",
    "PR166_S2_CalibrationLedger.report.json",
    "PR166_S2_MicrostructureLedger.report.json",
    "PR166_S2_LatLiqImpactLedger.report.json",
    "PR166_S2_SettlementLedger.report.json",
    "PR166_S2_AdverseSelectionLedger.report.json",
    "PR166_S2_WinnerRegistry.report.json",
    "PR166_S2_LoserRegistry.report.json",
    "PR166_S2_CondMemoryLedger.report.json",
    "PR166_S2_NegMemoryLedger.report.json",
    "PR166_S2_PosPrefLedger.report.json",
    "PR166_S2_ChampChallengerLedger.report.json",
    "PR166_S2_MarginalUtilityLedger.report.json",
    "PR166_S2_DiversificationLedger.report.json",
    "PR166_S2_CapacityCrowdingLedger.report.json",
    "PR166_S2_OverfitFDRLedger.report.json",
    "PR166_S2_RankStabilityLedger.report.json",
    "PR166_S2_StressLedger.report.json",
    "PR166_S2_NoLeakageAudit.report.json",
    "PR166_S2_PayloadExecAudit.report.json",
    "PR166_S2_FormulaQKUResultLedger.report.json",
    "PR166_S2_QuantumHandoff.report.json",
    "PR166_S2_PR166SM2Handoff.report.json",
    "PR166_S2_PR166SFFeedback.report.json",
    "PR166_S2_PR165D2Feedback.report.json",
    "PR166_S2_R3GapHandoff.report.json",
    "PR166_S2_PR167SimHandoff.report.json",
    "PR166_S2_AgentTaskQueue.report.json",
    "PR166_S2_AgentOutcomeHandoff.report.json",
    "PR166_S2_DashboardHandoff.report.json",
    "PR166_S2_GovernanceHandoff.report.json",
    "PR166_S2_CommanderHandoff.report.json",
    "PR166_S2_MarketResultIndex.report.json",
    "PR166_S2_RouteTriageMatrix.report.json",
    "PR166_S2_MasterPlanCrosswalk.report.json",
    "PR166_S2_CommandActionMatrix.report.json",
    "PR166_S2_ConnectorRefRouting.report.json",
    "PR166_S2_ExternalSignalRegistry.report.json",
    "PR166_S2_SearchReceipt.report.json",
    "PR166_S2_PRFileConnectivityAudit.report.json",
    "PR166_S2_RowValueConnectivityAudit.report.json",
    "PR166_S2_AuthorityBoundaryAudit.report.json",
    "PR166_S2_NoProfitEvidenceAudit.report.json",
    "PR166_S2_OrphanArtifactAudit.report.json",
    "PR166_S2_StatusEnumDriftAudit.report.json",
    "PR166_S2_ReportManifest.report.json",
    "PR166_S2_FinalSummary.report.json",
    "PR166_S2_ShardInputAudit.report.json",
    "PR166_S2_ExecReadinessAudit.report.json",
    "PR166_S2_FillModelPolicy.report.json",
    "PR166_S2_BookSnapshotLedger.report.json",
    "PR166_S2_ExecBudgetLedger.report.json",
    "PR166_S2_EpisodeDAGLedger.report.json",
    "PR166_S2_ResultDistLedger.report.json",
    "PR166_S2_ThresholdPolicy.report.json",
    "PR166_S2_AgentDutyLedger.report.json",
    "PR166_S2_SearchAudit.report.json",
    "PR166_S2_LifecycleLedger.report.json",
    "PR166_S2_PayloadRuntimeAudit.report.json",
    "PR166_S2_NoFillReasonLedger.report.json",
    "PR166_S2_EdgeAttributionLedger.report.json",
    "PR166_S2_EdgeDecayLedger.report.json",
    "PR166_S2_RankAggregationLedger.report.json",
    "PR166_S2_AltExecPathLedger.report.json",
    "PR166_S2_TTRiskLedger.report.json",
    "PR166_S2_AgentKPIAudit.report.json",
)

REQUIRED_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_SF_FinalSummary.report.json",
    "PR166_SF_ReportManifest.report.json",
    "PR166_SF_InputConsumptionAudit.report.json",
    "PR166_SF_RepairedCandidateRetestQueue.report.json",
    "PR166_SF_RetestReadinessRegistry.report.json",
    "PR166_SF_RepairedPayloadRegistry.report.json",
    "PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json",
    "PR166_SF_FormulaQKURepairRegistry.report.json",
    "PR166_SF_QKUTradabilityLedger.report.json",
    "PR166_SF_TestVectorRegistry.report.json",
    "PR166_SF_SmokeTestLedger.report.json",
    "PR166_SF_RepairPreviewScoreRegistry.report.json",
    "PR166_SF_TCATermLedger.report.json",
    "PR166_SF_ExecCostRepairLedger.report.json",
    "PR166_SF_CostDragRepairLedger.report.json",
    "PR166_SF_ProbabilityEdgeRepairLedger.report.json",
    "PR166_SF_MicrostructureRepairLedger.report.json",
    "PR166_SF_NoLeakageRepairAudit.report.json",
    "PR166_SF_RepairOverfitControl.report.json",
    "PR166_SF_RepairCapacityControl.report.json",
    "PR166_SF_RepairChampionChallengerLedger.report.json",
    "PR166_SF_RepairMarginalUtilityQueue.report.json",
    "PR166_SF_QuantumRepairRouter.report.json",
    "PR166_SF_QuantumStructureLedger.report.json",
    "PR166_SF_AgentRosterAudit.report.json",
    "PR166_SF_AgentDutyLedger.report.json",
    "PR166_SF_AgentRepairTaskQueue.report.json",
    "PR166_SF_CommandActionMatrix.report.json",
    "PR166_SF_RouteTriageMatrix.report.json",
    "PR166_SF_MarketSpecificRepairIndex.report.json",
    "PR166_SF_MasterPlanSectionCrosswalk.report.json",
    "PR166_SF_ConnectorRefRouting.report.json",
    "PR166_SF_ExternalValueFillLedger.report.json",
    "PR166_SF_ExternalRepairSignalRegistry.report.json",
    "PR166_SF_ExternalSearchReceipt.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
    "PR165_D2_AgentTaskQueue.report.json",
    "PR165_D2_CommandActionMatrix.report.json",
    "PR165_D2_FinalSummary.report.json",
    "PR165_D2_ReportManifest.report.json",
    "PR165_D2_ReplayPaperRetestBatchV2.report.json",
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
    "PR166_S_PointInTimeExecutionAudit.report.json",
    "PR166_S_NoLookaheadAudit.report.json",
    "PR166_S_QuantumAdvisoryPassthrough.report.json",
    "PR166_SM_FinalSummary.report.json",
    "PR166_SM_ReportManifest.report.json",
    "PR166_SM_RefreshedScoreRegistry.report.json",
    "PR166_SM_RefreshedMemoryLedger.report.json",
    "PR166_SM_NetEdgeRankDeltaRegistry.report.json",
    "PR166_SM_ConditionScopedWinnerRegistry.report.json",
    "PR166_SM_ConditionScopedLoserRegistry.report.json",
)

EXPECTED_ROW_COUNTS = {
    "PR166_SF_FinalSummary.report.json": 1,
    "PR166_SF_RepairedCandidateRetestQueue.report.json": 6502,
    "PR166_SF_RepairedPayloadRegistry.report.json": 6502,
    "PR166_SF_QKUTradabilityLedger.report.json": 6502,
    "PR166_SF_AgentDutyLedger.report.json": 6502,
    "PR165_D2_AgentRosterDiscoveryAudit.report.json": 8,
    "PR165_D2_AgentDutySourceCrosswalk.report.json": 8,
}

EXTERNAL_REFERENCE_ROWS = (
    {
        "source_family": "QUANTCONNECT_LEAN_REALITY_MODELING",
        "source_url": "https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "fills_slippage_fees_settlement_capacity_reality_modeling",
    },
    {
        "source_family": "KALSHI_BINARY_ORDERBOOK",
        "source_url": "https://docs.kalshi.com/getting_started/orderbook_responses",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "yes_no_bid_symmetry_and_price_complements",
    },
    {
        "source_family": "KALSHI_MARKET_ORDERBOOK_API",
        "source_url": "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "top_of_book_and_depth_proxy",
    },
    {
        "source_family": "QISKIT_OPTIMIZATION_QUADRATIC_PROGRAM",
        "source_url": "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "quadratic_program_qubo_ising_comparator_structure",
    },
    {
        "source_family": "D_WAVE_OCEAN_DIMOD_MODELS",
        "source_url": "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "bqm_cqm_dqm_qubo_ising_model_family",
    },
    {
        "source_family": "APACHE_AIRFLOW_DAG",
        "source_url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "upstream_downstream_episode_dag_orchestration",
    },
    {
        "source_family": "SCIKIT_LEARN_PROBABILITY_CALIBRATION",
        "source_url": "https://scikit-learn.org/stable/modules/calibration.html",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "probability_calibration_bucket_and_drift",
    },
    {
        "source_family": "SCIKIT_LEARN_BRIER_SCORE",
        "source_url": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html",
        "official_or_non_official": "OFFICIAL",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "brier_score_proxy",
    },
    {
        "source_family": "DEFLATED_SHARPE_FALSE_DISCOVERY",
        "source_url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf",
        "official_or_non_official": "PRIMARY_RESEARCH",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "multiple_testing_and_false_discovery_penalty",
    },
    {
        "source_family": "ALMGREN_CHRISS_OPTIMAL_EXECUTION",
        "source_url": "https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf",
        "official_or_non_official": "PRIMARY_RESEARCH",
        "signal_receipt_status": "USEFUL_SIGNAL",
        "mapped_component": "market_impact_and_implementation_shortfall",
    },
)


def _schema_name(filename: str) -> str:
    stem = filename.replace(".report.json", "")
    if not stem.startswith("PR166_S2_"):
        raise ValueError(f"unexpected PR166-S2 report filename: {filename}")
    tail = stem[len("PR166_S2_") :]
    replacements = {
        "PR": "Pr",
        "SF": "Sf",
        "SM2": "Sm2",
        "QKU": "Qku",
        "TCA": "Tca",
        "LCB": "Lcb",
        "FDR": "Fdr",
        "DAG": "Dag",
        "KPI": "Kpi",
        "TTRisk": "TtRisk",
    }
    for old, new in replacements.items():
        tail = tail.replace(old, new)
    snake_tail = re.sub(r"(?<!^)(?=[A-Z])", "_", tail).lower()
    snake_tail = snake_tail.replace("q_k_u", "qku").replace("t_c_a", "tca")
    snake_tail = snake_tail.replace("d_a_g", "dag").replace("f_d_r", "fdr")
    snake_tail = snake_tail.replace("l_c_b", "lcb")
    snake_tail = snake_tail.replace("k_p_i", "kpi")
    snake_tail = snake_tail.replace("s_f", "sf")
    return f"pr166_s2_{snake_tail}.schema.json"


REPORT_SCHEMA_REFS = {filename: _schema_name(filename) for filename in REPORT_FILENAMES}
SCHEMA_FILENAMES: tuple[str, ...] = (
    "pr166_s2_common.schema.json",
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
    "candidate_universe.py",
    "episode_policy.py",
    "episode_planner.py",
    "event_stream.py",
    "nonlive_order_intent.py",
    "simulated_fill.py",
    "simulated_state.py",
    "result_attribution.py",
    "tca_results.py",
    "net_edge_results.py",
    "probability_calibration.py",
    "microstructure_outcomes.py",
    "latency_liquidity_impact.py",
    "settlement_outcomes.py",
    "adverse_selection.py",
    "capacity_crowding.py",
    "false_discovery_overfit.py",
    "rank_stability.py",
    "regime_memory.py",
    "champion_challenger.py",
    "portfolio_diversification.py",
    "marginal_utility.py",
    "stress_scenarios.py",
    "quantum_retest_readiness.py",
    "external_signal_refresh.py",
    "agent_routing.py",
    "route_triage.py",
    "crosswalk.py",
    "market_index.py",
    "command_action_matrix.py",
    "dag_orchestration.py",
    "connectivity.py",
    "shard_input_audit.py",
    "execution_readiness.py",
    "fill_model_policy.py",
    "order_book_snapshot.py",
    "execution_budget.py",
    "result_distribution.py",
    "threshold_policy.py",
    "payload_runtime_audit.py",
    "candidate_lifecycle.py",
    "agent_duty_application.py",
    "external_search_audit.py",
    "score_memory_handoff_quality.py",
    "edge_decay.py",
    "rank_aggregation.py",
    "alternative_execution.py",
    "time_to_resolution_risk.py",
    "agent_kpi_audit.py",
    "report_writer.py",
    "validator.py",
)

if set(REPORT_SCHEMA_REFS) != set(REPORT_FILENAMES):  # pragma: no cover
    raise RuntimeError("PR166-S2 report/schema mapping drift")
