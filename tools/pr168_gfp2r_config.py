#!/usr/bin/env python3
"""Central constants for PR168-GFP2R DATA1A-gated candidate recompute."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
CANDIDATE_DIR = GENERATED_ROOT / "pr168_gfp2r_candidate_compute"

TOOL_NAME = "tools/build_pr168_gfp2r_data1a_gated_candidate_recompute.py"
REPORT_VERSION = "PR168-GFP2R-v3.0"
BRANCH_NAME = "pr168-gfp2r-data1a-gated-candidate-recompute"
PR234_MERGE_COMMIT = "dd31ba5129f3c427a67b7ffeadaa9fc80d2cb36f"

REQUIRED_DATA1A_REPORT_IDS = [
    "PR168_DATA1A_FinalSummary",
    "PR168_DATA1A_InputDiscovery",
    "PR168_DATA1A_FetchInventoryAudit",
    "PR168_DATA1A_DataProductIntegrityLedger",
    "PR168_DATA1A_QKUUnblockDeltaAudit",
    "PR168_DATA1A_DataQualityCoverageAudit",
    "PR168_DATA1A_HistoricalFullBookTruthLedger",
    "PR168_DATA1A_GFP2RReadinessDecision",
    "PR168_DATA1A_GFP2RAllowedDataFamilyContract",
    "PR168_DATA1A_QKUFormulaDataRequirementBridge",
    "PR168_DATA1A_QKUComputabilityRouteLedger",
    "PR168_DATA1A_FormulaInputCoverageMatrix",
    "PR168_DATA1A_DataQualitySeverityActionQueue",
    "PR168_DATA1A_RP2RANK2BatchReadinessAudit",
    "PR168_DATA1A_QuantumForwardUsabilityAudit",
    "PR168_DATA1A_AlphaCaptureReadinessMatrix",
    "PR168_DATA1A_NegativeToPositiveRecoveryReadinessQueue",
    "PR168_DATA1A_AgentRoutingAndNoOrphanProof",
    "PR168_DATA1A_DAGUpstreamDownstreamOrchestration",
    "PR168_DATA1A_EveryValueUpstreamDownstreamCrosswalk",
    "PR168_DATA1A_AgentConsumableDataValueRoutingLedger",
    "PR168_DATA1A_OperatorActionMatrix",
]

REQUIRED_DATA1_REPORT_IDS = [
    "PR168_DATA1_FinalSummary",
    "PR168_DATA1_PR168_GFP2R_DataReadyFormulaUniverse",
    "PR168_DATA1_PR168_RP2_FirstReplayPaperRecomputeBatch",
    "PR168_DATA1_PR168_RANK2_FirstEvidenceRankingBatch",
    "PR168_DATA1_QuantumForwardCoefficientFeatureSurface",
    "PR168_DATA1_NormalizedMarketDataFeatureRegistry",
]

REQUIRED_AGENT_REPORT_IDS = [
    "PR165_D2_AgentRosterDiscoveryAudit",
    "PR165_D2_AgentDutySourceCrosswalk",
]

REQUIRED_REPORT_IDS = [
    "PR168_GFP2R_InputDiscovery",
    "PR168_GFP2R_DATA1AConsumptionAudit",
    "PR168_GFP2R_AllowedDataFamilyContractConsumption",
    "PR168_GFP2R_QKUFormulaMappingRepairLedger",
    "PR168_GFP2R_DataConsumerToQKUFormulaBridge",
    "PR168_GFP2R_MappingRepairConfidenceLedger",
    "PR168_GFP2R_QKUFormulaRepairAndExpansionFactory",
    "PR168_GFP2R_FormulaVariantGenerationLedger",
    "PR168_GFP2R_FormulaAliasAndInputNormalizationLedger",
    "PR168_GFP2R_FormulaEquivalenceDeduplicationLedger",
    "PR168_GFP2R_FormulaUnitDimensionValidationLedger",
    "PR168_GFP2R_ExactCandidateComputeEligibility",
    "PR168_GFP2R_ProvisionalDataConsumerComputeEligibility",
    "PR168_GFP2R_CandidateFormulaExecutionLedger",
    "PR168_GFP2R_ProvisionalDataConsumerComputeLedger",
    "PR168_GFP2R_CandidateFormulaExecutionReceipts",
    "PR168_GFP2R_CandidateNumericEvidenceLedger",
    "PR168_GFP2R_CandidateEvidenceClassification",
    "PR168_GFP2R_BreakEvenAndRequiredEdgeThresholdLedger",
    "PR168_GFP2R_MarketImpliedProbabilityDisciplineLedger",
    "PR168_GFP2R_IndependentProbabilityInputGapLedger",
    "PR168_GFP2R_HistoricalFullBookDependencyRepairQueue",
    "PR168_GFP2R_ExecutionAdjustedCandidateSeed",
    "PR168_GFP2R_TCAFillLatencyCapacitySeed",
    "PR168_GFP2R_NoTradeComparatorSeed",
    "PR168_GFP2R_CandidateStackSearchSpaceSeed",
    "PR168_GFP2R_BreakEvenProbabilityThresholdSeed",
    "PR168_GFP2R_NegativeToPositiveRecoveryRepairQueue",
    "PR168_GFP2R_WeakCandidateRepairDiagnosis",
    "PR168_GFP2R_RecoveryPriorityScoringSeed",
    "PR168_GFP2R_RecoveryVariantGenerationLedger",
    "PR168_GFP2R_OverfitFDRTrialFamilySeed",
    "PR168_GFP2R_CalibrationSampleSizeGapSeed",
    "PR168_GFP2R_PortfolioMarginalUtilitySeed",
    "PR168_GFP2R_RegimeConditionedMemorySeed",
    "PR168_GFP2R_ScenarioLadderSeed",
    "PR168_GFP2R_QuantumStructuralCandidateMap",
    "PR168_GFP2R_QuantumObjectiveCoefficientConstraintSeed",
    "PR168_GFP2R_ClassicalFallbackComparatorSeed",
    "PR168_GFP2R_QuantumInterpretBackRepairQueue",
    "PR168_GFP2R_QuantumCoefficientQualityLedger",
    "PR168_GFP2R_QuantumFormulaVariantCoverageLedger",
    "PR168_GFP2R_To_PR168_RP2_CandidateFormulaRecomputeRows",
    "PR168_GFP2R_To_PR168_RANK2_CandidateRankingRows",
    "PR168_GFP2R_To_PR165B_ConditionScopedMemorySeed",
    "PR168_GFP2R_To_PR167_OpenTradeSimulatorSeed",
    "PR168_GFP2R_To_DATA1B_DataAcquisitionRepairQueue",
    "PR168_GFP2R_AgentRoutingAndNoOrphanProof",
    "PR168_GFP2R_DAGUpstreamDownstreamOrchestration",
    "PR168_GFP2R_EveryValueUpstreamDownstreamCrosswalk",
    "PR168_GFP2R_AgentConsumableCandidateComputeLedger",
    "PR168_GFP2R_EndpointAssumptionDriftHandoff",
    "PR168_GFP2R_OperatorActionMatrix",
    "PR168_GFP2R_ReportEssentialityAndDeduplicationAudit",
    "PR168_GFP2R_FinalSummary",
]

OPTIONAL_REPORT_IDS = [
    "PR168_GFP2R_MissingAgentCrosswalkBlocker",
    "PR168_GFP2R_MissingDATA1AArtifactsBlocker",
    "PR168_GFP2R_MissingFormulaRegistryBlocker",
    "PR168_GFP2R_OnlineVerificationNetworkUnavailableReceipt",
    "PR168_GFP2R_NoCandidateComputePossibleRootCause",
]

ROW_SHARDS = {
    "mapping_repair": CANDIDATE_DIR / "mapping_repair_rows.jsonl",
    "formula_variant": CANDIDATE_DIR / "formula_variant_rows.jsonl",
    "formula_equivalence": CANDIDATE_DIR / "formula_equivalence_rows.jsonl",
    "compute_eligibility": CANDIDATE_DIR / "compute_eligibility_rows.jsonl",
    "formula_execution": CANDIDATE_DIR / "formula_execution_rows.jsonl",
    "provisional_compute": CANDIDATE_DIR / "provisional_compute_rows.jsonl",
    "break_even_threshold": CANDIDATE_DIR / "break_even_threshold_rows.jsonl",
    "candidate_numeric_evidence": CANDIDATE_DIR / "candidate_numeric_evidence_rows.jsonl",
    "recovery_variant": CANDIDATE_DIR / "recovery_variant_rows.jsonl",
    "rp2_handoff": CANDIDATE_DIR / "rp2_handoff_rows.jsonl",
    "rank2_handoff": CANDIDATE_DIR / "rank2_handoff_rows.jsonl",
    "quantum_candidate_stack": CANDIDATE_DIR / "quantum_candidate_stack_rows.jsonl",
    "operator_action": CANDIDATE_DIR / "operator_action_rows.jsonl",
}

AUTHORITY_FALSE_FLAGS = {
    "manual_edit_allowed_flag": False,
    "live_authority_created_flag": False,
    "profit_evidence_created_flag": False,
    "source_truth_acceptance_created_flag": False,
    "connector_semantic_binding_created_flag": False,
    "private_state_access_created_flag": False,
    "order_authority_created_flag": False,
    "quantum_backend_execution_flag": False,
    "quantum_advantage_claim_flag": False,
    "qtt_sha_or_atomicrows_hash_authority_flag": False,
}

VALIDATOR_REFS = [
    "tools/pr168_gfp2r_validator.py",
    "tools/validate_pr168_gfp2r_data1a_gated_candidate_recompute.py",
]
TEST_REFS = ["tests/pr168_gfp2r"]
DOWNSTREAM_PRS = [
    "PR168-RP2",
    "PR168-RANK2",
    "PR165-B",
    "PR167",
    "PR162E-Q",
    "PR166-Q",
    "PR166-QB",
    "PR166-QC",
    "DATA1B",
]

ROUTES = {
    "formula": {
        "owning_agent": "qku_formula_materialization_agent",
        "consumer_agents": [
            "formula_execution_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "risk_tca_capacity_agent",
            "quantum_optimizer_agent",
            "dashboard_operator_agent",
        ],
    },
    "execution": {
        "owning_agent": "formula_execution_agent",
        "consumer_agents": [
            "replay_paper_agent",
            "ranking_scoring_agent",
            "risk_tca_capacity_agent",
            "dashboard_operator_agent",
        ],
    },
    "risk": {
        "owning_agent": "risk_tca_capacity_agent",
        "consumer_agents": [
            "formula_execution_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "dashboard_operator_agent",
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
    "ranking": {
        "owning_agent": "ranking_scoring_agent",
        "consumer_agents": [
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
    "source_evidence": {
        "owning_agent": "source_evidence_agent",
        "consumer_agents": [
            "market_data_acquisition_agent",
            "governance_validation_agent",
            "dashboard_operator_agent",
        ],
    },
    "market_data": {
        "owning_agent": "market_data_acquisition_agent",
        "consumer_agents": [
            "source_evidence_agent",
            "qku_formula_materialization_agent",
            "replay_paper_agent",
            "ranking_scoring_agent",
            "dashboard_operator_agent",
        ],
    },
    "governance": {
        "owning_agent": "governance_validation_agent",
        "consumer_agents": [
            "dashboard_operator_agent",
            "source_evidence_agent",
            "qku_formula_materialization_agent",
        ],
    },
}

ALLOWED_DATA_FAMILIES = [
    "current_orderbook_snapshot",
    "forward_l2_after_capture_start",
    "historical_trade",
    "recent_trade",
    "historical_candle",
    "market_candle",
    "price_history",
    "market_lifecycle",
    "resolution_or_settlement_if_present",
    "fee_tick_min_size_if_present",
    "data_quality_score_non_proof",
]

FORBIDDEN_OUTPUT_CLASSIFICATIONS = {
    "REAL_POSITIVE",
    "REAL_NEGATIVE",
    "REAL_NO_TRADE_DOMINANT",
    "CHAMPION",
    "LIVE_CANDIDATE",
    "PROFIT_PROOF",
}

VALID_MAPPING_CLASSES = {
    "EXACT_QKU_FORMULA_CANDIDATE_COMPUTE_READY",
    "EXACT_REPAIRED_QKU_FORMULA_CANDIDATE_COMPUTE_READY",
    "EXACT_QKU_FORMULA_REQUIRES_FORMULA_INPUT_REPAIR",
    "EXACT_QKU_MATCH_FORMULA_UNKNOWN",
    "FORMULA_MATCH_QKU_UNKNOWN",
    "DATA_CONSUMER_REQUIREMENT_MATCH_ONLY",
    "PROVISIONAL_DATA_CONSUMER_FORMULA_COMPUTE_READY",
    "PROVISIONAL_TO_EXACT_REPAIR_CANDIDATE",
    "FORMULA_VARIANT_GENERATED_NON_PROOF",
    "FORMULA_VARIANT_DUPLICATE_SUPPRESSED",
    "FORMULA_VARIANT_UNIT_INVALID",
    "FORMULA_VARIANT_DATA_INSUFFICIENT",
    "INFERRED_COMPONENT_FAMILY_MATCH_REPAIR_ONLY",
    "HISTORICAL_FULL_BOOK_DEPENDENT_REPAIR_ONLY",
    "FORECASTEX_IBKR_AUTH_DEPENDENT_REPAIR_ONLY",
    "STRUCTURALLY_NOT_COMPUTABLE_WITH_PROOF",
    "UNKNOWN_BASELINE_MISSING_UPSTREAM_REF",
}

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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def report_path(report_id: str) -> Path:
    return GENERATED_ROOT / f"{report_id}.report.json"


def generated_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def manifest_path(jsonl_path: Path) -> Path:
    return jsonl_path.with_suffix(".manifest.json")


def authority_flags() -> dict[str, bool]:
    return dict(AUTHORITY_FALSE_FLAGS)


def route_defaults(
    route_key: str = "governance",
    *,
    upstream_refs: list[str] | None = None,
    data1_refs: list[str] | None = None,
    data1a_refs: list[str] | None = None,
    formula_refs: list[str] | None = None,
    formula_variant_refs: list[str] | None = None,
    row_shard_refs: list[str] | None = None,
    numeric_evidence_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    computed_from_refs: list[str] | None = None,
    terminal_by_nature_flag: bool = False,
    terminal_reason_code: str | None = None,
    authority_class: str = "PR168_GFP2R_CANDIDATE_ONLY_NON_PROOF",
) -> dict[str, Any]:
    route = ROUTES[route_key]
    return {
        "upstream_input_refs": list(upstream_refs or []),
        "upstream_refs": list(upstream_refs or []),
        "DATA1_refs": list(data1_refs or []),
        "DATA1A_refs": list(data1a_refs or []),
        "formula_refs": list(formula_refs or []),
        "formula_variant_refs_if_available": list(formula_variant_refs or []),
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
        "repair_route_if_gap": None,
        "authority_class": authority_class,
        **authority_flags(),
    }
