"""Constants for PR166-QB bounded non-live quantum optimizer benchmark."""

from __future__ import annotations

from pathlib import Path

PR_ID = "PR166-QB"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-qb-bounded-nonlive-quantum-optimizer-benchmark"
CREATED_AT_UTC = "2026-06-17T00:00:00Z"
AUTHORITY_CLASS = "PR166_QB_BOUNDED_NONLIVE_QUANTUM_BENCHMARK_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_QB_AUTHORITY_BOUNDARY::BOUNDED_NONLIVE_NO_CLOUD_BACKEND_"
    "NO_CREDENTIALS_NO_LIVE_SOURCE_TRUTH_CONNECTOR_PROFIT_OR_ADVANTAGE"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_qb_bounded_quantum_benchmark.py"
BUILDER_REF = "tools/build_pr166_qb_bounded_quantum_benchmark.py"
MANIFEST_REF = "PR166_QB_ReportManifest.report.json"
NOT_APPLICABLE = "NOT_APPLICABLE_FOR_THIS_ROW"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr166_qb_shards"
PACKAGE_DIR = Path("src/qtt/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark")
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path("tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark")
PACKAGE_IMPORT = "src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark"
DEFAULT_SHARD_ROW_TARGET = 750

STRICT_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
    "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
    "PR166_Q_QuantumStructuralReadiness.report.json",
    "PR166_Q_QUBOReadinessRegistry.report.json",
    "PR166_Q_BQMReadinessRegistry.report.json",
    "PR166_Q_IsingReadinessRegistry.report.json",
    "PR166_Q_CQMReadinessRegistry.report.json",
    "PR166_Q_DQMReadinessRegistry.report.json",
    "PR166_Q_QuadraticProgramReadinessRegistry.report.json",
    "PR166_Q_ClassicalBaselineComparator.report.json",
    "PR166_Q_QuantumInspiredComparator.report.json",
    "PR166_Q_HybridComparator.report.json",
    "PR166_Q_ExecutionAdjustedRanking.report.json",
    "PR166_Q_TCADecomposition.report.json",
    "PR166_Q_OrderBookQueueRiskLedger.report.json",
    "PR166_Q_LatencyCostRiskLedger.report.json",
    "PR166_Q_OverfitFalseDiscoveryControl.report.json",
    "PR166_Q_PortfolioDiversificationLedger.report.json",
    "PR166_Q_CapacityCrowdingLimitLedger.report.json",
    "PR166_Q_MarginalUtilitySelection.report.json",
    "PR166_Q_AgentWorkOrderLedger.report.json",
    "PR166_Q_AgentOrchestrationDAG.report.json",
    "PR166_Q_UniversalArtifactConsumerMap.report.json",
    "PR166_Q_NoOrphanProof.report.json",
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
)

EXPECTED_559_INPUTS: tuple[str, ...] = tuple(
    name
    for name in STRICT_INPUT_REPORTS
    if name
    not in {
        "PR166_Q_UniversalArtifactConsumerMap.report.json",
        "PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "PR165_D2_AgentDutySourceCrosswalk.report.json",
    }
)

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_QB_InputConsumption.report.json",
    "PR166_QB_BudgetPolicy.report.json",
    "PR166_QB_SourceBenchmarkParams.report.json",
    "PR166_QB_Eligibility.report.json",
    "PR166_QB_SubsetSelection.report.json",
    "PR166_QB_FairnessNorm.report.json",
    "PR166_QB_ClassicalReceipt.report.json",
    "PR166_QB_QInspiredReceipt.report.json",
    "PR166_QB_QAOAReceipt.report.json",
    "PR166_QB_SamplingVQEReceipt.report.json",
    "PR166_QB_AnnealTabuReceipt.report.json",
    "PR166_QB_QUBOReceipt.report.json",
    "PR166_QB_BQMReceipt.report.json",
    "PR166_QB_IsingReceipt.report.json",
    "PR166_QB_CQMReceipt.report.json",
    "PR166_QB_DQMReceipt.report.json",
    "PR166_QB_QuadProgramReceipt.report.json",
    "PR166_QB_ObjectiveQuality.report.json",
    "PR166_QB_RuntimeLatency.report.json",
    "PR166_QB_SeedStability.report.json",
    "PR166_QB_TCARanking.report.json",
    "PR166_QB_OverfitPenalty.report.json",
    "PR166_QB_PortfolioUtility.report.json",
    "PR166_QB_ChampChallenger.report.json",
    "PR166_QB_RegimeMemory.report.json",
    "PR166_QB_RaceLedger.report.json",
    "PR166_QB_RaceArb.report.json",
    "PR166_QB_BackendReadyNoExec.report.json",
    "PR166_QB_CloudSwitchReady.report.json",
    "PR166_QB_OwnerQuantumControlReady.report.json",
    "PR166_QB_MarketPortability.report.json",
    "PR166_QB_DependencyLedger.report.json",
    "PR166_QB_QuantumRepairLab.report.json",
    "PR166_QB_AgentWorkOrders.report.json",
    "PR166_QB_AgentDAG.report.json",
    "PR166_QB_NoOrphanProof.report.json",
    "PR166_QB_ArtifactMap.report.json",
    "PR166_QB_To_PR166_QC.report.json",
    "PR166_QB_To_PR162E_Q.report.json",
    "PR166_QB_To_PR167.report.json",
    "PR166_QB_To_PR162E.report.json",
    "PR166_QB_To_PR162F.report.json",
    "PR166_QB_To_CloudSwitchboard.report.json",
    "PR166_QB_To_OwnerDashboard.report.json",
    "PR166_QB_FinalSummary.report.json",
    "PR166_QB_ReportManifest.report.json",
)

BENCHMARK_ROW_REPORTS: frozenset[str] = frozenset(
    {
        "PR166_QB_Eligibility.report.json",
        "PR166_QB_SubsetSelection.report.json",
        "PR166_QB_FairnessNorm.report.json",
        "PR166_QB_ClassicalReceipt.report.json",
        "PR166_QB_QInspiredReceipt.report.json",
        "PR166_QB_QAOAReceipt.report.json",
        "PR166_QB_SamplingVQEReceipt.report.json",
        "PR166_QB_AnnealTabuReceipt.report.json",
        "PR166_QB_QUBOReceipt.report.json",
        "PR166_QB_BQMReceipt.report.json",
        "PR166_QB_IsingReceipt.report.json",
        "PR166_QB_CQMReceipt.report.json",
        "PR166_QB_DQMReceipt.report.json",
        "PR166_QB_QuadProgramReceipt.report.json",
        "PR166_QB_ObjectiveQuality.report.json",
        "PR166_QB_RuntimeLatency.report.json",
        "PR166_QB_SeedStability.report.json",
        "PR166_QB_TCARanking.report.json",
        "PR166_QB_OverfitPenalty.report.json",
        "PR166_QB_PortfolioUtility.report.json",
        "PR166_QB_ChampChallenger.report.json",
        "PR166_QB_RegimeMemory.report.json",
        "PR166_QB_RaceLedger.report.json",
        "PR166_QB_RaceArb.report.json",
        "PR166_QB_BackendReadyNoExec.report.json",
        "PR166_QB_MarketPortability.report.json",
        "PR166_QB_QuantumRepairLab.report.json",
        "PR166_QB_AgentWorkOrders.report.json",
        "PR166_QB_AgentDAG.report.json",
        "PR166_QB_NoOrphanProof.report.json",
        "PR166_QB_To_PR166_QC.report.json",
        "PR166_QB_To_PR162E_Q.report.json",
        "PR166_QB_To_PR167.report.json",
        "PR166_QB_To_PR162E.report.json",
        "PR166_QB_To_PR162F.report.json",
        "PR166_QB_To_CloudSwitchboard.report.json",
        "PR166_QB_To_OwnerDashboard.report.json",
    }
)

SUMMARY_REPORTS: frozenset[str] = frozenset(name for name in REPORT_FILENAMES if name not in BENCHMARK_ROW_REPORTS)

MODEL_FAMILIES: tuple[str, ...] = (
    "QUBO",
    "BQM",
    "Ising",
    "CQM",
    "DQM",
    "QuadraticProgram",
)

BENCHMARK_DISPOSITIONS: tuple[str, ...] = (
    "BENCHMARK_EXECUTED_BOUNDED_LOCAL",
    "BENCHMARK_EXECUTED_QUANTUM_INSPIRED_LOCAL",
    "BENCHMARK_EXECUTED_CLASSICAL_BASELINE_LOCAL",
    "BENCHMARK_EXECUTED_SURROGATE_LOCAL",
    "BENCHMARK_STRUCTURAL_ONLY_DEPENDENCY_UNAVAILABLE",
    "BENCHMARK_STRUCTURAL_ONLY_RUNTIME_CAP",
    "BENCHMARK_SKIPPED_RUNTIME_CAP_WITH_EXACT_REASON",
    "BENCHMARK_SKIPPED_UNSUPPORTED_MODEL_WITH_EXACT_REASON",
    "BENCHMARK_ROUTED_TO_PR162E_Q_AUTOMAPPER",
    "BENCHMARK_ROUTED_TO_PR166_QC_REPLAY_PAPER_RETEST",
    "BENCHMARK_ROUTED_TO_FUTURE_CLOUD_SWITCHBOARD_NO_EXECUTION",
    "BENCHMARK_ROUTED_TO_OWNER_DASHBOARD_SWITCH_NO_EXECUTION",
    "BENCHMARK_ROUTED_TO_RACE_ARBITRATION_NONLIVE",
    "EXCLUDED_UNSAFE_OR_IMPOSSIBLE_WITH_EXACT_REASON",
)

FORBIDDEN_BENCHMARK_DISPOSITIONS: tuple[str, ...] = (
    "METADATA_ONLY_BENCHMARKED",
    "SOLVER_LABEL_ONLY_BENCHMARKED",
    "FUTURE_CONSUMER_NOTE_ONLY_BENCHMARKED",
    "PLACEHOLDER_BENCHMARKED",
    "UNKNOWN_BUT_PASS",
    "UNBOUNDED_BENCHMARK_EXECUTED",
    "CLOUD_BACKEND_EXECUTED",
    "QUANTUM_ADVANTAGE_CLAIMED",
    "PROFIT_EVIDENCE_CREATED",
    "LIVE_READY_CLAIMED",
)

EXECUTION_MODES: tuple[str, ...] = (
    "CLASSICAL_EXACT_SMALL",
    "CLASSICAL_GREEDY_HEURISTIC",
    "CLASSICAL_LOCAL_SEARCH",
    "CLASSICAL_MILP_OR_SCIPY_IF_AVAILABLE",
    "QUANTUM_INSPIRED_SIMULATED_ANNEALING_LOCAL",
    "QUANTUM_INSPIRED_TABU_LOCAL",
    "QAOA_LOCAL_SIMULATOR_IF_AVAILABLE",
    "SAMPLING_VQE_LOCAL_SIMULATOR_IF_AVAILABLE",
    "STRUCTURAL_READY_NO_EXECUTION_DEPENDENCY_UNAVAILABLE",
    "STRUCTURAL_READY_NO_EXECUTION_RUNTIME_CAP",
    "FUTURE_BACKEND_ROUTE_NO_EXECUTION",
    "FUTURE_CLOUD_SWITCHBOARD_ROUTE_NO_EXECUTION",
    "FUTURE_OWNER_DASHBOARD_TOGGLE_ROUTE_NO_EXECUTION",
    "FUTURE_RACE_ARBITRATION_ROUTE_NO_LIVE_AUTHORITY",
)

FORBIDDEN_EXECUTION_MODES: tuple[str, ...] = (
    "CLOUD_BACKEND_EXECUTION",
    "HARDWARE_QPU_EXECUTION",
    "CREDENTIAL_REQUIRED_EXECUTION",
    "UNBOUNDED_LOCAL_EXECUTION",
    "UNKNOWN_BUT_PASS",
    "PLACEHOLDER_BENCHMARK",
)

BENCHMARK_CAPS: dict[str, int] = {
    "max_actual_benchmark_rows_default_ci": 64,
    "max_rows_per_family_default_ci": 16,
    "max_qaoa_p_depth_default_ci": 2,
    "max_vqe_ansatz_layers_default_ci": 2,
    "max_optimizer_iterations_default_ci": 64,
    "max_samples_or_reads_default_ci": 512,
    "max_random_seeds_default_ci": 3,
    "max_problem_variables_default_ci": 32,
}

OWNER_CLOUD_MODES: tuple[str, ...] = (
    "OFF",
    "LOCAL_SIMULATOR_ONLY",
    "CLOUD_STRUCTURAL_READY_ONLY",
    "CLOUD_SHADOW_PAPER_ONLY",
    "CLOUD_PAPER_EXECUTION_ONLY",
    "CLOUD_LIVE_CANDIDATE_ONLY",
    "LIVE_ENABLED_WITH_OWNER_APPROVAL",
)

PROVIDER_FAMILIES: tuple[str, ...] = (
    "NONE",
    "IBM_QUANTUM",
    "AWS_BRAKET",
    "DWAVE_LEAP",
    "OTHER_CANDIDATE",
)

DOWNSTREAM_PR_REFS: tuple[str, ...] = (
    "PR166-QC",
    "PR162E-Q",
    "PR167",
    "PR162E",
    "PR162F",
    "FUTURE_CLOUD_SWITCHBOARD_ENABLEMENT",
    "FUTURE_OWNER_DASHBOARD_QUANTUM_CONTROL",
    "FUTURE_RACE_ARBITRATION",
)

AGENT_IDS: tuple[str, ...] = (
    "Commander",
    "Governance",
    "Research Agent",
    "Source/External Scout Agent",
    "QKU/Formula Materialization Agent",
    "Quantum Optimizer / Quantum Benchmark Agent",
    "Quantum Comparator Agent",
    "Classical Comparator Agent",
    "Portfolio/Risk Agent",
    "Execution/TCA Agent",
    "Replay Agent",
    "Paper Agent",
    "Dashboard/Owner Review Agent",
    "Quantum AutoMapper Agent",
    "Quantum Cloud Switchboard Agent",
    "Owner Dashboard Control Agent",
    "Race Arbitration Agent",
    "External Acquisition Agent",
)

CHAMPION_ROLES: tuple[str, ...] = (
    "benchmark champion",
    "benchmark challenger",
    "benchmark watch",
    "replay/paper retest",
    "automapper priority",
    "backend-readiness-only",
    "dependency-missing route",
    "runtime-cap route",
    "no-trade",
    "repair",
    "quantum-repair-lab",
    "race-arbitration-candidate",
    "future-cloud-switchboard-route",
    "future-owner-dashboard-toggle-route",
)
