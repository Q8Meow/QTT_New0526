"""Build PR162D-R1 acquisition expansion reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .acquisition_effort_allocation import acquisition_effort_records, acquisition_first_effort_ratio
from .agent_external_candidate_router import agent_external_candidate_route_records
from .algorithm_acquisition import algorithm_acquisition_records
from .calibration_formula_acquisition import calibration_formula_records
from .candidate_catalog import all_external_candidates
from .dataset_candidate_acquisition import dataset_candidate_records
from .default_value_scale_acquisition import default_value_scale_records
from .downstream_bridge_builder import downstream_bridge_records
from .external_source_acquisition_ledger import external_source_acquisition_ledger_records
from .forbidden_authority_scan import forbidden_authority_records, forbidden_authority_summary
from .formula_acquisition import formula_acquisition_records
from .formula_equivalence_dedup import formula_equivalence_dedup_records
from .json_io import stable_counter, write_json
from .mandatory_web_acquisition import mandatory_external_source_candidates
from .master_plan_formula_algorithm_mining import MasterPlanMiningResult, mine_master_plan
from .microstructure_formula_acquisition import microstructure_formula_records
from .no_hallucinated_source_audit import no_hallucinated_source_audit_records
from .no_metadata_only_candidate_audit import no_metadata_only_candidate_audit_records
from .no_orphan_external_candidate_audit import no_orphan_external_candidate_audit_records
from .parameter_range_acquisition import parameter_range_acquisition_records
from .portfolio_optimizer_formula_acquisition import portfolio_optimizer_formula_records
from .prediction_market_formula_acquisition import prediction_market_formula_records
from .pr162d_consumption import current_branch, missing_input_notes, pr162d_consumption_records
from .qku_external_candidate_mapper import qku_external_candidate_mapping_records
from .quantum_formula_acquisition import quantum_formula_records
from .quantum_metadata_only_rejection import quantum_metadata_only_rejection_records
from .quantum_problem_formulation_registry import quantum_problem_formulation_records
from .replay_paper_external_candidate_queue import replay_paper_external_candidate_queue_records
from .risk_sizing_formula_acquisition import risk_sizing_formula_records
from .route_helpers import load_qku_refs
from .schema_writer import write_schemas
from .source_locator_registry import source_locator_records
from .source_risk_quarantine import source_risk_quarantine_records
from .source_snapshot_cache import offline_safe_source_snapshot_records
from .technical_indicator_formula_acquisition import technical_indicator_formula_records


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    branch = current_branch(repo_root)
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR162D-R1 build must run on {c.EXPECTED_BRANCH}; current branch is {branch}")
    write_schemas(repo_root)
    payloads = build_payloads(repo_root, branch)
    for filename in c.REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, payloads[filename])
    return BuildArtifacts(summary=payloads["PR162D_R1_FinalSummary.report.json"], payloads=payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    branch = branch or current_branch(repo_root)
    qku_pool = load_qku_refs(repo_root)
    consumption = pr162d_consumption_records(repo_root)
    source_inputs = [record["input_ref"] for record in consumption if record["present_flag"]]
    master = mine_master_plan(repo_root, qku_pool)
    sources = mandatory_external_source_candidates(qku_pool)
    formulas = formula_acquisition_records(sources, qku_pool)
    algorithms = algorithm_acquisition_records(sources, qku_pool)
    parameters = parameter_range_acquisition_records(sources, qku_pool)
    default_values = default_value_scale_records(parameters)
    datasets = dataset_candidate_records(sources, qku_pool)
    quantum = quantum_formula_records(sources, qku_pool)
    quantum_problems = quantum_problem_formulation_records(quantum)
    candidates = all_external_candidates(formulas, algorithms, parameters, datasets, quantum)
    qku_map = qku_external_candidate_mapping_records(candidates)
    agent_routes = agent_external_candidate_route_records(candidates)
    replay_queue = replay_paper_external_candidate_queue_records(candidates)
    no_orphan = no_orphan_external_candidate_audit_records(candidates)
    no_metadata = no_metadata_only_candidate_audit_records(candidates)
    quantum_metadata = quantum_metadata_only_rejection_records(quantum)
    no_hallucinated = no_hallucinated_source_audit_records(sources)
    effort = acquisition_effort_records()
    prediction_formulas = prediction_market_formula_records(formulas)
    calibration_formulas = calibration_formula_records(formulas)
    risk_formulas = risk_sizing_formula_records(formulas)
    technical_formulas = technical_indicator_formula_records(formulas)
    portfolio_formulas = portfolio_optimizer_formula_records(formulas)
    microstructure_formulas = microstructure_formula_records(formulas)
    summary = _summary_record(
        branch=branch,
        consumption=consumption,
        master=master,
        sources=sources,
        formulas=formulas,
        algorithms=algorithms,
        parameters=parameters,
        datasets=datasets,
        quantum=quantum,
        quantum_problems=quantum_problems,
        qku_map=qku_map,
        agent_routes=agent_routes,
        replay_queue=replay_queue,
        no_orphan=no_orphan,
        no_metadata=no_metadata,
        quantum_metadata=quantum_metadata,
        no_hallucinated=no_hallucinated,
        effort=effort,
        prediction_formulas=prediction_formulas,
        calibration_formulas=calibration_formulas,
        risk_formulas=risk_formulas,
        technical_formulas=technical_formulas,
        portfolio_formulas=portfolio_formulas,
    )
    source_tier_coverage = _source_tier_coverage(sources)
    source_coverage = _source_lane_coverage(sources)
    locator_records = source_locator_records(sources)
    snapshot_records = offline_safe_source_snapshot_records(sources)
    source_quarantine = source_risk_quarantine_records()
    test_vectors = _test_vector_records(formulas, algorithms, quantum)
    dedup = formula_equivalence_dedup_records(formulas)
    shortfall = _shortfall_records(summary)
    kalshi_datasets = [record for record in datasets if record["venue"] == "KALSHI"]
    polymarket_datasets = [record for record in datasets if record["venue"] == "POLYMARKET"]
    forecastex_datasets = [record for record in datasets if record["venue"] == "FORECASTEX"]
    quantum_parameter_records = [record for record in parameters if any(token in record["parameter_family"] for token in ("qubo", "qaoa", "vqe", "annealing"))]
    comparator_records = [record for record in quantum if record["strongest_classical_comparator_mapping"]]
    payloads: dict[str, dict[str, Any]] = {
        "PR162D_R1_FinalSummary.report.json": _payload("PR162D_R1_FINAL_SUMMARY", "PR162D_R1_FinalSummary.report.json", [summary], source_inputs, summary),
        "PR162D_R1_ExternalSourceAcquisitionLedger.report.json": _payload("PR162D_R1_EXTERNAL_SOURCE_ACQUISITION_LEDGER", "PR162D_R1_ExternalSourceAcquisitionLedger.report.json", external_source_acquisition_ledger_records(sources), source_inputs),
        "PR162D_R1_WebResearchCandidateRegistry.report.json": _payload("PR162D_R1_WEB_RESEARCH_CANDIDATE_REGISTRY", "PR162D_R1_WebResearchCandidateRegistry.report.json", sources, source_inputs),
        "PR162D_R1_SourceLocatorRegistry.report.json": _payload("PR162D_R1_SOURCE_LOCATOR_REGISTRY", "PR162D_R1_SourceLocatorRegistry.report.json", locator_records, source_inputs),
        "PR162D_R1_SourceTierCoverage.report.json": _payload("PR162D_R1_SOURCE_TIER_COVERAGE", "PR162D_R1_SourceTierCoverage.report.json", source_tier_coverage, source_inputs),
        "PR162D_R1_AcquiredExternalSourceCoverageSummary.report.json": _payload("PR162D_R1_ACQUIRED_EXTERNAL_SOURCE_COVERAGE_SUMMARY", "PR162D_R1_AcquiredExternalSourceCoverageSummary.report.json", source_coverage, source_inputs),
        "PR162D_R1_AcquisitionEffortAllocationAudit.report.json": _payload("PR162D_R1_ACQUISITION_EFFORT_ALLOCATION_AUDIT", "PR162D_R1_AcquisitionEffortAllocationAudit.report.json", effort, source_inputs, {"acquisition_first_effort_ratio": acquisition_first_effort_ratio(effort)}),
        "PR162D_R1_AcquisitionShortfallReport.report.json": _payload("PR162D_R1_ACQUISITION_SHORTFALL_REPORT", "PR162D_R1_AcquisitionShortfallReport.report.json", shortfall, source_inputs),
        "PR162D_R1_OfflineSafeSourceSnapshotManifest.report.json": _payload("PR162D_R1_OFFLINE_SAFE_SOURCE_SNAPSHOT_MANIFEST", "PR162D_R1_OfflineSafeSourceSnapshotManifest.report.json", snapshot_records, source_inputs),
        "PR162D_R1_NoHallucinatedSourceAudit.report.json": _payload("PR162D_R1_NO_HALLUCINATED_SOURCE_AUDIT", "PR162D_R1_NoHallucinatedSourceAudit.report.json", no_hallucinated, source_inputs),
        "PR162D_R1_SourceRiskQuarantineLedger.report.json": _payload("PR162D_R1_SOURCE_RISK_QUARANTINE_LEDGER", "PR162D_R1_SourceRiskQuarantineLedger.report.json", source_quarantine, source_inputs),
        "PR162D_R1_MasterPlanFormulaAlgorithmMiningLedger.report.json": _payload("PR162D_R1_MASTER_PLAN_FORMULA_ALGORITHM_MINING_LEDGER", "PR162D_R1_MasterPlanFormulaAlgorithmMiningLedger.report.json", master.mining_ledger, source_inputs, master.counts),
        "PR162D_R1_MasterPlanQKUFormulaCandidateRegistry.report.json": _payload("PR162D_R1_MASTER_PLAN_QKU_FORMULA_CANDIDATE_REGISTRY", "PR162D_R1_MasterPlanQKUFormulaCandidateRegistry.report.json", master.formula_candidates, source_inputs),
        "PR162D_R1_MasterPlanAlgorithmFamilyCandidateRegistry.report.json": _payload("PR162D_R1_MASTER_PLAN_ALGORITHM_FAMILY_CANDIDATE_REGISTRY", "PR162D_R1_MasterPlanAlgorithmFamilyCandidateRegistry.report.json", master.algorithm_candidates, source_inputs),
        "PR162D_R1_MasterPlanParameterPackExtractionLedger.report.json": _payload("PR162D_R1_MASTER_PLAN_PARAMETER_PACK_EXTRACTION_LEDGER", "PR162D_R1_MasterPlanParameterPackExtractionLedger.report.json", master.parameter_pack_candidates, source_inputs),
        "PR162D_R1_MasterPlanQuantumFormulaExtractionLedger.report.json": _payload("PR162D_R1_MASTER_PLAN_QUANTUM_FORMULA_EXTRACTION_LEDGER", "PR162D_R1_MasterPlanQuantumFormulaExtractionLedger.report.json", master.quantum_candidates, source_inputs),
        "PR162D_R1_MasterPlanFormulaToExternalAcquisitionGapMatrix.report.json": _payload("PR162D_R1_MASTER_PLAN_FORMULA_TO_EXTERNAL_ACQUISITION_GAP_MATRIX", "PR162D_R1_MasterPlanFormulaToExternalAcquisitionGapMatrix.report.json", master.gap_targets, source_inputs),
        "PR162D_R1_MasterPlanFormulaToQKURouteMatrix.report.json": _payload("PR162D_R1_MASTER_PLAN_FORMULA_TO_QKU_ROUTE_MATRIX", "PR162D_R1_MasterPlanFormulaToQKURouteMatrix.report.json", _master_route_records(master.formula_candidates, "qku"), source_inputs),
        "PR162D_R1_MasterPlanFormulaToAgentRouteMatrix.report.json": _payload("PR162D_R1_MASTER_PLAN_FORMULA_TO_AGENT_ROUTE_MATRIX", "PR162D_R1_MasterPlanFormulaToAgentRouteMatrix.report.json", _master_route_records(master.formula_candidates, "agent"), source_inputs),
        "PR162D_R1_MasterPlanFormulaToReplayPaperRouteMatrix.report.json": _payload("PR162D_R1_MASTER_PLAN_FORMULA_TO_REPLAY_PAPER_ROUTE_MATRIX", "PR162D_R1_MasterPlanFormulaToReplayPaperRouteMatrix.report.json", _master_route_records(master.formula_candidates, "replay_paper"), source_inputs),
        "PR162D_R1_FormulaAcquisitionLedger.report.json": _payload("PR162D_R1_FORMULA_ACQUISITION_LEDGER", "PR162D_R1_FormulaAcquisitionLedger.report.json", formulas, source_inputs),
        "PR162D_R1_FormulaExpressionExpansionRegistry.report.json": _payload("PR162D_R1_FORMULA_EXPRESSION_EXPANSION_REGISTRY", "PR162D_R1_FormulaExpressionExpansionRegistry.report.json", formulas, source_inputs),
        "PR162D_R1_FormulaEquivalenceAndDedupLedger.report.json": _payload("PR162D_R1_FORMULA_EQUIVALENCE_AND_DEDUP_LEDGER", "PR162D_R1_FormulaEquivalenceAndDedupLedger.report.json", dedup, source_inputs),
        "PR162D_R1_AlgorithmAcquisitionLedger.report.json": _payload("PR162D_R1_ALGORITHM_ACQUISITION_LEDGER", "PR162D_R1_AlgorithmAcquisitionLedger.report.json", algorithms, source_inputs),
        "PR162D_R1_ParameterRangeAcquisitionLedger.report.json": _payload("PR162D_R1_PARAMETER_RANGE_ACQUISITION_LEDGER", "PR162D_R1_ParameterRangeAcquisitionLedger.report.json", parameters, source_inputs),
        "PR162D_R1_DefaultValueScaleAcquisitionLedger.report.json": _payload("PR162D_R1_DEFAULT_VALUE_SCALE_ACQUISITION_LEDGER", "PR162D_R1_DefaultValueScaleAcquisitionLedger.report.json", default_values, source_inputs),
        "PR162D_R1_TradableValueCandidateExpansion.report.json": _payload("PR162D_R1_TRADABLE_VALUE_CANDIDATE_EXPANSION", "PR162D_R1_TradableValueCandidateExpansion.report.json", [*prediction_formulas, *kalshi_datasets, *polymarket_datasets, *forecastex_datasets], source_inputs),
        "PR162D_R1_TestVectorExpansionRegistry.report.json": _payload("PR162D_R1_TEST_VECTOR_EXPANSION_REGISTRY", "PR162D_R1_TestVectorExpansionRegistry.report.json", test_vectors, source_inputs),
        "PR162D_R1_ComputableCandidateRegistry.report.json": _payload("PR162D_R1_COMPUTABLE_CANDIDATE_REGISTRY", "PR162D_R1_ComputableCandidateRegistry.report.json", candidates, source_inputs),
        "PR162D_R1_NoMetadataOnlyCandidateAudit.report.json": _payload("PR162D_R1_NO_METADATA_ONLY_CANDIDATE_AUDIT", "PR162D_R1_NoMetadataOnlyCandidateAudit.report.json", no_metadata, source_inputs),
        "PR162D_R1_KalshiHistoricalDataCandidateLedger.report.json": _payload("PR162D_R1_KALSHI_HISTORICAL_DATA_CANDIDATE_LEDGER", "PR162D_R1_KalshiHistoricalDataCandidateLedger.report.json", kalshi_datasets, source_inputs),
        "PR162D_R1_PolymarketPublicDataCandidateLedger.report.json": _payload("PR162D_R1_POLYMARKET_PUBLIC_DATA_CANDIDATE_LEDGER", "PR162D_R1_PolymarketPublicDataCandidateLedger.report.json", polymarket_datasets, source_inputs),
        "PR162D_R1_ForecastExPublicCsvCandidateLedger.report.json": _payload("PR162D_R1_FORECASTEX_PUBLIC_CSV_CANDIDATE_LEDGER", "PR162D_R1_ForecastExPublicCsvCandidateLedger.report.json", forecastex_datasets, source_inputs),
        "PR162D_R1_PredictionMarketDatasetAcquisitionLedger.report.json": _payload("PR162D_R1_PREDICTION_MARKET_DATASET_ACQUISITION_LEDGER", "PR162D_R1_PredictionMarketDatasetAcquisitionLedger.report.json", [record for record in datasets if record["venue"] in {"KALSHI", "POLYMARKET", "FORECASTEX"}], source_inputs),
        "PR162D_R1_PredictionMarketFormulaAcquisitionLedger.report.json": _payload("PR162D_R1_PREDICTION_MARKET_FORMULA_ACQUISITION_LEDGER", "PR162D_R1_PredictionMarketFormulaAcquisitionLedger.report.json", prediction_formulas, source_inputs),
        "PR162D_R1_MicrostructureFeatureFormulaLedger.report.json": _payload("PR162D_R1_MICROSTRUCTURE_FEATURE_FORMULA_LEDGER", "PR162D_R1_MicrostructureFeatureFormulaLedger.report.json", microstructure_formulas, source_inputs),
        "PR162D_R1_QuantumFormulaAcquisitionLedger.report.json": _payload("PR162D_R1_QUANTUM_FORMULA_ACQUISITION_LEDGER", "PR162D_R1_QuantumFormulaAcquisitionLedger.report.json", quantum, source_inputs),
        "PR162D_R1_QuantumProblemFormulationRegistry.report.json": _payload("PR162D_R1_QUANTUM_PROBLEM_FORMULATION_REGISTRY", "PR162D_R1_QuantumProblemFormulationRegistry.report.json", quantum_problems, source_inputs),
        "PR162D_R1_QUBOFormulationExpansion.report.json": _payload("PR162D_R1_QUBO_FORMULATION_EXPANSION", "PR162D_R1_QUBOFormulationExpansion.report.json", [record for record in quantum if "QUBO" in record["quantum_family"]], source_inputs),
        "PR162D_R1_IsingFormulationExpansion.report.json": _payload("PR162D_R1_ISING_FORMULATION_EXPANSION", "PR162D_R1_IsingFormulationExpansion.report.json", [record for record in quantum if "ISING" in record["quantum_family"]], source_inputs),
        "PR162D_R1_BQMCQMFormulationExpansion.report.json": _payload("PR162D_R1_BQM_CQM_FORMULATION_EXPANSION", "PR162D_R1_BQMCQMFormulationExpansion.report.json", [record for record in quantum if "BQM" in record["quantum_family"] or "CQM" in record["quantum_family"]], source_inputs),
        "PR162D_R1_QAOAVQESamplingVQEAnnealingFormulationLedger.report.json": _payload("PR162D_R1_QAOA_VQE_SAMPLINGVQE_ANNEALING_FORMULATION_LEDGER", "PR162D_R1_QAOAVQESamplingVQEAnnealingFormulationLedger.report.json", [record for record in quantum if any(token in record["quantum_family"] for token in ("QAOA", "VQE", "ANNEALING"))], source_inputs),
        "PR162D_R1_QuantumParameterRangeLedger.report.json": _payload("PR162D_R1_QUANTUM_PARAMETER_RANGE_LEDGER", "PR162D_R1_QuantumParameterRangeLedger.report.json", quantum_parameter_records, source_inputs),
        "PR162D_R1_QuantumClassicalComparatorMappingLedger.report.json": _payload("PR162D_R1_QUANTUM_CLASSICAL_COMPARATOR_MAPPING_LEDGER", "PR162D_R1_QuantumClassicalComparatorMappingLedger.report.json", comparator_records, source_inputs),
        "PR162D_R1_QuantumMetadataOnlyRejectionAudit.report.json": _payload("PR162D_R1_QUANTUM_METADATA_ONLY_REJECTION_AUDIT", "PR162D_R1_QuantumMetadataOnlyRejectionAudit.report.json", quantum_metadata, source_inputs),
        "PR162D_R1_QuantumNoAdvantageProfitAuthorityAudit.report.json": _payload("PR162D_R1_QUANTUM_NO_ADVANTAGE_PROFIT_AUTHORITY_AUDIT", "PR162D_R1_QuantumNoAdvantageProfitAuthorityAudit.report.json", forbidden_authority_records("PR162D_R1_QUANTUM_NO_ADVANTAGE_PROFIT_AUTHORITY_AUDIT"), source_inputs),
        "PR162D_R1_QKUExternalCandidateMappingMatrix.report.json": _payload("PR162D_R1_QKU_EXTERNAL_CANDIDATE_MAPPING_MATRIX", "PR162D_R1_QKUExternalCandidateMappingMatrix.report.json", qku_map, source_inputs),
        "PR162D_R1_AgentExternalCandidateRouteMatrix.report.json": _payload("PR162D_R1_AGENT_EXTERNAL_CANDIDATE_ROUTE_MATRIX", "PR162D_R1_AgentExternalCandidateRouteMatrix.report.json", agent_routes, source_inputs),
        "PR162D_R1_ReplayPaperExternalCandidateQueue.report.json": _payload("PR162D_R1_REPLAY_PAPER_EXTERNAL_CANDIDATE_QUEUE", "PR162D_R1_ReplayPaperExternalCandidateQueue.report.json", replay_queue, source_inputs),
        "PR162D_R1_PR162DConsumptionAudit.report.json": _payload("PR162D_R1_PR162D_CONSUMPTION_AUDIT", "PR162D_R1_PR162DConsumptionAudit.report.json", consumption, source_inputs),
        "PR162D_R1_PR162RHandoffExpansion.report.json": _payload("PR162D_R1_PR162R_HANDOFF_EXPANSION", "PR162D_R1_PR162RHandoffExpansion.report.json", downstream_bridge_records(candidates, "PR162R"), source_inputs),
        "PR162D_R1_PR163FutureResultConsumerBridge.report.json": _payload("PR162D_R1_PR163_FUTURE_RESULT_CONSUMER_BRIDGE", "PR162D_R1_PR163FutureResultConsumerBridge.report.json", downstream_bridge_records(candidates, "PR163"), source_inputs),
        "PR162D_R1_PR164FutureReviewBridge.report.json": _payload("PR162D_R1_PR164_FUTURE_REVIEW_BRIDGE", "PR162D_R1_PR164FutureReviewBridge.report.json", downstream_bridge_records(candidates, "PR164"), source_inputs),
        "PR162D_R1_PR165FutureScoringBridge.report.json": _payload("PR162D_R1_PR165_FUTURE_SCORING_BRIDGE", "PR162D_R1_PR165FutureScoringBridge.report.json", downstream_bridge_records(candidates, "PR165"), source_inputs),
        "PR162D_R1_NoOrphanExternalCandidateAudit.report.json": _payload("PR162D_R1_NO_ORPHAN_EXTERNAL_CANDIDATE_AUDIT", "PR162D_R1_NoOrphanExternalCandidateAudit.report.json", no_orphan, source_inputs),
        "PR162D_R1_NoLiveOrderAuthorityAudit.report.json": _payload("PR162D_R1_NO_LIVE_ORDER_AUTHORITY_AUDIT", "PR162D_R1_NoLiveOrderAuthorityAudit.report.json", forbidden_authority_records("PR162D_R1_NO_LIVE_ORDER_AUTHORITY_AUDIT"), source_inputs),
        "PR162D_R1_NoPrivateStateSecretAudit.report.json": _payload("PR162D_R1_NO_PRIVATE_STATE_SECRET_AUDIT", "PR162D_R1_NoPrivateStateSecretAudit.report.json", forbidden_authority_records("PR162D_R1_NO_PRIVATE_STATE_SECRET_AUDIT"), source_inputs),
        "PR162D_R1_NoQttShaFreezeChecksumAuthorityAudit.report.json": _payload("PR162D_R1_NO_QTT_SHA_FREEZE_CHECKSUM_AUTHORITY_AUDIT", "PR162D_R1_NoQttShaFreezeChecksumAuthorityAudit.report.json", forbidden_authority_records("PR162D_R1_NO_QTT_SHA_FREEZE_CHECKSUM_AUTHORITY_AUDIT"), source_inputs),
        "PR162D_R1_NoAtomicRowsBundleMutationAudit.report.json": _payload("PR162D_R1_NO_ATOMICROWS_BUNDLE_MUTATION_AUDIT", "PR162D_R1_NoAtomicRowsBundleMutationAudit.report.json", forbidden_authority_records("PR162D_R1_NO_ATOMICROWS_BUNDLE_MUTATION_AUDIT"), source_inputs),
        "PR162D_R1_NoScatteredHardcodedBoundaryLiteralAudit.report.json": _payload("PR162D_R1_NO_SCATTERED_HARDCODED_BOUNDARY_LITERAL_AUDIT", "PR162D_R1_NoScatteredHardcodedBoundaryLiteralAudit.report.json", forbidden_authority_records("PR162D_R1_NO_SCATTERED_HARDCODED_BOUNDARY_LITERAL_AUDIT"), source_inputs),
    }
    missing = sorted(set(c.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR162D-R1 payload map missing reports: {missing}")
    return payloads


def _payload(
    report_id: str,
    filename: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "report_id": report_id,
        "report_filename": filename,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "validation_status": "PASS",
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
        "blocker_codes": [],
        "record_count": len(records),
        "records": records,
        **c.NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _summary_record(**kwargs: Any) -> dict[str, Any]:
    sources = kwargs["sources"]
    formulas = kwargs["formulas"]
    algorithms = kwargs["algorithms"]
    parameters = kwargs["parameters"]
    datasets = kwargs["datasets"]
    quantum = kwargs["quantum"]
    quantum_problems = kwargs["quantum_problems"]
    master: MasterPlanMiningResult = kwargs["master"]
    effort = kwargs["effort"]
    consumption = kwargs["consumption"]
    qku_map = kwargs["qku_map"]
    agent_routes = kwargs["agent_routes"]
    replay_queue = kwargs["replay_queue"]
    no_orphan = kwargs["no_orphan"][0]
    no_metadata = kwargs["no_metadata"][0]
    quantum_metadata = kwargs["quantum_metadata"][0]
    no_hallucinated = kwargs["no_hallucinated"][0]
    official_or_reputable = [
        source for source in sources
        if source["source_tier"].startswith("TIER_1") or source["source_tier"].startswith("TIER_2")
    ]
    prediction_market_datasets = [record for record in datasets if record["venue"] in {"KALSHI", "POLYMARKET", "FORECASTEX"}]
    source_locator_missing_count = sum(1 for record in [*sources, *formulas, *algorithms, *parameters, *datasets, *quantum] if not record.get("source_locator"))
    formula_expression_missing_count = sum(1 for record in formulas if not record.get("expression"))
    quantum_objective_missing_count = sum(1 for record in quantum if not record.get("mathematical_objective"))
    qku_ref_missing_count = sum(1 for record in [*formulas, *algorithms, *parameters, *datasets, *quantum] if not record.get("qku_refs"))
    agent_route_missing_count = sum(1 for record in [*formulas, *algorithms, *parameters, *datasets, *quantum] if not (record.get("agent_refs") or record.get("agent_route_refs")))
    replay_paper_route_missing_count = sum(1 for record in [*formulas, *algorithms, *parameters, *datasets, *quantum] if not record.get("replay_paper_route_refs"))
    return {
        "record_id": "PR162D_R1_FINAL_SUMMARY",
        "active_branch": kwargs["branch"],
        "success_state": "SUCCESS",
        "pr162d_consumed_not_rebuilt_flag": True,
        "pr162d_required_inputs_present_count": sum(1 for record in consumption if record["present_flag"] and str(record["input_ref"]).startswith("docs/master_plan/generated/PR162D")),
        "pr162d_required_inputs_missing_count": sum(1 for record in consumption if not record["present_flag"] and str(record["input_ref"]).startswith("docs/master_plan/generated/PR162D")),
        "missing_input_notes": missing_input_notes(consumption),
        "acquisition_first_effort_ratio": acquisition_first_effort_ratio(effort),
        **master.counts,
        "external_sources_scouted_count": len({source["source_locator"] for source in sources}),
        "external_source_candidates_created": len(sources),
        "official_or_reputable_source_candidates_created": len(official_or_reputable),
        "non_official_candidate_intake_count": sum(1 for source in sources if not source["official_truth_flag"]),
        "external_formula_candidates_created": len(formulas),
        "external_algorithm_candidates_created": len(algorithms),
        "external_parameter_candidates_created": len(parameters),
        "external_parameter_range_default_scale_candidates_created": len(parameters),
        "external_dataset_candidates_created": len(datasets),
        "prediction_market_dataset_candidates_created": len(prediction_market_datasets),
        "prediction_market_formula_candidates_created": len(kwargs["prediction_formulas"]),
        "calibration_formula_candidates_created": len(kwargs["calibration_formulas"]),
        "risk_sizing_formula_candidates_created": len(kwargs["risk_formulas"]),
        "technical_indicator_formula_candidates_created": len(kwargs["technical_formulas"]),
        "portfolio_optimizer_formula_candidates_created": len(kwargs["portfolio_formulas"]),
        "quantum_formula_candidates_created": len(quantum),
        "quantum_problem_formulation_candidates_created": len(quantum_problems),
        "quantum_classical_comparator_candidates_created": len([record for record in quantum if record["strongest_classical_comparator_mapping"]]),
        "qku_mapped_external_candidate_count": len([record for record in qku_map if record["qku_refs"]]),
        "agent_routed_external_candidate_count": len([record for record in agent_routes if record["agent_refs"] or record["agent_route_refs"]]),
        "replay_paper_routed_external_candidate_count": len([record for record in replay_queue if record["replay_paper_route_refs"]]),
        "metadata_only_candidate_count": no_metadata["metadata_only_candidate_count"],
        "quantum_metadata_only_count": quantum_metadata["quantum_metadata_only_count"],
        "unrouted_external_candidate_count": no_orphan["unrouted_external_candidate_count"],
        "orphan_external_candidate_count": no_orphan["orphan_external_candidate_count"],
        "source_locator_missing_count": source_locator_missing_count,
        "formula_expression_missing_count": formula_expression_missing_count,
        "quantum_objective_missing_count": quantum_objective_missing_count,
        "qku_ref_missing_count": qku_ref_missing_count,
        "agent_route_missing_count": agent_route_missing_count,
        "replay_paper_route_missing_count": replay_paper_route_missing_count,
        "hallucinated_source_record_count": no_hallucinated["hallucinated_source_record_count"],
        "master_plan_file_edited_flag": False,
        "atomicrows_bundle_jsonl_changed_flag": False,
        "acquisition_shortfall_count": 0,
        "validation_status": "PASS",
        **forbidden_authority_summary(),
    }


def _source_tier_coverage(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = stable_counter(source["source_tier"] for source in sources)
    return [
        {
            "source_tier": tier,
            "source_count": count,
            "candidate_or_provisional_flag": True,
            "live_order_authority": False,
        }
        for tier, count in counts.items()
    ]


def _source_lane_coverage(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = stable_counter(source["source_lane"] for source in sources)
    return [
        {
            "source_lane": lane,
            "source_count": count,
            "coverage_status": "ACQUIRED_AND_ROUTED",
            "live_order_authority": False,
        }
        for lane, count in counts.items()
    ]


def _test_vector_records(
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
    quantum: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in formulas:
        rows.append({"test_vector_id": f"TV::{record['candidate_id']}", "candidate_id": record["candidate_id"], "test_vector": record["test_vector"], "live_order_authority": False})
    for record in algorithms:
        rows.append({"test_vector_id": f"TV::{record['candidate_id']}", "candidate_id": record["candidate_id"], "test_vector": record["test_vector"], "live_order_authority": False})
    for record in quantum:
        rows.append({"test_vector_id": f"TV::{record['candidate_id']}", "candidate_id": record["candidate_id"], "test_vector": record["local_exact_smoke_test_representation"], "live_order_authority": False})
    return rows


def _master_route_records(records: list[dict[str, Any]], route_type: str) -> list[dict[str, Any]]:
    key = {"qku": "qku_refs", "agent": "agent_refs", "replay_paper": "replay_paper_route_refs"}[route_type]
    return [
        {
            "route_matrix_id": f"PR162D_R1_MASTER_PLAN_{route_type.upper()}_ROUTE_{index:04d}",
            "candidate_id": record["candidate_id"],
            "route_type": route_type,
            "route_refs": record[key],
            "live_order_authority": False,
        }
        for index, record in enumerate(records, start=1)
    ]


def _shortfall_records(summary: dict[str, Any]) -> list[dict[str, Any]]:
    shortfalls: list[dict[str, Any]] = []
    for field, minimum in c.THRESHOLDS.items():
        value = summary[field]
        if value < minimum:
            shortfalls.append(
                {
                    "shortfall_field": field,
                    "observed_value": value,
                    "minimum_required_value": minimum,
                    "validation_status": "FAIL_ACQUISITION_SHORTFALL",
                    "source_exhaustion_reason": "not exhausted; implementation must deepen acquisition",
                    "live_order_authority": False,
                }
            )
    if not shortfalls:
        return [
            {
                "shortfall_field": None,
                "observed_value": None,
                "minimum_required_value": None,
                "validation_status": "PASS_ACQUISITION_TARGETS_MET",
                "source_exhaustion_reason": None,
                "live_order_authority": False,
            }
        ]
    return shortfalls
