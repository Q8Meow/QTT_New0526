"""Paths, report names, schema names, and branch guard for PR166-S."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess

from .central_vocab import EXPECTED_BRANCH

GENERATED_DIR = Path("docs/master_plan/generated")
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr166_s_replay_paper_scenario_retest_execution"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
SHARD_DIR = GENERATED_DIR / "pr166_s_shards"
TEST_DIR = Path("tests/stage1_prediction_markets/pr166_s_replay_paper_scenario_retest_execution")
PACKAGE_IMPORT = "src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution"

REQUIRED_INPUTS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR165_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_GlobalCandidateRanking.report.json",
    "docs/master_plan/generated/PR165_RegimeSlicedRanking.report.json",
    "docs/master_plan/generated/PR165_ExpectedValueScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_TCAAdjustedScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_LatencyLaneAssignmentRegistry.report.json",
    "docs/master_plan/generated/PR165_QuantumFormulationMaterializationRegistry.report.json",
    "docs/master_plan/generated/PR165_LineageGraph.report.json",
    "docs/master_plan/generated/pr165_shards",
    "docs/master_plan/generated/PR165_B_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_B_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_B_ConditionFingerprintRegistry.report.json",
    "docs/master_plan/generated/PR165_B_CombinationFingerprintRegistry.report.json",
    "docs/master_plan/generated/PR165_B_ScenarioOutcomeMatrix.report.json",
    "docs/master_plan/generated/PR165_B_CombinationOutcomeMemoryLedger.report.json",
    "docs/master_plan/generated/PR165_B_NegativeCombinationAvoidanceRegistry.report.json",
    "docs/master_plan/generated/PR165_B_PositiveConditionScopedPreferenceRegistry.report.json",
    "docs/master_plan/generated/PR165_B_FragileCombinationWatchlist.report.json",
    "docs/master_plan/generated/PR165_B_OutcomeAttributionLedger.report.json",
    "docs/master_plan/generated/PR165_B_CooldownPolicyRegistry.report.json",
    "docs/master_plan/generated/PR165_B_RetestEligibilityRegistry.report.json",
    "docs/master_plan/generated/PR165_B_ReplayPaperRetestQueue.report.json",
    "docs/master_plan/generated/PR165_B_RepairRouteHandoffRegistry.report.json",
    "docs/master_plan/generated/PR165_B_AgentMemoryRouter.report.json",
    "docs/master_plan/generated/PR165_B_LineageGraph.report.json",
    "docs/master_plan/generated/pr165_b_shards",
    "docs/master_plan/generated/PR165_C_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_C_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_C_MemoryConsumerRouter.report.json",
    "docs/master_plan/generated/PR165_C_PendingRetestQueue.report.json",
    "docs/master_plan/generated/PR165_C_RepairToRetestHandoff.report.json",
    "docs/master_plan/generated/PR165_C_RetestPriorityRanking.report.json",
    "docs/master_plan/generated/PR165_C_ComputableArtifactPayloadRegistry.report.json",
    "docs/master_plan/generated/PR165_C_ComputableQKUFormulaActionRegistry.report.json",
    "docs/master_plan/generated/PR165_C_FormulaTestVectorRegistry.report.json",
    "docs/master_plan/generated/PR165_C_ConditionRegimeFeatureMatrix.report.json",
    "docs/master_plan/generated/PR165_C_QuantumConsumerRouter.report.json",
    "docs/master_plan/generated/PR165_C_AgentTaskQueue.report.json",
    "docs/master_plan/generated/PR165_C_AgentTaskReceiptRequirementMatrix.report.json",
    "docs/master_plan/generated/PR165_C_DashboardConsumerHandoff.report.json",
    "docs/master_plan/generated/PR165_C_GovernanceConsumerHandoff.report.json",
    "docs/master_plan/generated/PR165_C_CommanderConsumerHandoff.report.json",
    "docs/master_plan/generated/PR165_C_LineageGraph.report.json",
    "docs/master_plan/generated/PR165_C_AuthorityBoundaryAudit.report.json",
    "docs/master_plan/generated/PR165_C_OrphanArtifactAudit.report.json",
    "docs/master_plan/generated/pr165_c_shards",
    "docs/master_plan/generated/PR165_D_ReportManifest.report.json",
    "docs/master_plan/generated/PR165_D_FinalSummary.report.json",
    "docs/master_plan/generated/PR165_D_ScenarioQKUCombinationSelectionPolicy.report.json",
    "docs/master_plan/generated/PR165_D_ScenarioGroupRegistry.report.json",
    "docs/master_plan/generated/PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
    "docs/master_plan/generated/PR165_D_RetestBatchSelectionQueue.report.json",
    "docs/master_plan/generated/PR165_D_RepairBeforeRetestSelectionQueue.report.json",
    "docs/master_plan/generated/PR165_D_SelectedExcludedReasonLedger.report.json",
    "docs/master_plan/generated/PR165_D_SelectionScoreRegistry.report.json",
    "docs/master_plan/generated/PR165_D_MarginalUtilitySelectionLedger.report.json",
    "docs/master_plan/generated/PR165_D_BatchExposureCapacityLedger.report.json",
    "docs/master_plan/generated/PR165_D_SelectionFalseDiscoveryControl.report.json",
    "docs/master_plan/generated/PR165_D_PointInTimeSelectionAudit.report.json",
    "docs/master_plan/generated/PR165_D_AgentSelectionContract.report.json",
    "docs/master_plan/generated/PR165_D_AgentSelectionHandoff.report.json",
    "docs/master_plan/generated/PR165_D_DashboardSelectionHandoff.report.json",
    "docs/master_plan/generated/PR165_D_GovernanceSelectionHandoff.report.json",
    "docs/master_plan/generated/PR165_D_CommanderSelectionHandoff.report.json",
    "docs/master_plan/generated/PR165_D_QuantumSelectionRouter.report.json",
    "docs/master_plan/generated/PR165_D_FormulaAlgorithmOptionalRouteRegistry.report.json",
    "docs/master_plan/generated/PR165_D_AuthorityBoundaryAudit.report.json",
    "docs/master_plan/generated/PR165_D_OrphanArtifactAudit.report.json",
    "docs/master_plan/generated/pr165_d_shards",
    "docs/master_plan/generated/PR208_FinalSummary.report.json",
    "docs/master_plan/generated/PR208_ValidatorClassificationRegistry.report.json",
    "docs/master_plan/generated/PR208_ChangedAreaRoutingPolicy.report.json",
    "docs/master_plan/generated/PR208_CrossPlatformPathInvariant.report.json",
    "tools/run_validation_gates.py",
    "tools/ci_branch_context.py",
    "tools/changed_area_validation_router.py",
    "tools/validation_inventory.py",
    "tools/repo_path_refs.py",
    "tools/cross_platform_path_invariant.py",
)

OPTIONAL_INPUT_GROUPS = {
    "repo_local_historical_replay_datasets": (
        "data/replay_paper/historical",
        "docs/master_plan/generated/ReplayPaperHistoricalEventDatasetIndex.report.json",
    ),
    "repo_local_paper_simulation_fixtures": (
        "tests/fixtures/replay_paper",
        "docs/master_plan/generated/PaperSimulationFixtureIndex.report.json",
    ),
    "pr162e_f_formula_registry_artifacts": (
        "docs/master_plan/generated/PR162E_FormulaPluginRegistry.report.json",
        "docs/master_plan/generated/PR162F_FormulaAlgorithmIntakeRegistry.report.json",
    ),
    "pr162e_q_quantum_auto_mapper_artifacts": (
        "docs/master_plan/generated/PR162E_Q_QuantumAutoMapperRegistry.report.json",
        "docs/master_plan/generated/PR162E-Q_QuantumAutoMapperRegistry.report.json",
    ),
    "pr166_q_comparator_artifacts": (
        "docs/master_plan/generated/PR166_Q_QuantumClassicalComparatorResultRegistry.report.json",
        "docs/master_plan/generated/PR166-Q_QuantumClassicalComparatorResultRegistry.report.json",
    ),
    "unexpected_retest_result_artifacts": (
        "docs/master_plan/generated/PR166_S_ReplayPaperRetestResultRegistry.report.json",
        "docs/master_plan/generated/PR166-S_ReplayPaperRetestResultRegistry.report.json",
    ),
}

REPORT_FILENAMES = (
    "PR166_S_InputConsumptionAudit.report.json",
    "PR166_S_OptionalReplayPaperInputMissingReceipt.report.json",
    "PR166_S_ExternalDesignScoutCandidateLedger.report.json",
    "PR166_S_SelectedBatchConsumptionRegistry.report.json",
    "PR166_S_ReplayEpisodeRegistry.report.json",
    "PR166_S_PaperEpisodeRegistry.report.json",
    "PR166_S_EventStreamRegistry.report.json",
    "PR166_S_ExecutionModelAssumptionLedger.report.json",
    "PR166_S_ExecutionSensitivityScenarioGrid.report.json",
    "PR166_S_OrderIntentRegistry.report.json",
    "PR166_S_OrderStateTransitionLedger.report.json",
    "PR166_S_SimulatedFillLedger.report.json",
    "PR166_S_FeeModelLedger.report.json",
    "PR166_S_SpreadModelLedger.report.json",
    "PR166_S_SlippageModelLedger.report.json",
    "PR166_S_LatencyModelLedger.report.json",
    "PR166_S_LiquidityModelLedger.report.json",
    "PR166_S_MarketImpactModelLedger.report.json",
    "PR166_S_SettlementAssumptionLedger.report.json",
    "PR166_S_ExecutionCostLedger.report.json",
    "PR166_S_ReplayRunResultRegistry.report.json",
    "PR166_S_PaperRunResultRegistry.report.json",
    "PR166_S_ResultAttributionLedger.report.json",
    "PR166_S_ResultConfidenceRegistry.report.json",
    "PR166_S_ScoreRefreshCandidateRegistry.report.json",
    "PR166_S_MemoryRefreshCandidateRegistry.report.json",
    "PR166_S_RepairFeedbackRouter.report.json",
    "PR166_S_QuantumAdvisoryPassthrough.report.json",
    "PR166_S_AgentExecutionContract.report.json",
    "PR166_S_AgentExecutionHandoff.report.json",
    "PR166_S_DashboardExecutionHandoff.report.json",
    "PR166_S_GovernanceExecutionHandoff.report.json",
    "PR166_S_CommanderExecutionHandoff.report.json",
    "PR166_S_PointInTimeExecutionAudit.report.json",
    "PR166_S_NoLookaheadAudit.report.json",
    "PR166_S_LineageGraph.report.json",
    "PR166_S_AuthorityBoundaryAudit.report.json",
    "PR166_S_OrphanArtifactAudit.report.json",
    "PR166_S_PRFileConnectivityAudit.report.json",
    "PR166_S_RowValueConnectivityAudit.report.json",
    "PR166_S_TerminalArtifactReceiptRegistry.report.json",
    "PR166_S_ReportManifest.report.json",
    "PR166_S_FinalSummary.report.json",
)

SUMMARY_REPORTS = frozenset(
    {
        "PR166_S_InputConsumptionAudit.report.json",
        "PR166_S_OptionalReplayPaperInputMissingReceipt.report.json",
        "PR166_S_ExternalDesignScoutCandidateLedger.report.json",
        "PR166_S_AuthorityBoundaryAudit.report.json",
        "PR166_S_OrphanArtifactAudit.report.json",
        "PR166_S_PRFileConnectivityAudit.report.json",
        "PR166_S_RowValueConnectivityAudit.report.json",
        "PR166_S_TerminalArtifactReceiptRegistry.report.json",
        "PR166_S_ReportManifest.report.json",
        "PR166_S_FinalSummary.report.json",
    }
)
ROW_LEVEL_REPORTS = frozenset(filename for filename in REPORT_FILENAMES if filename not in SUMMARY_REPORTS)

SCHEMA_FILENAMES = (
    "pr166_s_report_manifest.schema.json",
    "pr166_s_input_consumption_audit.schema.json",
    "pr166_s_optional_replay_paper_input_receipt.schema.json",
    "pr166_s_external_design_scouting.schema.json",
    "pr166_s_replay_episode.schema.json",
    "pr166_s_paper_episode.schema.json",
    "pr166_s_event_stream.schema.json",
    "pr166_s_execution_model_assumption.schema.json",
    "pr166_s_execution_sensitivity_scenario.schema.json",
    "pr166_s_order_intent.schema.json",
    "pr166_s_order_state_transition.schema.json",
    "pr166_s_fill_record.schema.json",
    "pr166_s_fee_model.schema.json",
    "pr166_s_spread_model.schema.json",
    "pr166_s_slippage_model.schema.json",
    "pr166_s_latency_model.schema.json",
    "pr166_s_liquidity_model.schema.json",
    "pr166_s_market_impact_model.schema.json",
    "pr166_s_settlement_assumption.schema.json",
    "pr166_s_execution_cost_record.schema.json",
    "pr166_s_replay_run_result.schema.json",
    "pr166_s_paper_run_result.schema.json",
    "pr166_s_result_attribution.schema.json",
    "pr166_s_result_confidence.schema.json",
    "pr166_s_score_refresh_candidate.schema.json",
    "pr166_s_memory_refresh_candidate.schema.json",
    "pr166_s_repair_feedback_route.schema.json",
    "pr166_s_quantum_advisory_passthrough.schema.json",
    "pr166_s_agent_execution_contract.schema.json",
    "pr166_s_agent_execution_handoff.schema.json",
    "pr166_s_dashboard_handoff.schema.json",
    "pr166_s_governance_handoff.schema.json",
    "pr166_s_commander_handoff.schema.json",
    "pr166_s_point_in_time_execution_audit.schema.json",
    "pr166_s_no_lookahead_audit.schema.json",
    "pr166_s_lineage_graph_record.schema.json",
    "pr166_s_orphan_audit.schema.json",
    "pr166_s_authority_boundary_audit.schema.json",
    "pr166_s_final_summary.schema.json",
    "pr166_s_pr_file_connectivity_audit.schema.json",
    "pr166_s_row_value_connectivity_audit.schema.json",
    "pr166_s_terminal_artifact_receipt.schema.json",
)

REPORT_SCHEMA_REFS = {
    "PR166_S_InputConsumptionAudit.report.json": "pr166_s_input_consumption_audit.schema.json",
    "PR166_S_OptionalReplayPaperInputMissingReceipt.report.json": "pr166_s_optional_replay_paper_input_receipt.schema.json",
    "PR166_S_ExternalDesignScoutCandidateLedger.report.json": "pr166_s_external_design_scouting.schema.json",
    "PR166_S_SelectedBatchConsumptionRegistry.report.json": "pr166_s_replay_episode.schema.json",
    "PR166_S_ReplayEpisodeRegistry.report.json": "pr166_s_replay_episode.schema.json",
    "PR166_S_PaperEpisodeRegistry.report.json": "pr166_s_paper_episode.schema.json",
    "PR166_S_EventStreamRegistry.report.json": "pr166_s_event_stream.schema.json",
    "PR166_S_ExecutionModelAssumptionLedger.report.json": "pr166_s_execution_model_assumption.schema.json",
    "PR166_S_ExecutionSensitivityScenarioGrid.report.json": "pr166_s_execution_sensitivity_scenario.schema.json",
    "PR166_S_OrderIntentRegistry.report.json": "pr166_s_order_intent.schema.json",
    "PR166_S_OrderStateTransitionLedger.report.json": "pr166_s_order_state_transition.schema.json",
    "PR166_S_SimulatedFillLedger.report.json": "pr166_s_fill_record.schema.json",
    "PR166_S_FeeModelLedger.report.json": "pr166_s_fee_model.schema.json",
    "PR166_S_SpreadModelLedger.report.json": "pr166_s_spread_model.schema.json",
    "PR166_S_SlippageModelLedger.report.json": "pr166_s_slippage_model.schema.json",
    "PR166_S_LatencyModelLedger.report.json": "pr166_s_latency_model.schema.json",
    "PR166_S_LiquidityModelLedger.report.json": "pr166_s_liquidity_model.schema.json",
    "PR166_S_MarketImpactModelLedger.report.json": "pr166_s_market_impact_model.schema.json",
    "PR166_S_SettlementAssumptionLedger.report.json": "pr166_s_settlement_assumption.schema.json",
    "PR166_S_ExecutionCostLedger.report.json": "pr166_s_execution_cost_record.schema.json",
    "PR166_S_ReplayRunResultRegistry.report.json": "pr166_s_replay_run_result.schema.json",
    "PR166_S_PaperRunResultRegistry.report.json": "pr166_s_paper_run_result.schema.json",
    "PR166_S_ResultAttributionLedger.report.json": "pr166_s_result_attribution.schema.json",
    "PR166_S_ResultConfidenceRegistry.report.json": "pr166_s_result_confidence.schema.json",
    "PR166_S_ScoreRefreshCandidateRegistry.report.json": "pr166_s_score_refresh_candidate.schema.json",
    "PR166_S_MemoryRefreshCandidateRegistry.report.json": "pr166_s_memory_refresh_candidate.schema.json",
    "PR166_S_RepairFeedbackRouter.report.json": "pr166_s_repair_feedback_route.schema.json",
    "PR166_S_QuantumAdvisoryPassthrough.report.json": "pr166_s_quantum_advisory_passthrough.schema.json",
    "PR166_S_AgentExecutionContract.report.json": "pr166_s_agent_execution_contract.schema.json",
    "PR166_S_AgentExecutionHandoff.report.json": "pr166_s_agent_execution_handoff.schema.json",
    "PR166_S_DashboardExecutionHandoff.report.json": "pr166_s_dashboard_handoff.schema.json",
    "PR166_S_GovernanceExecutionHandoff.report.json": "pr166_s_governance_handoff.schema.json",
    "PR166_S_CommanderExecutionHandoff.report.json": "pr166_s_commander_handoff.schema.json",
    "PR166_S_PointInTimeExecutionAudit.report.json": "pr166_s_point_in_time_execution_audit.schema.json",
    "PR166_S_NoLookaheadAudit.report.json": "pr166_s_no_lookahead_audit.schema.json",
    "PR166_S_LineageGraph.report.json": "pr166_s_lineage_graph_record.schema.json",
    "PR166_S_AuthorityBoundaryAudit.report.json": "pr166_s_authority_boundary_audit.schema.json",
    "PR166_S_OrphanArtifactAudit.report.json": "pr166_s_orphan_audit.schema.json",
    "PR166_S_PRFileConnectivityAudit.report.json": "pr166_s_pr_file_connectivity_audit.schema.json",
    "PR166_S_RowValueConnectivityAudit.report.json": "pr166_s_row_value_connectivity_audit.schema.json",
    "PR166_S_TerminalArtifactReceiptRegistry.report.json": "pr166_s_terminal_artifact_receipt.schema.json",
    "PR166_S_ReportManifest.report.json": "pr166_s_report_manifest.schema.json",
    "PR166_S_FinalSummary.report.json": "pr166_s_final_summary.schema.json",
}

SOURCE_FILENAMES = (
    "__init__.py",
    "paths.py",
    "json_io.py",
    "deterministic_ids.py",
    "central_vocab.py",
    "authority_policy.py",
    "input_consumption.py",
    "optional_input_receipts.py",
    "external_design_scouting.py",
    "selected_batch_loader.py",
    "replay_episode_builder.py",
    "paper_episode_builder.py",
    "event_stream_builder.py",
    "execution_model_assumptions.py",
    "execution_sensitivity_grid.py",
    "order_intent_builder.py",
    "order_state_machine.py",
    "fill_model.py",
    "fee_model.py",
    "spread_model.py",
    "slippage_model.py",
    "latency_model.py",
    "liquidity_model.py",
    "market_impact_model.py",
    "settlement_assumption_model.py",
    "execution_cost_engine.py",
    "replay_run_engine.py",
    "paper_run_engine.py",
    "result_attribution.py",
    "result_confidence.py",
    "score_refresh_candidates.py",
    "memory_refresh_candidates.py",
    "repair_feedback_router.py",
    "quantum_advisory_passthrough.py",
    "agent_execution_contract.py",
    "agent_execution_handoff.py",
    "dashboard_execution_handoff.py",
    "governance_execution_handoff.py",
    "commander_execution_handoff.py",
    "point_in_time_execution_audit.py",
    "no_lookahead_audit.py",
    "lineage_graph_builder.py",
    "orphan_artifact_audit.py",
    "report_sharding.py",
    "schema_writer.py",
    "validators.py",
    "report_builder.py",
    "tests_support.py",
)


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def ensure_branch(repo_root: Path) -> None:
    branch = current_branch(repo_root)
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"PR166-S must build on {EXPECTED_BRANCH}, got {branch}")


def normalize_repo_ref(value: str | Path) -> str:
    raw = value.as_posix() if isinstance(value, (PurePosixPath, PureWindowsPath)) else str(value)
    windows_ref = PureWindowsPath(raw)
    if windows_ref.drive or windows_ref.root:
        raise ValueError(f"repo ref must be relative: {raw}")
    normalized = raw.replace("\\", "/")
    posix_ref = PurePosixPath(normalized)
    if posix_ref.is_absolute():
        raise ValueError(f"repo ref must be relative: {raw}")
    parts = tuple(part for part in posix_ref.parts if part != ".")
    if not parts:
        raise ValueError("repo ref must not be empty")
    if any(part == ".." for part in parts):
        raise ValueError(f"repo ref must not contain '..': {raw}")
    return "/".join(parts)


def to_repo_posix(path: Path, repo_root: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        root = Path(repo_root).resolve()
        try:
            candidate = candidate.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError(f"path is outside repo root: {path}") from exc
    return normalize_repo_ref(candidate)


def resolve_repo_relative(repo_root: Path, repo_ref: str | Path) -> Path:
    normalized = normalize_repo_ref(repo_ref)
    return Path(repo_root).joinpath(*normalized.split("/"))


def schema_path(repo_root: Path, filename: str) -> Path:
    return repo_root / SCHEMA_DIR / filename
