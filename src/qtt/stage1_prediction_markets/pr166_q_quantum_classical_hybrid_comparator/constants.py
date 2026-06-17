"""Constants for PR166-Q quantum/classical/hybrid comparator."""

from __future__ import annotations

from pathlib import Path
import re

PR_ID = "PR166-Q"
BASE_BRANCH = "main"
EXPECTED_BRANCH = "pr166-q-quantum-classical-hybrid-comparator"
CREATED_AT_UTC = "2026-06-17T00:00:00Z"
AUTHORITY_CLASS = "PR166_Q_REPLAY_PAPER_QUANTUM_CLASSICAL_HYBRID_COMPARATOR_ONLY"
AUTHORITY_BOUNDARY_REF = (
    "PR166_Q_AUTHORITY_BOUNDARY::REPLAY_PAPER_ONLY_NO_LIVE_SOURCE_TRUTH_"
    "CONNECTOR_BINDING_PROFIT_QUANTUM_BACKEND_QTT_SHA_OR_ATOMICROWS_HASH"
)
VALIDATION_STATUS = "PASS"
VALIDATOR_REF = "tools/validate_pr166_q_quantum_classical_hybrid_comparator.py"
BUILDER_REF = "tools/build_pr166_q_quantum_classical_hybrid_comparator.py"
MANIFEST_REF = "PR166_Q_ReportManifest.report.json"
NOT_APPLICABLE = "NOT_APPLICABLE_FOR_THIS_ROW"
NOT_TERMINAL_REASON = "ROW_CONTINUES_TO_DECLARED_DOWNSTREAM_ROUTE"
REVIEW_ROUTE = "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW"

GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr166_q_shards"
PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
TEST_DIR = Path(
    "tests/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator"
)
PACKAGE_IMPORT = (
    "src.qtt.stage1_prediction_markets."
    "pr166_q_quantum_classical_hybrid_comparator"
)
DEFAULT_SHARD_ROW_TARGET = 750
ROOT_REPORT_LIMIT_BYTES = 10 * 1024 * 1024
SHARD_LIMIT_BYTES = 25 * 1024 * 1024

UPSTREAM_PR_REFS: tuple[str, ...] = (
    "PR165-D3",
    "PR166-SM3",
    "PR166-SF-R2",
    "PR166-SM2",
    "PR165-D2",
    "PR166-S2",
    "PR166-SF",
    "PR166-S",
    "PR165-D",
    "PR165-C",
    "PR165-B",
    "PR165",
    "PR164",
)
DOWNSTREAM_PR_REFS: tuple[str, ...] = (
    "PR166-QB",
    "PR166-QC",
    "PR162E-Q",
    "PR167",
    "PR162D-R3",
    "PR162E",
    "PR162F",
    REVIEW_ROUTE,
)

REPORT_FILENAMES: tuple[str, ...] = (
    "PR166_Q_InputHandoffConsumption.report.json",
    "PR166_Q_RootReportConsumptionLedger.report.json",
    "PR166_Q_UniversalArtifactConsumerMap.report.json",
    "PR166_Q_SourceReadingAndCandidateExtractionLedger.report.json",
    "PR166_Q_QuantumStructuralReadiness.report.json",
    "PR166_Q_ClassicalBaselineComparator.report.json",
    "PR166_Q_QuantumInspiredComparator.report.json",
    "PR166_Q_HybridComparator.report.json",
    "PR166_Q_QUBOReadinessRegistry.report.json",
    "PR166_Q_BQMReadinessRegistry.report.json",
    "PR166_Q_IsingReadinessRegistry.report.json",
    "PR166_Q_CQMReadinessRegistry.report.json",
    "PR166_Q_DQMReadinessRegistry.report.json",
    "PR166_Q_QuadraticProgramReadinessRegistry.report.json",
    "PR166_Q_ObjectiveVariableConstraintPenaltyMap.report.json",
    "PR166_Q_ExecutionAdjustedRanking.report.json",
    "PR166_Q_TCADecomposition.report.json",
    "PR166_Q_OrderBookQueueRiskLedger.report.json",
    "PR166_Q_LatencyCostRiskLedger.report.json",
    "PR166_Q_OverfitFalseDiscoveryControl.report.json",
    "PR166_Q_PurgedWalkForwardValidationPlan.report.json",
    "PR166_Q_PortfolioDiversificationLedger.report.json",
    "PR166_Q_CapacityCrowdingLimitLedger.report.json",
    "PR166_Q_ChampionChallengerSelection.report.json",
    "PR166_Q_RegimeConditionedMemory.report.json",
    "PR166_Q_ScenarioMemoryRetrievalLedger.report.json",
    "PR166_Q_MarginalUtilitySelection.report.json",
    "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
    "PR166_Q_QuantumRelevantNegativeRepairTriage.report.json",
    "PR166_Q_AgentWorkOrderLedger.report.json",
    "PR166_Q_AgentOrchestrationDAG.report.json",
    "PR166_Q_NoOrphanProof.report.json",
    "PR166_Q_ExternalCandidateIntakeLedger.report.json",
    "PR166_Q_ComputabilityDispositionLedger.report.json",
    "PR166_Q_RepairFillActionQueue.report.json",
    "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
    "PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json",
    "PR166_Q_PR162E_Q_AutoMapperHandoff.report.json",
    "PR166_Q_PR167_OpenTradeSimulatorHandoff.report.json",
    "PR166_Q_PR162D_R3_ExternalAcquisitionGapHandoff.report.json",
    "PR166_Q_PR162E_PluginFrameworkHandoff.report.json",
    "PR166_Q_PR162F_OwnerAgentIntakeHandoff.report.json",
    "PR166_Q_FinalSummary.report.json",
    "PR166_Q_ReportManifest.report.json",
)

ROW_LEVEL_REPORTS = frozenset(
    {
        "PR166_Q_QuantumStructuralReadiness.report.json",
        "PR166_Q_ClassicalBaselineComparator.report.json",
        "PR166_Q_QuantumInspiredComparator.report.json",
        "PR166_Q_HybridComparator.report.json",
        "PR166_Q_QUBOReadinessRegistry.report.json",
        "PR166_Q_BQMReadinessRegistry.report.json",
        "PR166_Q_IsingReadinessRegistry.report.json",
        "PR166_Q_CQMReadinessRegistry.report.json",
        "PR166_Q_DQMReadinessRegistry.report.json",
        "PR166_Q_QuadraticProgramReadinessRegistry.report.json",
        "PR166_Q_ObjectiveVariableConstraintPenaltyMap.report.json",
        "PR166_Q_ExecutionAdjustedRanking.report.json",
        "PR166_Q_TCADecomposition.report.json",
        "PR166_Q_OrderBookQueueRiskLedger.report.json",
        "PR166_Q_LatencyCostRiskLedger.report.json",
        "PR166_Q_OverfitFalseDiscoveryControl.report.json",
        "PR166_Q_PurgedWalkForwardValidationPlan.report.json",
        "PR166_Q_PortfolioDiversificationLedger.report.json",
        "PR166_Q_CapacityCrowdingLimitLedger.report.json",
        "PR166_Q_ChampionChallengerSelection.report.json",
        "PR166_Q_RegimeConditionedMemory.report.json",
        "PR166_Q_ScenarioMemoryRetrievalLedger.report.json",
        "PR166_Q_MarginalUtilitySelection.report.json",
        "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
        "PR166_Q_QuantumRelevantNegativeRepairTriage.report.json",
        "PR166_Q_AgentWorkOrderLedger.report.json",
        "PR166_Q_AgentOrchestrationDAG.report.json",
        "PR166_Q_NoOrphanProof.report.json",
        "PR166_Q_ComputabilityDispositionLedger.report.json",
        "PR166_Q_RepairFillActionQueue.report.json",
        "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
        "PR166_Q_PR166_QC_QuantumSelectedReplayPaperRetestHandoff.report.json",
        "PR166_Q_PR162E_Q_AutoMapperHandoff.report.json",
        "PR166_Q_PR167_OpenTradeSimulatorHandoff.report.json",
        "PR166_Q_PR162D_R3_ExternalAcquisitionGapHandoff.report.json",
        "PR166_Q_PR162E_PluginFrameworkHandoff.report.json",
        "PR166_Q_PR162F_OwnerAgentIntakeHandoff.report.json",
    }
)
SUMMARY_REPORTS = frozenset(name for name in REPORT_FILENAMES if name not in ROW_LEVEL_REPORTS)

STRICT_INPUT_REPORTS: tuple[str, ...] = (
    "PR166_SM3_PR166QHandoff.report.json",
    "PR166_SM3_PR166QBHandoff.report.json",
    "PR166_SM3_PR166QCHandoff.report.json",
    "PR166_SM3_QuantumPriority.report.json",
    "PR166_SM3_ReportManifest.report.json",
    "PR166_SM3_RowDAG.report.json",
    "PR166_SM3_AgentConsumerMap.report.json",
    "PR166_SM3_AgentDutyLedger.report.json",
    "PR166_SM3_AgentTaskQueue.report.json",
    "PR166_SM3_TCAScore.report.json",
    "PR166_SM3_OverfitFDR.report.json",
    "PR166_SM3_CapacityCrowding.report.json",
    "PR166_SM3_RegimeMemory.report.json",
    "PR166_SM3_MarginalUtility.report.json",
    "PR166_SF_R2_PR166QHandoff.report.json",
    "PR166_SF_R2_QuantumRepair.report.json",
    "PR166_SF_R2_QuantumObjectiveMap.report.json",
    "PR166_SF_R2_TCALedger.report.json",
    "PR166_SF_R2_NetEdgeLedger.report.json",
    "PR166_SF_R2_Microstructure.report.json",
    "PR166_SF_R2_CapacityCrowding.report.json",
    "PR166_SF_R2_OverfitFDR.report.json",
    "PR165_D3_SelectionUniverse.report.json",
    "PR165_D3_SelectedCombos.report.json",
    "PR165_D3_NoTradeDecisions.report.json",
    "PR165_D3_ReplayRetestQueue.report.json",
    "PR165_D3_RepairRoute.report.json",
    "PR165_D3_QUBOModelReady.report.json",
    "PR165_D3_CQMModelReady.report.json",
    "PR165_D3_QuantumObjectiveMap.report.json",
    "PR165_D3_QuantumPortfolioOpt.report.json",
)
OPTIONAL_INPUT_REPORTS: tuple[str, ...] = (
    "PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "PR165_D2_AgentDutySourceCrosswalk.report.json",
    "PR166_SM2_ReportManifest.report.json",
    "PR166_SF_R2_ReportManifest.report.json",
    "PR165_D3_ReportManifest.report.json",
    "PR166_SM3_FinalSummary.report.json",
    "PR166_SF_R2_FinalSummary.report.json",
    "PR165_D3_FinalSummary.report.json",
)

COMPUTABILITY_DISPOSITIONS: tuple[str, ...] = (
    "COMPUTABLE_NOW",
    "COMPUTABLE_WITH_CANDIDATE_ASSUMPTIONS",
    "COMPUTABLE_AFTER_NARROW_FILL_ACTION",
    "QUANTUM_REFORMULATION_TRIAGE_REQUIRED",
    "EXCLUDED_UNSAFE_OR_IMPOSSIBLE_WITH_EXACT_REASON",
)
FORBIDDEN_COMPUTABILITY_DISPOSITIONS: tuple[str, ...] = (
    "METADATA_ONLY_READY",
    "SOLVER_LABEL_ONLY_READY",
    "FUTURE_CONSUMER_NOTE_ONLY_READY",
    "PLACEHOLDER_READY",
    "UNKNOWN_BUT_PASS",
    "BLOCKED_WITHOUT_FILL_ACTION",
    "NON_COMPUTABLE_BUT_COUNTED_AS_SUCCESS",
    "NEGATIVE_BUT_IGNORED",
    "ORPHANED_REPAIR_CANDIDATE",
)
MODEL_FAMILIES: tuple[str, ...] = (
    "QUBO",
    "BQM",
    "Ising",
    "CQM",
    "DQM",
    "QuadraticProgram",
)
CHAMPION_ROLES: tuple[str, ...] = (
    "champion",
    "challenger",
    "watch",
    "retest",
    "repair",
    "no-trade",
)
AGENT_IDS: tuple[str, ...] = (
    "Commander",
    "Governance",
    "Research Agent",
    "Source/External Scout Agent",
    "QKU/Formula Materialization Agent",
    "Quantum Optimizer",
    "Quantum Comparator Agent",
    "Classical Comparator Agent",
    "Portfolio/Risk Agent",
    "Execution/TCA Agent",
    "Replay Agent",
    "Paper Agent",
    "Dashboard/Owner Review Agent",
    "Quantum Repair Triage Agent",
    "External Acquisition Agent",
)

SOURCE_READING_ROWS: tuple[dict[str, object], ...] = (
    {
        "source_id": "SRC_QISKIT_OPTIMIZATION_QUADRATIC_PROGRAM",
        "source_type": "official_quantum_optimization_docs",
        "official_flag": True,
        "non_official_flag": False,
        "source_locator_or_query": "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.QuadraticProgram.html",
        "candidate_values_extracted_count": 4,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 1,
        "quantum_structures_extracted_count": 1,
        "parameter_ranges_extracted_count": 1,
        "quantum_mapping_patterns_extracted_count": 2,
        "routed_report_refs": ["PR166_Q_QuadraticProgramReadinessRegistry.report.json"],
    },
    {
        "source_id": "SRC_QISKIT_CONVERTERS",
        "source_type": "official_quantum_converter_docs",
        "official_flag": True,
        "non_official_flag": False,
        "source_locator_or_query": "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html",
        "candidate_values_extracted_count": 7,
        "formulas_extracted_count": 1,
        "algorithms_extracted_count": 6,
        "quantum_structures_extracted_count": 2,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 6,
        "routed_report_refs": ["PR166_Q_QuadraticProgramReadinessRegistry.report.json", "PR166_Q_QUBOReadinessRegistry.report.json"],
    },
    {
        "source_id": "SRC_QISKIT_MINIMUM_EIGEN_OPTIMIZER",
        "source_type": "official_quantum_algorithm_docs",
        "official_flag": True,
        "non_official_flag": False,
        "source_locator_or_query": "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.algorithms.MinimumEigenOptimizer.html",
        "candidate_values_extracted_count": 3,
        "formulas_extracted_count": 1,
        "algorithms_extracted_count": 3,
        "quantum_structures_extracted_count": 2,
        "parameter_ranges_extracted_count": 1,
        "quantum_mapping_patterns_extracted_count": 2,
        "routed_report_refs": ["PR166_Q_HybridComparator.report.json"],
    },
    {
        "source_id": "SRC_DWAVE_MODELS",
        "source_type": "official_quantum_model_docs",
        "official_flag": True,
        "non_official_flag": False,
        "source_locator_or_query": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "candidate_values_extracted_count": 5,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 2,
        "quantum_structures_extracted_count": 4,
        "parameter_ranges_extracted_count": 1,
        "quantum_mapping_patterns_extracted_count": 5,
        "routed_report_refs": ["PR166_Q_BQMReadinessRegistry.report.json", "PR166_Q_CQMReadinessRegistry.report.json", "PR166_Q_DQMReadinessRegistry.report.json"],
    },
    {
        "source_id": "SRC_DWAVE_REFORMULATION",
        "source_type": "official_quantum_reformulation_docs",
        "official_flag": True,
        "non_official_flag": False,
        "source_locator_or_query": "https://docs.dwavequantum.com/en/latest/quantum_research/reformulating.html",
        "candidate_values_extracted_count": 4,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 1,
        "quantum_structures_extracted_count": 3,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 5,
        "routed_report_refs": ["PR166_Q_QuantumRelevantNegativeRepairTriage.report.json"],
    },
    {
        "source_id": "SRC_DWAVE_HYBRID_SOLVERS",
        "source_type": "official_hybrid_solver_docs",
        "official_flag": True,
        "non_official_flag": False,
        "source_locator_or_query": "https://docs.dwavequantum.com/en/latest/industrial_optimization/dwave_hybrid.html",
        "candidate_values_extracted_count": 3,
        "formulas_extracted_count": 1,
        "algorithms_extracted_count": 3,
        "quantum_structures_extracted_count": 3,
        "parameter_ranges_extracted_count": 1,
        "quantum_mapping_patterns_extracted_count": 3,
        "routed_report_refs": ["PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json"],
    },
    {
        "source_id": "SRC_AMAZON_BRAKET_HYBRID_JOBS",
        "source_type": "official_hybrid_quantum_docs",
        "official_flag": True,
        "non_official_flag": False,
        "source_locator_or_query": "https://docs.aws.amazon.com/braket/latest/developerguide/braket-jobs.html",
        "candidate_values_extracted_count": 3,
        "formulas_extracted_count": 1,
        "algorithms_extracted_count": 2,
        "quantum_structures_extracted_count": 1,
        "parameter_ranges_extracted_count": 1,
        "quantum_mapping_patterns_extracted_count": 1,
        "routed_report_refs": ["PR166_Q_HybridComparator.report.json"],
    },
    {
        "source_id": "SRC_BAILEY_PBO",
        "source_type": "research_backtest_overfitting",
        "official_flag": False,
        "non_official_flag": True,
        "source_locator_or_query": "https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf",
        "candidate_values_extracted_count": 4,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 1,
        "quantum_structures_extracted_count": 0,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 0,
        "routed_report_refs": ["PR166_Q_OverfitFalseDiscoveryControl.report.json"],
    },
    {
        "source_id": "SRC_CPCV_DSR_RESEARCH",
        "source_type": "research_false_discovery_control",
        "official_flag": False,
        "non_official_flag": True,
        "source_locator_or_query": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4686376",
        "candidate_values_extracted_count": 5,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 2,
        "quantum_structures_extracted_count": 0,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 0,
        "routed_report_refs": ["PR166_Q_PurgedWalkForwardValidationPlan.report.json"],
    },
    {
        "source_id": "SRC_IMPLEMENTATION_SHORTFALL_TCA",
        "source_type": "research_execution_tca",
        "official_flag": False,
        "non_official_flag": True,
        "source_locator_or_query": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2807317",
        "candidate_values_extracted_count": 6,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 1,
        "quantum_structures_extracted_count": 0,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 0,
        "routed_report_refs": ["PR166_Q_TCADecomposition.report.json"],
    },
    {
        "source_id": "SRC_LIMIT_ORDER_LATENCY_ADVERSE_SELECTION",
        "source_type": "research_order_book_queue_risk",
        "official_flag": False,
        "non_official_flag": True,
        "source_locator_or_query": "https://arxiv.org/pdf/1610.00261",
        "candidate_values_extracted_count": 5,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 1,
        "quantum_structures_extracted_count": 0,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 0,
        "routed_report_refs": ["PR166_Q_OrderBookQueueRiskLedger.report.json"],
    },
    {
        "source_id": "SRC_POLYMARKET_MICROSTRUCTURE",
        "source_type": "prediction_market_microstructure_research",
        "official_flag": False,
        "non_official_flag": True,
        "source_locator_or_query": "https://arxiv.org/html/2604.24366v1",
        "candidate_values_extracted_count": 5,
        "formulas_extracted_count": 1,
        "algorithms_extracted_count": 1,
        "quantum_structures_extracted_count": 0,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 0,
        "routed_report_refs": ["PR166_Q_OrderBookQueueRiskLedger.report.json", "PR166_Q_RegimeConditionedMemory.report.json"],
    },
    {
        "source_id": "SRC_QUANTUM_INSPIRED_PORTFOLIO_QUBO",
        "source_type": "research_quantum_inspired_portfolio",
        "official_flag": False,
        "non_official_flag": True,
        "source_locator_or_query": "https://arxiv.org/html/2410.05932v3",
        "candidate_values_extracted_count": 4,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 3,
        "quantum_structures_extracted_count": 2,
        "parameter_ranges_extracted_count": 2,
        "quantum_mapping_patterns_extracted_count": 2,
        "routed_report_refs": ["PR166_Q_QuantumInspiredComparator.report.json", "PR166_Q_PortfolioDiversificationLedger.report.json"],
    },
    {
        "source_id": "SRC_QUBO_ISING_MAPPING_STARTER",
        "source_type": "research_quantum_mapping",
        "official_flag": False,
        "non_official_flag": True,
        "source_locator_or_query": "https://www.cmu.edu/sites/default/files/cmu-tepper-site-files/documents/Five%20Starter%20Problems%20Solving%20Quadratic%20Unconstrained%20Binary%20Optimization%20Models%20on%20Quantum%20Computers.pdf",
        "candidate_values_extracted_count": 4,
        "formulas_extracted_count": 2,
        "algorithms_extracted_count": 1,
        "quantum_structures_extracted_count": 2,
        "parameter_ranges_extracted_count": 1,
        "quantum_mapping_patterns_extracted_count": 3,
        "routed_report_refs": ["PR166_Q_IsingReadinessRegistry.report.json"],
    },
)


def _schema_name(report_filename: str) -> str:
    stem = report_filename.removesuffix(".report.json").replace("PR166_Q_", "pr166_q_")
    stem = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", stem)
    stem = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", stem)
    stem = stem.replace("__", "_").lower()
    return f"{stem}.schema.json"


REPORT_SCHEMA_REFS = {name: _schema_name(name) for name in REPORT_FILENAMES}
SCHEMA_FILENAMES: tuple[str, ...] = (
    "pr166_q_common.schema.json",
    *(REPORT_SCHEMA_REFS[name] for name in REPORT_FILENAMES),
)
