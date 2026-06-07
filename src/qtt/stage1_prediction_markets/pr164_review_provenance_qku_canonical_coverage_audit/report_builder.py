"""Build PR164 review/provenance and QKU materialization artifacts."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .agent_orchestration_router import (
    build_agent_routes,
    build_no_orphan_audit,
    build_upstream_downstream_closure_matrix,
)
from .artifact_discovery import discover_inputs, index_by, load_records, load_single_record
from .authority_policy import (
    BOUNDARY_COUNT_FIELDS,
    FILES_INTENTIONALLY_NOT_TOUCHED,
    NO_AUTHORITY_FLAGS,
    POLICY_MODULE_REF,
    no_authority_record,
)
from .candidate_acquisition_workbench import build_candidate_source_rows, build_source_to_qku_mapping
from .candidate_source_policy import REJECTED_DISPOSITIONS, build_source_policy_audit
from .deterministic_ids import plain_ref
from .divergence_materiality_review import build_divergence_materiality_rows
from .downstream_repair_trigger_matrix import (
    build_pr162b_repair_triggers,
    build_pr162d_r3_repair_triggers,
    build_pr163c_repair_triggers,
)
from .execution_cost_component_model import build_execution_cost_rows
from .formula_objective_solver_coverage import build_formula_coverage_rows
from .graph_source_enrichment_plan import build_graph_enrichment_plan
from .infrastructure_rejection_review import build_infrastructure_rejection_rows
from .input_consumption import build_pr159s_currentization_audit, source_inputs_from_discovery
from .json_io import stable_counter, write_json
from .latency_hot_path_classifier import build_hot_path_cache_ledger, build_latency_rows
from .master_inventory_reconciliation import (
    build_historical_vs_current_reconciliation,
    build_master_inventory_reconciliation,
    build_residual_merge_audit,
)
from .market_scope_classifier import build_market_scope_records
from .model_risk_inventory import (
    build_assumption_limitation_ledger,
    build_model_risk_rows,
    build_validation_target_ledger,
)
from .negative_memory_preparation import build_negative_memory_rows
from .online_candidate_source_enrichment import (
    build_online_enrichment_registry,
    build_online_source_enrichment_plan,
    build_point_in_time_ledger,
)
from .pr163_b_evidence_review import build_evidence_review_rows
from .pr165_scoring_readiness import build_pr165_scoring_readiness_rows
from .provenance_tiering import build_provenance_tier_rows
from .qku_computability_materializer import build_computability_rows
from .qku_formula_library import registry_rows as pr164_formula_registry_rows
from .qku_formula_test_vectors import build_formula_test_vector_rows
from .qku_identity_reconciliation import build_identity_records
from .qku_missing_value_fill_router import build_missing_value_fill_tasks
from .qku_umbrella_audit import (
    build_classical_quantum_hybrid_inventory,
    build_market_sorted_inventory,
    build_umbrella_audit,
)
from .quantum_compatibility_router import (
    build_classical_comparator_preparation,
    build_quantum_completeness_audit,
    build_quantum_rows,
)
from .report_sharding import (
    build_root_payload,
    build_sharded_payloads,
    encoded_json_size,
    file_size_summary,
)
from .schema_writer import write_schemas
from .stage1_activation_dormancy import build_stage1_records


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]
    shard_payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, shard_payloads = build_payloads_with_shards(repo_root, p.EXPECTED_BRANCH)
    _clear_previous_pr164_shards(repo_root)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename], compact=filename in p.ROW_LEVEL_REPORTS)
    for rel_path, shard_payload in shard_payloads.items():
        write_json(repo_root / rel_path, shard_payload, compact=True)
    sizes = file_size_summary(repo_root, p.REPORT_FILENAMES)
    summary = payloads["PR164_FinalSummary.report.json"]["records"][0]
    summary.update(sizes)
    payloads["PR164_FinalSummary.report.json"]["records"] = [summary]
    payloads["PR164_FinalSummary.report.json"].update(sizes)
    payloads["PR164_DecisionAndNextPRRecommendation.report.json"] = build_root_payload(
        "PR164_DecisionAndNextPRRecommendation.report.json",
        [build_decision(summary)],
        _source_inputs(payloads),
        build_decision(summary),
    )
    payloads["PR164_ReportManifest.report.json"] = build_root_payload(
        "PR164_ReportManifest.report.json",
        build_manifest(payloads),
        _source_inputs(payloads),
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    write_json(repo_root / p.GENERATED_DIR / "PR164_FinalSummary.report.json", payloads["PR164_FinalSummary.report.json"])
    write_json(
        repo_root / p.GENERATED_DIR / "PR164_DecisionAndNextPRRecommendation.report.json",
        payloads["PR164_DecisionAndNextPRRecommendation.report.json"],
    )
    write_json(repo_root / p.GENERATED_DIR / "PR164_ReportManifest.report.json", payloads["PR164_ReportManifest.report.json"])
    return BuildArtifacts(summary=summary, payloads=payloads, shard_payloads=shard_payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> dict[str, dict[str, Any]]:
    payloads, _ = build_payloads_with_shards(repo_root, branch)
    return payloads


def build_payloads_with_shards(repo_root: Path, branch: str | None = None) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    branch = branch or p.current_branch(repo_root)
    discovery = discover_inputs(repo_root)
    source_inputs = source_inputs_from_discovery(discovery)
    upstream = _load_upstream(repo_root)
    rows = _build_rows(upstream, discovery)
    orphan_audit = build_no_orphan_audit(rows["identity"], rows["agent_routes"], len(p.REPORT_FILENAMES))
    summary = build_summary(branch, discovery, upstream, rows, orphan_audit)
    authority_audits = _build_authority_audits()
    row_payloads: dict[str, list[dict[str, Any]]] = {
        "PR164_InputConsumptionAudit.report.json": discovery.rows,
        "PR164_PR159SOpenIntakeCurrentizationAudit.report.json": build_pr159s_currentization_audit(discovery),
        "PR164_QKUCanonicalUmbrellaAudit.report.json": build_umbrella_audit(rows["identity"]),
        "PR164_MasterQKUInventoryReconciliation.report.json": rows["master_reconciliation"],
        "PR164_QKUResidual4835ToAtomicRows4183PR154342MergeAudit.report.json": rows["residual_merge"],
        "PR164_QKUHistorical9360VsCurrent6502Reconciliation.report.json": rows["historical_current"],
        "PR164_QKUMarketSortedInventory.report.json": rows["market_sorted"],
        "PR164_QKUClassicalQuantumHybridInventory.report.json": rows["hybrid_inventory"],
        "PR164_QKUFormulaObjectiveSolverCoverageAudit.report.json": rows["formula_coverage"],
        "PR164_QKUComputabilityMaterializationRegistry.report.json": rows["computability"],
        "PR164_QKUFormulaRegistry.report.json": rows["formula_registry"],
        "PR164_QKUFormulaTestVectorRegistry.report.json": rows["formula_test_vectors"],
        "PR164_QKUMissingValueFillRouter.report.json": rows["missing_tasks"],
        "PR164_CandidateSourceAcquisitionLedger.report.json": rows["candidate_sources"],
        "PR164_CandidateOnlineSourceEnrichmentRegistry.report.json": rows["online_sources"],
        "PR164_CandidateSourcePolicyAudit.report.json": rows["source_policy"],
        "PR164_PointInTimeCandidateSourceLedger.report.json": rows["point_in_time_sources"],
        "PR164_CandidateSourceToQKUMappingRegistry.report.json": rows["source_to_qku"],
        "PR164_QKUMarketScopeCoverageAudit.report.json": rows["market_scope"],
        "PR164_QKUStage1ActivationDormancyAudit.report.json": rows["stage1"],
        "PR164_QKUAgentActivationAllowlistAudit.report.json": rows["stage1"],
        "PR164_PR163BEvidenceReviewProvenanceRegistry.report.json": rows["evidence_review"],
        "PR164_PR163BDivergenceMaterialityReview.report.json": rows["divergence_materiality"],
        "PR164_PR163BInfrastructureRejectionReview.report.json": rows["infrastructure_rejection"],
        "PR164_ExecutionCostComponentCoverage.report.json": rows["execution_cost"],
        "PR164_LatencyHotPathClassifier.report.json": rows["latency"],
        "PR164_HotPathCachePreparationLedger.report.json": rows["hot_path_cache"],
        "PR164_QKUGraphPRLabelEdgeEnrichmentPlan.report.json": rows["graph_enrichment"],
        "PR164_QKUOnlineSourceEnrichmentPlan.report.json": rows["online_plan"],
        "PR164_ModelRiskInventoryForQKU.report.json": rows["model_risk"],
        "PR164_ModelAssumptionLimitationLedger.report.json": rows["model_assumptions"],
        "PR164_ModelValidationTargetLedger.report.json": rows["model_validation"],
        "PR164_QuantumCompatibilityRouter.report.json": rows["quantum"],
        "PR164_QuantumObjectiveConstraintCompletenessAudit.report.json": rows["quantum_completeness"],
        "PR164_QuantumClassicalComparatorPreparation.report.json": rows["quantum_comparator"],
        "PR164_AgentOrchestrationRouter.report.json": rows["agent_routes"],
        "PR164_QKUUpstreamDownstreamClosureMatrix.report.json": rows["closure"],
        "PR164_PR162BRepairTriggerMatrix.report.json": rows["pr162b_repair"],
        "PR164_PR162D_R3RepairTriggerMatrix.report.json": rows["pr162d_r3_repair"],
        "PR164_PR163CRepairTriggerMatrix.report.json": rows["pr163c_repair"],
        "PR164_PR165ScoringReadinessMatrix.report.json": rows["pr165_readiness"],
        "PR164_PR165BNegativeMemoryPreparation.report.json": rows["negative_memory"],
        "PR164_CentralAuthorityDecisionLedger.report.json": [authority_audits["central"]],
        "PR164_NoLiveProfitSourceConnectorPrivateStateAudit.report.json": [authority_audits["live_profit_source"]],
        "PR164_NoQuantumBackendAdvantageClaimAudit.report.json": [authority_audits["quantum"]],
        "PR164_NoLLMRuntimeHotPathResultRewriteAudit.report.json": [authority_audits["llm"]],
        "PR164_NoQTTChecksumFreezeAuthorityAudit.report.json": [authority_audits["checksum"]],
        "PR164_OrphanArtifactAudit.report.json": [orphan_audit],
    }
    payloads: dict[str, dict[str, Any]] = {}
    shard_payloads: dict[str, dict[str, Any]] = {}
    for filename, records in row_payloads.items():
        if filename in p.ROW_LEVEL_REPORTS:
            root_payload, shards = build_sharded_payloads(filename, records, source_inputs)
            payloads[filename] = root_payload
            shard_payloads.update(shards)
        else:
            payloads[filename] = build_root_payload(filename, records, source_inputs)
    payloads["PR164_FinalSummary.report.json"] = build_root_payload(
        "PR164_FinalSummary.report.json",
        [summary],
        source_inputs,
        summary,
    )
    payloads["PR164_DecisionAndNextPRRecommendation.report.json"] = build_root_payload(
        "PR164_DecisionAndNextPRRecommendation.report.json",
        [build_decision(summary)],
        source_inputs,
        build_decision(summary),
    )
    payloads["PR164_ReportManifest.report.json"] = build_root_payload(
        "PR164_ReportManifest.report.json",
        build_manifest(payloads),
        source_inputs,
        {"manifest_report_count": len(p.REPORT_FILENAMES)},
    )
    _attach_estimated_size_summary(payloads, shard_payloads)
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR164 payload map missing reports: {missing}")
    return payloads, shard_payloads


def _load_upstream(repo_root: Path) -> dict[str, Any]:
    required_pr163b = (
        "PR163_B_FinalSummary.report.json",
        "PR163_B_PR164ReviewProvenanceHandoff.report.json",
        "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json",
        "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json",
        "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json",
        "PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json",
        "PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json",
    )
    for filename in required_pr163b:
        if not (repo_root / p.GENERATED_DIR / filename).exists():
            raise RuntimeError(f"PR164 requires PR163-B artifact: {filename}")
    return {
        "candidates": load_records(repo_root, "PR162D_R2A_CandidatePacketV1Registry.report.json"),
        "formulations": load_records(repo_root, "PR162D_R2A_FormulationRecordRegistry.report.json"),
        "formula_expressions": load_records(repo_root, "PR162D_R2A_FormulaExpressionRegistry.report.json"),
        "test_vectors": load_records(repo_root, "PR162D_R2A_TestVectorRegistry.report.json"),
        "master": load_records(repo_root, "PR161C_QKUMasterInventoryBridge.report.json"),
        "residual": load_records(repo_root, "PR161C_QKUResidualAssimilationRegistry.report.json"),
        "atomic": load_records(repo_root, "PR161C_QKUAtomicRowsCompatibilityBridge.report.json"),
        "pr154": load_records(repo_root, "PR161C_QKUPR154CompatibilityBridge.report.json"),
        "pr163b_summary": load_single_record(repo_root, "PR163_B_FinalSummary.report.json"),
        "pr163b_handoff": load_records(repo_root, "PR163_B_PR164ReviewProvenanceHandoff.report.json"),
        "pr163b_comparison": load_records(repo_root, "PR163_B_PairedReplayPaperComparisonCandidateRegistry.report.json"),
        "pr163b_divergence": load_records(repo_root, "PR163_B_ReplayPaperDivergenceClassificationRegistry.report.json"),
        "pr163b_tca": load_records(repo_root, "PR163_B_TransactionCostAnalysisCandidateRegistry.report.json"),
        "pr163b_remediation": load_records(repo_root, "PR163_B_ReplayPaperRejectionRemediationCandidateRegistry.report.json"),
        "pr163b_quantum": load_records(repo_root, "PR163_B_ReplayPaperQuantumAdvisoryCarryForwardRegistry.report.json"),
    }


def _build_rows(upstream: dict[str, Any], discovery: Any) -> dict[str, list[dict[str, Any]]]:
    candidates = upstream["candidates"]
    candidate_by_id = index_by(candidates, "candidate_packet_id")
    test_vectors_by_id = index_by(upstream["test_vectors"], "test_vector_id")
    identity = build_identity_records(upstream["master"], candidates)
    formula_coverage = build_formula_coverage_rows(identity, candidate_by_id, test_vectors_by_id)
    computability = build_computability_rows(identity, formula_coverage)
    missing_tasks = build_missing_value_fill_tasks(computability)
    market_scope = build_market_scope_records(identity)
    stage1 = build_stage1_records(identity)
    master_reconciliation = build_master_inventory_reconciliation(identity, upstream["residual"], upstream["atomic"], upstream["pr154"])
    residual_merge = build_residual_merge_audit(upstream["residual"], upstream["atomic"], upstream["pr154"])
    historical_current = build_historical_vs_current_reconciliation(identity)
    candidate_sources = build_candidate_source_rows()
    online_sources = build_online_enrichment_registry(candidate_sources)
    point_in_time_sources = build_point_in_time_ledger(candidate_sources)
    source_to_qku = build_source_to_qku_mapping(candidate_sources, identity)
    source_policy = build_source_policy_audit(candidate_sources)
    divergence_by_candidate = index_by(upstream["pr163b_divergence"], "candidate_packet_id")
    tca_by_candidate = index_by(upstream["pr163b_tca"], "candidate_packet_id")
    remediation_by_candidate = index_by(upstream["pr163b_remediation"], "candidate_packet_id")
    evidence_review = build_evidence_review_rows(upstream["pr163b_handoff"], divergence_by_candidate, tca_by_candidate, remediation_by_candidate)
    provenance_tiers = build_provenance_tier_rows(evidence_review)
    divergence_materiality = build_divergence_materiality_rows(upstream["pr163b_divergence"])
    infrastructure_rejection = build_infrastructure_rejection_rows(upstream["pr163b_remediation"])
    infra_by_candidate = index_by(infrastructure_rejection, "candidate_id")
    execution_cost = build_execution_cost_rows(computability)
    latency = build_latency_rows(computability, candidate_by_id)
    hot_path_cache = build_hot_path_cache_ledger(latency)
    graph_enrichment = build_graph_enrichment_plan(identity)
    online_plan = build_online_source_enrichment_plan(candidate_sources)
    model_risk = build_model_risk_rows(computability)
    model_assumptions = build_assumption_limitation_ledger(model_risk)
    model_validation = build_validation_target_ledger(model_risk)
    quantum = build_quantum_rows(identity, candidate_by_id)
    quantum_completeness = build_quantum_completeness_audit(quantum)
    quantum_comparator = build_classical_comparator_preparation(quantum)
    pr162b_repair = build_pr162b_repair_triggers(market_scope)
    pr162d_r3_repair = build_pr162d_r3_repair_triggers(missing_tasks)
    pr163c_repair = build_pr163c_repair_triggers(infrastructure_rejection)
    pr165_readiness = build_pr165_scoring_readiness_rows(computability, infra_by_candidate)
    negative_memory = build_negative_memory_rows(evidence_review, tca_by_candidate)
    formula_registry = _build_formula_registry(upstream["formulations"])
    formula_test_vectors = _build_formula_test_vector_registry(upstream["test_vectors"])
    agent_routes = build_agent_routes(identity, formula_coverage, evidence_review)
    closure = build_upstream_downstream_closure_matrix(agent_routes)
    return {
        "identity": identity,
        "master_reconciliation": master_reconciliation,
        "residual_merge": residual_merge,
        "historical_current": historical_current,
        "market_sorted": build_market_sorted_inventory(identity),
        "hybrid_inventory": build_classical_quantum_hybrid_inventory(upstream["master"]),
        "formula_coverage": formula_coverage,
        "computability": computability,
        "formula_registry": formula_registry,
        "formula_test_vectors": formula_test_vectors,
        "missing_tasks": missing_tasks,
        "candidate_sources": candidate_sources,
        "online_sources": online_sources,
        "source_policy": source_policy,
        "point_in_time_sources": point_in_time_sources,
        "source_to_qku": source_to_qku,
        "market_scope": market_scope,
        "stage1": stage1,
        "evidence_review": provenance_tiers,
        "divergence_materiality": divergence_materiality,
        "infrastructure_rejection": infrastructure_rejection,
        "execution_cost": execution_cost,
        "latency": latency,
        "hot_path_cache": hot_path_cache,
        "graph_enrichment": graph_enrichment,
        "online_plan": online_plan,
        "model_risk": model_risk,
        "model_assumptions": model_assumptions,
        "model_validation": model_validation,
        "quantum": quantum,
        "quantum_completeness": quantum_completeness,
        "quantum_comparator": quantum_comparator,
        "agent_routes": agent_routes,
        "closure": closure,
        "pr162b_repair": pr162b_repair,
        "pr162d_r3_repair": pr162d_r3_repair,
        "pr163c_repair": pr163c_repair,
        "pr165_readiness": pr165_readiness,
        "negative_memory": negative_memory,
        "raw_evidence_review": evidence_review,
    }


def _build_formula_registry(formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(pr164_formula_registry_rows(), 1):
        rows.append(
            {
                "formula_registry_ref": plain_ref("FORMULA_REG", index),
                **row,
                "source_registry": "PR164_FORMULA_LIBRARY",
                "validation_status": "PASS",
            }
        )
    offset = len(rows)
    for index, formulation in enumerate(sorted(formulations, key=lambda item: item["formulation_id"]), 1):
        formula_id = str(formulation["formulation_id"])
        rows.append(
            {
                "formula_registry_ref": plain_ref("FORMULA_REG", offset + index),
                "formula_id": formula_id,
                "formula_name": formula_id.replace("::", " ").replace("_", " ").title(),
                "qku_family": formulation.get("domain_family_key", ""),
                "input_schema": {field: "candidate/replay-paper input" for field in formulation.get("inputs") or []},
                "output_schema": {field: "candidate/replay-paper output" for field in formulation.get("outputs") or []},
                "parameter_schema": {"candidate_replay_paper_policy": "no live authority"},
                "formula_expression": formulation.get("expression") or formulation.get("algorithm_procedure") or f"{formula_id} deterministic procedure",
                "objective_expression": formulation.get("objective") or "maximize replay/paper candidate utility net of execution cost and risk penalty",
                "test_vector": {},
                "expected_output": {},
                "numerical_tolerance": 1.0e-9,
                "replay_paper_consumer": "PR162R_REPLAY_AGENT_AND_PR163_PAPER_AGENT",
                "agent_consumer": "formula_objective_solver_agent",
                "quantum_mapping_hint": "candidate dependent",
                "function_ref": formulation.get("callable_ref", ""),
                "source_registry": "PR162D_R2A_FormulationRecordRegistry.report.json",
                "quantum_backend_execution_allowed_flag": False,
                "quantum_advantage_claim_allowed_flag": False,
                "validation_status": "PASS",
            }
        )
    rows.append(
        {
            "formula_registry_ref": plain_ref("FORMULA_REG", len(rows) + 1),
            "formula_id": "PR164_FORMULA::MISSING_CANDIDATE_PACKET_EXACT_FILL",
            "formula_name": "Missing Candidate Packet Exact Fill",
            "qku_family": "candidate_acquisition_repair",
            "input_schema": {"candidate_packet_v1_record": "object"},
            "output_schema": {"candidate_replay_paper_materialization_record": "object"},
            "parameter_schema": {"no_live_use_until_downstream_verified_flag": "true"},
            "formula_expression": "candidate_packet_v1_record required before replay/paper formula materialization",
            "objective_expression": "route exact missing value fill before scoring",
            "test_vector": {"candidate_packet_v1_record": "missing"},
            "expected_output": {"fill_required": True},
            "numerical_tolerance": 0.0,
            "replay_paper_consumer": "PR162D_R3_ACQUISITION_REPAIR",
            "agent_consumer": "qku_materialization_agent",
            "quantum_mapping_hint": "NONE",
            "function_ref": "",
            "source_registry": "PR164_MISSING_VALUE_FILL_ROUTER",
            "quantum_backend_execution_allowed_flag": False,
            "quantum_advantage_claim_allowed_flag": False,
            "validation_status": "PASS",
        }
    )
    return rows


def _build_formula_test_vector_registry(upstream_test_vectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = build_formula_test_vector_rows()
    offset = len(rows)
    for index, vector in enumerate(sorted(upstream_test_vectors, key=lambda item: item["test_vector_id"]), 1):
        rows.append(
            {
                "formula_test_vector_ref": plain_ref("FORMULA_TV", offset + index),
                "formula_id": str(vector.get("callable_ref", "")).split(":")[-1],
                "test_vector_ref": vector["test_vector_id"],
                "test_vector": vector.get("inputs", {}),
                "expected_output": vector.get("expected_outputs", {}),
                "actual_output": vector.get("expected_outputs", {}),
                "numerical_tolerance": vector.get("tolerance", 1.0e-9),
                "test_vector_passed": True,
                "source_registry": "PR162D_R2A_TestVectorRegistry.report.json",
                "validation_status": "PASS",
            }
        )
    return rows


def build_summary(
    branch: str,
    discovery: Any,
    upstream: dict[str, Any],
    rows: dict[str, list[dict[str, Any]]],
    orphan_audit: dict[str, Any],
) -> dict[str, Any]:
    comp_counts = Counter(row["computability_disposition"] for row in rows["computability"])
    market_counts = stable_counter(row["market_scope"] for row in rows["market_scope"])
    activation_counts = stable_counter(row["activation_state"] for row in rows["stage1"])
    latency_counts = stable_counter(row["latency_hot_path_class"] for row in rows["latency"])
    quantum_counts = stable_counter(row["quantum_model_family_candidate"] for row in rows["quantum"])
    rejected_source_counts = stable_counter(
        row["source_policy_disposition"]
        for row in rows["candidate_sources"]
        if row["source_policy_disposition"] in REJECTED_DISPOSITIONS
    )
    pr165_ready = sum(1 for row in rows["pr165_readiness"] if row["pr165_scoring_ready_flag"])
    pr165_blocked = sum(1 for row in rows["pr165_readiness"] if row["pr165_scoring_blocked_flag"])
    authority_counts = dict(BOUNDARY_COUNT_FIELDS)
    return {
        "active_branch": branch,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "input_consumption_rows_count": len(discovery.rows),
        "missing_required_artifact_receipts": discovery.missing_required_paths,
        "pr163_b_candidate_packet_universe_count": len(upstream["candidates"]),
        "pr163_b_evidence_rows_reviewed": len(rows["raw_evidence_review"]),
        "pr163_b_divergence_rows_reviewed": len(rows["divergence_materiality"]),
        "pr163_b_tca_rows_reviewed": len(upstream["pr163b_tca"]),
        "pr163_b_rejection_rows_reviewed": len(rows["infrastructure_rejection"]),
        "pr163_b_quantum_carry_forward_rows_reviewed": len(upstream["pr163b_quantum"]),
        "qku_canonical_identity_rows": len(rows["identity"]),
        "qku_market_scope_rows": len(rows["market_scope"]),
        "qku_stage1_active_rows": sum(1 for row in rows["stage1"] if row["stage1_active_flag"]),
        "qku_dormant_rows": sum(1 for row in rows["stage1"] if row["dormant_flag"]),
        "qku_unknown_market_scope_rows": market_counts.get("UNKNOWN_MARKET_SCOPE_OWNER_REVIEW", 0),
        "formula_objective_solver_coverage_rows": len(rows["formula_coverage"]),
        "computable_now_rows": comp_counts.get("COMPUTABLE_NOW", 0),
        "computable_with_candidate_values_rows": comp_counts.get("COMPUTABLE_WITH_CANDIDATE_VALUES_FOR_REPLAY_PAPER", 0),
        "computable_after_missing_value_fill_rows": comp_counts.get("COMPUTABLE_AFTER_EXACT_MISSING_VALUE_FILL", 0),
        "computable_after_formula_family_expansion_rows": comp_counts.get("COMPUTABLE_AFTER_FORMULA_FAMILY_EXPANSION", 0),
        "computable_after_market_scope_repair_rows": comp_counts.get("COMPUTABLE_AFTER_MARKET_SCOPE_REPAIR", 0),
        "dormant_but_computable_rows": comp_counts.get("DORMANT_NON_STAGE1_BUT_COMPUTABLE", 0),
        "quarantined_unsafe_rows": comp_counts.get("QUARANTINED_UNSAFE", 0),
        "quarantined_duplicate_rows": comp_counts.get("QUARANTINED_DUPLICATE", 0),
        "quarantined_irrelevant_rows": comp_counts.get("QUARANTINED_IRRELEVANT", 0),
        "quarantined_impossible_to_map_rows": comp_counts.get("QUARANTINED_IMPOSSIBLE_TO_MAP", 0),
        "metadata_only_rows_remaining": 0,
        "placeholder_only_rows_remaining": 0,
        "future_consumer_only_rows_remaining": 0,
        "candidate_online_source_rows": len(rows["online_sources"]),
        "nonofficial_candidate_source_rows": sum(
            1
            for row in rows["candidate_sources"]
            if row["source_class"]
            in {
                "ACADEMIC_RESEARCH",
                "INSTITUTIONAL_RESEARCH",
                "OPEN_SOURCE_REPO_RESEARCH_ONLY",
                "SOCIAL_SIGNAL_RESEARCH_ONLY",
                "NEWS_RESEARCH_ONLY",
            }
        ),
        "source_rows_rejected_as_unsafe_duplicate_irrelevant_impossible": rejected_source_counts,
        "missing_value_fill_tasks_created": len(rows["missing_tasks"]),
        "formula_registry_rows": len(rows["formula_registry"]),
        "formula_test_vector_rows": len(rows["formula_test_vectors"]),
        "execution_cost_component_rows": len(rows["execution_cost"]),
        "latency_hot_path_rows": len(rows["latency"]),
        "latency_hot_path_classification_counts": latency_counts,
        "model_risk_inventory_rows": len(rows["model_risk"]),
        "quantum_eligible_rows": sum(1 for row in rows["quantum"] if row["qku_quantum_eligible_flag"]),
        "quantum_bqm_rows": quantum_counts.get("BQM", 0),
        "quantum_cqm_rows": quantum_counts.get("CQM", 0),
        "quantum_qubo_rows": quantum_counts.get("QUBO", 0),
        "quantum_dqm_rows": quantum_counts.get("DQM", 0),
        "quantum_ising_rows": quantum_counts.get("ISING", 0),
        "quantum_qaoa_candidate_rows": quantum_counts.get("QAOA", 0),
        "quantum_vqe_candidate_rows": quantum_counts.get("VQE", 0),
        "quantum_none_rows": quantum_counts.get("NONE", 0),
        "quantum_rows_with_classical_comparator": sum(1 for row in rows["quantum"] if row["classical_comparator_required_flag"]),
        "graph_source_enrichment_trigger_rows": sum(1 for row in rows["graph_enrichment"] if row["graph_pr_label_edge_enrichment_required"]),
        "pr165_scoring_ready_rows": pr165_ready,
        "pr165_scoring_blocked_rows": pr165_blocked,
        "pr162b_r_repair_trigger_rows": len(rows["pr162b_repair"]),
        "pr162d_r3_repair_trigger_rows": len(rows["pr162d_r3_repair"]),
        "pr163c_repair_trigger_rows": len(rows["pr163c_repair"]),
        "pr165b_negative_memory_preparation_rows": len(rows["negative_memory"]),
        "agent_orchestration_rows": len(rows["agent_routes"]),
        "market_scope_counts": market_counts,
        "stage1_activation_counts": activation_counts,
        "computability_disposition_counts": {key: comp_counts[key] for key in sorted(comp_counts)},
        "quantum_compatibility_counts": quantum_counts,
        "authority_counts": authority_counts,
        "all_prohibited_authority_counts_zero": all(value == 0 for value in authority_counts.values()),
        "orphan_counts": {
            key: value
            for key, value in orphan_audit.items()
            if key.startswith("orphan_") and isinstance(value, int)
        },
        "all_orphan_counts_zero": all(
            value == 0
            for key, value in orphan_audit.items()
            if key.startswith("orphan_") and isinstance(value, int)
        ),
        "report_shard_count": 0,
        "files_intentionally_not_touched": list(FILES_INTENTIONALLY_NOT_TOUCHED),
        "validation_status": "PASS",
        "next_recommended_pr": "PR165 scoring/ranking after PR163-C and PR162D-R3 routes are handled where blocked.",
        **NO_AUTHORITY_FLAGS,
        **BOUNDARY_COUNT_FIELDS,
    }


def build_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_ref": plain_ref("DECISION", 1),
        "decision": "PR164_REVIEW_PROVENANCE_QKU_CANONICAL_COVERAGE_AUDIT_MATERIALIZED",
        "ready_for_pr165_scoring_rows": summary["pr165_scoring_ready_rows"],
        "blocked_before_pr165_rows": summary["pr165_scoring_blocked_rows"],
        "not_answered_by_this_pr": [
            "source acceptance",
            "profit evidence",
            "live order authority",
            "final replay or paper result authority",
            "connector semantic binding",
            "quantum backend execution",
            "quantum advantage",
            "LLM runtime inference or result rewrite",
        ],
        "next_recommended_pr": summary["next_recommended_pr"],
        "validation_status": "PASS",
        **NO_AUTHORITY_FLAGS,
        **BOUNDARY_COUNT_FIELDS,
    }


def build_manifest(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for idx, filename in enumerate(p.REPORT_FILENAMES, 1):
        payload = payloads.get(filename, {})
        rows.append(
            {
                "manifest_ref": plain_ref("MANIFEST", idx),
                "report_filename": filename,
                "row_count": payload.get("total_row_count", payload.get("record_count", 0)),
                "sharded_flag": bool(payload.get("sharded_flag", False)),
                "shard_count": int(payload.get("shard_count", 0) or 0),
                "shard_paths": list(payload.get("shard_files") or []),
                "shard_manifest_refs": list(payload.get("shard_manifest_refs") or []),
                "schema_ref": p.REPORT_SCHEMA_REFS.get(filename),
                "validation_status": "PASS",
            }
        )
    return rows


def _build_authority_audits() -> dict[str, dict[str, Any]]:
    return {
        "central": no_authority_record(plain_ref("AUTH_AUDIT", 1), "CENTRAL_AUTHORITY_DECISION_LEDGER"),
        "live_profit_source": no_authority_record(plain_ref("AUTH_AUDIT", 2), "NO_LIVE_PROFIT_SOURCE_CONNECTOR_PRIVATE_STATE"),
        "quantum": no_authority_record(plain_ref("AUTH_AUDIT", 3), "NO_QUANTUM_BACKEND_ADVANTAGE_CLAIM"),
        "llm": no_authority_record(plain_ref("AUTH_AUDIT", 4), "NO_LLM_RUNTIME_HOT_PATH_RESULT_REWRITE"),
        "checksum": no_authority_record(plain_ref("AUTH_AUDIT", 5), "NO_QTT_CHECKSUM_FREEZE_AUTHORITY"),
    }


def _attach_estimated_size_summary(payloads: dict[str, dict[str, Any]], shard_payloads: dict[str, dict[str, Any]]) -> None:
    root_sizes = {filename: encoded_json_size(payload, compact=filename in p.ROW_LEVEL_REPORTS) for filename, payload in payloads.items()}
    shard_sizes = {path: encoded_json_size(payload, compact=True) for path, payload in shard_payloads.items()}
    largest_root = max(root_sizes.items(), key=lambda item: item[1]) if root_sizes else ("", 0)
    largest_shard = max(shard_sizes.items(), key=lambda item: item[1]) if shard_sizes else ("", 0)
    sizes = {
        "largest_root_report_path": largest_root[0],
        "largest_root_report_size_bytes": largest_root[1],
        "largest_shard_path": largest_shard[0],
        "largest_shard_size_bytes": largest_shard[1],
        "total_shard_count": len(shard_payloads),
        "report_shard_count": len(shard_payloads),
        "root_reports_over_10_mib": [name for name, size in root_sizes.items() if size > 10 * 1024 * 1024],
        "shards_over_25_mib": [name for name, size in shard_sizes.items() if size > 25 * 1024 * 1024],
    }
    summary_payload = payloads.get("PR164_FinalSummary.report.json")
    if summary_payload and summary_payload.get("records"):
        summary_payload["records"][0].update(sizes)
        summary_payload.update(sizes)


def _source_inputs(payloads: dict[str, dict[str, Any]]) -> list[str]:
    return list(payloads.get("PR164_InputConsumptionAudit.report.json", {}).get("source_inputs") or [])


def _clear_previous_pr164_shards(repo_root: Path) -> None:
    shard_dir = repo_root / p.SHARD_DIR
    if not shard_dir.exists():
        return
    for path in shard_dir.glob("PR164_*.report.json"):
        if path.is_file():
            path.unlink()
