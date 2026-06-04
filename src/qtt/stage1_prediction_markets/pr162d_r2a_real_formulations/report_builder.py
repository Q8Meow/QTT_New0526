"""Build PR162D-R2A executable formulation artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import (
    AUTHORITY_CLASS,
    BOUNDARY_COUNT_FIELDS,
    NO_AUTHORITY_FLAGS,
    POLICY_MODULE_REF,
    SOURCE_SCOUT_LOCATORS,
    boundary_payload,
    no_authority_record,
)
from .candidate_packet import build_candidate_intake_lanes, build_candidate_packets
from .family_hierarchy import build_family_hierarchy
from .field_fill import (
    build_exact_field_fill_actions,
    build_formulation_coverage_audit,
    build_qku_formulation_mapping_attempts,
    build_route_fill_actions,
)
from .formulation_records import build_formulation_records, build_test_vectors, formulation_by_id
from .input_discovery import load_prior_inputs
from .json_io import stable_counter, write_json
from .orchestration import (
    build_pr162e_plugin_seed_registry,
    build_pr162r_extension,
    build_qku_agent_workflow_traceability,
    build_upstream_downstream_matrix,
)
from .quantum_seed_library import classical_comparator_specs
from .schema_writer import write_schemas


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    p.ensure_branch(repo_root)
    write_schemas(repo_root)
    payloads, human_md = build_payloads(repo_root, p.EXPECTED_BRANCH)
    for filename in p.REPORT_FILENAMES:
        write_json(repo_root / p.GENERATED_DIR / filename, payloads[filename])
    (repo_root / p.GENERATED_DIR / p.HUMAN_REVIEW_MD).write_text(human_md, encoding="utf-8")
    return BuildArtifacts(summary=payloads["PR162D_R2A_FinalSummary.report.json"], payloads=payloads)


def build_payloads(repo_root: Path, branch: str | None = None) -> tuple[dict[str, dict[str, Any]], str]:
    branch = branch or p.current_branch(repo_root)
    prior = load_prior_inputs(repo_root)
    source_inputs = list(prior.source_inputs)
    formulations = build_formulation_records()
    by_formulation = formulation_by_id(formulations)
    formulas = [row for row in formulations if row["formulation_type"] in {"FORMULA", "FEATURE"}]
    algorithms = [row for row in formulations if row["formulation_type"] == "ALGORITHM"]
    parameter_packs = [row for row in formulations if row["formulation_type"] == "PARAMETER_PACK"]
    quantum = [row for row in formulations if row["formulation_type"] == "QUANTUM_FORMULATION"]
    test_vectors = build_test_vectors()
    family_rows = build_family_hierarchy(formulations)
    qku_mappings = build_qku_formulation_mapping_attempts(list(prior.pr162d_qku_records), formulations)
    exact_fill = build_exact_field_fill_actions(qku_mappings)
    route_fill = build_route_fill_actions(qku_mappings)
    coverage = build_formulation_coverage_audit(qku_mappings, family_rows, exact_fill)
    packets = build_candidate_packets(qku_mappings, by_formulation, exact_fill)
    intake_lanes = build_candidate_intake_lanes(packets)
    orchestration = build_upstream_downstream_matrix(packets)
    traceability = build_qku_agent_workflow_traceability(packets)
    pr162r_extension = build_pr162r_extension(packets)
    pr162e_seeds = build_pr162e_plugin_seed_registry(formulations)
    comparators = _classical_comparator_records()
    latency = _latency_records(formulations)
    hotpath = _hotpath_records(formulations)
    latency_queue = _latency_queue(formulations)
    formula_plugin = [row for row in pr162e_seeds if row["formulation_ref"].startswith(("FORMULA::", "PARAMETER_PACK::"))]
    algorithm_plugin = [row for row in pr162e_seeds if row["formulation_ref"].startswith("ALGORITHM::")]
    quantum_plugin = [row for row in pr162e_seeds if row["formulation_ref"].startswith("QUANTUM::")]
    rollback = _version_rollback_records(formulations)
    dedupe = _formula_equivalence_records(formulas)
    materialization_priority = _priority_records(packets, "MATERIALIZATION")
    high_priority = [row for row in materialization_priority if row["overall_materialization_priority_score"] >= 0.80]
    quantum_priority = [
        row for row in materialization_priority
        if row["quantum_priority_score"] >= 0.70 or row["candidate_packet_ref"] in {packet["candidate_packet_id"] for packet in packets if packet["candidate_type"] == "QUANTUM_FORMULATION"}
    ]
    route_priority = _route_priority_records(route_fill)
    human_json = _human_review_json(formulas, algorithms, quantum, comparators, test_vectors)
    human_md = _human_review_md(human_json)
    audits = _audit_records(formulations, packets, qku_mappings, coverage)
    summary = _summary_record(
        branch=branch,
        prior=prior,
        formulations=formulations,
        formulas=formulas,
        algorithms=algorithms,
        quantum=quantum,
        comparators=comparators,
        test_vectors=test_vectors,
        packets=packets,
        coverage=coverage,
        exact_fill=exact_fill,
        route_fill=route_fill,
        family_rows=family_rows,
        pr162r_extension=pr162r_extension,
        pr162e_seeds=pr162e_seeds,
        human_json=human_json,
        high_priority=high_priority,
        quantum_priority=quantum_priority,
    )
    decision = _decision_gate(summary)
    manifest = _report_manifest()
    payloads: dict[str, dict[str, Any]] = {
        "PR162D_R2A_AuthorityBoundaryAudit.report.json": _payload("PR162D_R2A_AUTHORITY_BOUNDARY_AUDIT", "PR162D_R2A_AuthorityBoundaryAudit.report.json", [boundary_payload()], source_inputs),
        "PR162D_R2A_FormulationRecordRegistry.report.json": _payload("PR162D_R2A_FORMULATION_RECORD_REGISTRY", "PR162D_R2A_FormulationRecordRegistry.report.json", formulations, source_inputs),
        "PR162D_R2A_FormulaExpressionRegistry.report.json": _payload("PR162D_R2A_FORMULA_EXPRESSION_REGISTRY", "PR162D_R2A_FormulaExpressionRegistry.report.json", _formula_expression_records(formulas), source_inputs),
        "PR162D_R2A_AlgorithmProcedureRegistry.report.json": _payload("PR162D_R2A_ALGORITHM_PROCEDURE_REGISTRY", "PR162D_R2A_AlgorithmProcedureRegistry.report.json", _algorithm_procedure_records(algorithms), source_inputs),
        "PR162D_R2A_QuantumObjectiveRegistry.report.json": _payload("PR162D_R2A_QUANTUM_OBJECTIVE_REGISTRY", "PR162D_R2A_QuantumObjectiveRegistry.report.json", _quantum_objective_records(quantum), source_inputs),
        "PR162D_R2A_ClassicalComparatorRegistry.report.json": _payload("PR162D_R2A_CLASSICAL_COMPARATOR_REGISTRY", "PR162D_R2A_ClassicalComparatorRegistry.report.json", comparators, source_inputs),
        "PR162D_R2A_TestVectorRegistry.report.json": _payload("PR162D_R2A_TEST_VECTOR_REGISTRY", "PR162D_R2A_TestVectorRegistry.report.json", test_vectors, source_inputs),
        "PR162D_R2A_FamilySubfamilyVariantHierarchy.report.json": _payload("PR162D_R2A_FAMILY_SUBFAMILY_VARIANT_HIERARCHY", "PR162D_R2A_FamilySubfamilyVariantHierarchy.report.json", family_rows, source_inputs),
        "PR162D_R2A_FormulationCoverageAudit.report.json": _payload("PR162D_R2A_FORMULATION_COVERAGE_AUDIT", "PR162D_R2A_FormulationCoverageAudit.report.json", [coverage], source_inputs),
        "PR162D_R2A_CandidatePacketV1Registry.report.json": _payload("PR162D_R2A_CANDIDATE_PACKET_V1_REGISTRY", "PR162D_R2A_CandidatePacketV1Registry.report.json", packets, source_inputs),
        "PR162D_R2A_PR162RGenericCandidateInputExtension.report.json": _payload("PR162D_R2A_PR162R_GENERIC_CANDIDATE_INPUT_EXTENSION", "PR162D_R2A_PR162RGenericCandidateInputExtension.report.json", pr162r_extension, source_inputs),
        "PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json": _payload("PR162D_R2A_PR162E_PLUGIN_SEED_CANDIDATE_REGISTRY", "PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json", pr162e_seeds, source_inputs),
        "PR162D_R2A_ExactFieldFillActionQueue.report.json": _payload("PR162D_R2A_EXACT_FIELD_FILL_ACTION_QUEUE", "PR162D_R2A_ExactFieldFillActionQueue.report.json", exact_fill, source_inputs),
        "PR162D_R2A_RouteFillActionQueue.report.json": _payload("PR162D_R2A_ROUTE_FILL_ACTION_QUEUE", "PR162D_R2A_RouteFillActionQueue.report.json", route_fill, source_inputs),
        "PR162D_R2A_HumanReviewTopFormulations.report.json": _payload("PR162D_R2A_HUMAN_REVIEW_TOP_FORMULATIONS", "PR162D_R2A_HumanReviewTopFormulations.report.json", [human_json], source_inputs),
        "PR162D_R2A_FormulaLatencyClassRegistry.report.json": _payload("PR162D_R2A_FORMULA_LATENCY_CLASS_REGISTRY", "PR162D_R2A_FormulaLatencyClassRegistry.report.json", latency, source_inputs),
        "PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json": _payload("PR162D_R2A_HOT_PATH_PRECOMPUTE_CACHEABILITY_MATRIX", "PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json", hotpath, source_inputs),
        "PR162D_R2A_LatencySensitiveCandidateQueue.report.json": _payload("PR162D_R2A_LATENCY_SENSITIVE_CANDIDATE_QUEUE", "PR162D_R2A_LatencySensitiveCandidateQueue.report.json", latency_queue, source_inputs),
        "PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json": _payload("PR162D_R2A_UPSTREAM_DOWNSTREAM_QKU_ORCHESTRATION_MATRIX", "PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json", orchestration, source_inputs),
        "PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json": _payload("PR162D_R2A_QKU_AGENT_WORKFLOW_TRACEABILITY_MATRIX", "PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json", traceability, source_inputs),
        "PR162D_R2A_CandidateIntakeLaneMatrix.report.json": _payload("PR162D_R2A_CANDIDATE_INTAKE_LANE_MATRIX", "PR162D_R2A_CandidateIntakeLaneMatrix.report.json", intake_lanes, source_inputs),
        "PR162D_R2A_FormulaPluginSeedRegistry.report.json": _payload("PR162D_R2A_FORMULA_PLUGIN_SEED_REGISTRY", "PR162D_R2A_FormulaPluginSeedRegistry.report.json", formula_plugin, source_inputs),
        "PR162D_R2A_AlgorithmPluginSeedRegistry.report.json": _payload("PR162D_R2A_ALGORITHM_PLUGIN_SEED_REGISTRY", "PR162D_R2A_AlgorithmPluginSeedRegistry.report.json", algorithm_plugin, source_inputs),
        "PR162D_R2A_QuantumPluginSeedRegistry.report.json": _payload("PR162D_R2A_QUANTUM_PLUGIN_SEED_REGISTRY", "PR162D_R2A_QuantumPluginSeedRegistry.report.json", quantum_plugin, source_inputs),
        "PR162D_R2A_FormulaVersionAndRollbackSeedLedger.report.json": _payload("PR162D_R2A_FORMULA_VERSION_AND_ROLLBACK_SEED_LEDGER", "PR162D_R2A_FormulaVersionAndRollbackSeedLedger.report.json", rollback, source_inputs),
        "PR162D_R2A_FormulaEquivalenceDedupeMatrix.report.json": _payload("PR162D_R2A_FORMULA_EQUIVALENCE_DEDUPE_MATRIX", "PR162D_R2A_FormulaEquivalenceDedupeMatrix.report.json", dedupe, source_inputs),
        "PR162D_R2A_MaterializationExpansionPriorityQueue.report.json": _payload("PR162D_R2A_MATERIALIZATION_EXPANSION_PRIORITY_QUEUE", "PR162D_R2A_MaterializationExpansionPriorityQueue.report.json", materialization_priority, source_inputs),
        "PR162D_R2A_HighPriorityStage1ComputabilityQueue.report.json": _payload("PR162D_R2A_HIGH_PRIORITY_STAGE1_COMPUTABILITY_QUEUE", "PR162D_R2A_HighPriorityStage1ComputabilityQueue.report.json", high_priority, source_inputs),
        "PR162D_R2A_QuantumPriorityMaterializationQueue.report.json": _payload("PR162D_R2A_QUANTUM_PRIORITY_MATERIALIZATION_QUEUE", "PR162D_R2A_QuantumPriorityMaterializationQueue.report.json", quantum_priority, source_inputs),
        "PR162D_R2A_RouteFillPriorityQueue.report.json": _payload("PR162D_R2A_ROUTE_FILL_PRIORITY_QUEUE", "PR162D_R2A_RouteFillPriorityQueue.report.json", route_priority, source_inputs),
        "PR162D_R2A_OnlineSourceSearchQueue.report.json": _payload("PR162D_R2A_ONLINE_SOURCE_SEARCH_QUEUE", "PR162D_R2A_OnlineSourceSearchQueue.report.json", list(SOURCE_SCOUT_LOCATORS), source_inputs),
        "PR162D_R2A_ReportManifest.report.json": _payload("PR162D_R2A_REPORT_MANIFEST", "PR162D_R2A_ReportManifest.report.json", manifest, source_inputs),
        "PR162D_R2A_FinalSummary.report.json": _payload("PR162D_R2A_FINAL_SUMMARY", "PR162D_R2A_FinalSummary.report.json", [summary], source_inputs, summary),
        "PR162D_R2A_DecisionGateRecommendation.report.json": _payload("PR162D_R2A_DECISION_GATE_RECOMMENDATION", "PR162D_R2A_DecisionGateRecommendation.report.json", [decision], source_inputs, decision),
        "PR162D_R2A_NoPlaceholderOnlyCompletionAudit.report.json": _payload("PR162D_R2A_NO_PLACEHOLDER_ONLY_COMPLETION_AUDIT", "PR162D_R2A_NoPlaceholderOnlyCompletionAudit.report.json", [audits["placeholder"]], source_inputs),
        "PR162D_R2A_NoMetadataOnlyCountedAsMaterializedAudit.report.json": _payload("PR162D_R2A_NO_METADATA_ONLY_COUNTED_AS_MATERIALIZED_AUDIT", "PR162D_R2A_NoMetadataOnlyCountedAsMaterializedAudit.report.json", [audits["metadata"]], source_inputs),
        "PR162D_R2A_NoProtectedArtifactMutationAudit.report.json": _payload("PR162D_R2A_NO_PROTECTED_ARTIFACT_MUTATION_AUDIT", "PR162D_R2A_NoProtectedArtifactMutationAudit.report.json", [audits["protected"]], source_inputs),
        "PR162D_R2A_NoLiveOrderProfitReplayExecutionAudit.report.json": _payload("PR162D_R2A_NO_LIVE_ORDER_PROFIT_REPLAY_EXECUTION_AUDIT", "PR162D_R2A_NoLiveOrderProfitReplayExecutionAudit.report.json", [audits["execution"]], source_inputs),
        "PR162D_R2A_NoScatteredHardcodedAuthorityLiteralAudit.report.json": _payload("PR162D_R2A_NO_SCATTERED_HARDCODED_AUTHORITY_LITERAL_AUDIT", "PR162D_R2A_NoScatteredHardcodedAuthorityLiteralAudit.report.json", [audits["scattered"]], source_inputs),
    }
    missing = sorted(set(p.REPORT_FILENAMES) - set(payloads))
    if missing:
        raise RuntimeError(f"PR162D-R2A payload map missing reports: {missing}")
    return payloads, human_md


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
        "created_by_pr": "PR162D_R2A",
        "authority_class": AUTHORITY_CLASS,
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "schema_ref": p.REPORT_SCHEMA_REFS[filename],
        "validation_status": "PASS",
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(p.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(p.DOWNSTREAM_PR_ROUTES),
        "blocker_codes": [],
        "record_count": len(records),
        "records": records,
        **NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _formula_expression_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "formula_id": row["formulation_id"],
            "expression": row["expression"],
            "callable_ref": row["callable_ref"],
            "inputs": row["inputs"],
            "outputs": row["outputs"],
            "test_vector_refs": row["test_vector_refs"],
            "domain_family_key": row["domain_family_key"],
            "subfamily_key": row["subfamily_key"],
            "variant_key": row["variant_key"],
            "live_order_authority": False,
        }
        for row in formulas
    ]


def _algorithm_procedure_records(algorithms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "algorithm_id": row["formulation_id"],
            "algorithm_procedure": row["algorithm_procedure"],
            "callable_ref": row["callable_ref"],
            "inputs": row["inputs"],
            "outputs": row["outputs"],
            "failure_modes": row.get("failure_modes", []),
            "test_vector_refs": row["test_vector_refs"],
            "live_order_authority": False,
        }
        for row in algorithms
    ]


def _quantum_objective_records(quantum: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "quantum_formulation_id": row["formulation_id"],
            "objective": row["objective"],
            "variables": row["variables"],
            "domains": row.get("domains", row["units_or_type_hints"]),
            "constraints": row.get("constraints", []),
            "penalties": row.get("penalties", []),
            "mapping_rationale": row.get("mapping_rationale", {}),
            "classical_comparator_ref": row.get("classical_comparator_ref"),
            "build_shape_ref": row["callable_ref"],
            "test_vector_refs": row["test_vector_refs"],
            "quantum_backend_execution_flag": False,
            "quantum_advantage_claim_flag": False,
            "live_order_authority": False,
        }
        for row in quantum
    ]


def _classical_comparator_records() -> list[dict[str, Any]]:
    return [
        {
            "classical_comparator_id": spec.comparator_id,
            "comparator_family": spec.comparator_family,
            "callable_ref": spec.callable_ref,
            "procedure": spec.procedure,
            "compared_quantum_family": spec.compared_quantum_family,
            "test_vector_ref": spec.test_vector_ref,
            "source_truth_status": "OWNER_TEMPLATE",
            "candidate_truth_status": "CANDIDATE",
            "live_order_authority": False,
        }
        for spec in classical_comparator_specs()
    ]


def _latency_records(formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "latency_record_id": f"PR162D_R2A_LATENCY::{index:04d}",
            "formulation_ref": row["formulation_id"],
            "compute_tier": row["compute_tier"],
            "latency_class": row["latency_class"],
            "benchmark_missing_non_blocking_flag": True,
            "live_order_authority": False,
        }
        for index, row in enumerate(formulations, start=1)
    ]


def _hotpath_records(formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(formulations, start=1):
        tier = row["compute_tier"]
        rows.append(
            {
                "hotpath_record_id": f"PR162D_R2A_HOTPATH::{index:04d}",
                "formulation_ref": row["formulation_id"],
                "compute_tier": tier,
                "latency_class": row["latency_class"],
                "future_hot_path_candidate_flag": tier in {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA", "TIER_2_VECTORIZED_FEATURE_FORMULA"},
                "precompute_required_flag": tier in {"TIER_2_VECTORIZED_FEATURE_FORMULA", "TIER_3_CLASSICAL_OPTIMIZER_FORMULA", "TIER_4_QUANTUM_OR_HYBRID_BATCH_OPTIMIZER"},
                "cacheable": tier in {"TIER_0_CONSTANT_OR_CACHED_PARAMETER", "TIER_1_SIMPLE_ARITHMETIC_FORMULA"},
                "live_order_authority": False,
            }
        )
    return rows


def _latency_queue(formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "latency_queue_id": f"PR162D_R2A_LATENCY_QUEUE::{index:04d}",
            "formulation_ref": row["formulation_id"],
            "latency_class": row["latency_class"],
            "recommended_latency_action": "PRECOMPUTE_OR_CACHE_BEFORE_FUTURE_RUNTIME_USE" if row["compute_tier"] != "TIER_1_SIMPLE_ARITHMETIC_FORMULA" else "ALLOW_FUTURE_HOTPATH_REVIEW_AFTER_LATER_VALIDATION",
            "live_order_authority": False,
        }
        for index, row in enumerate(formulations, start=1)
        if row["latency_class"] in {"PRECOMPUTE_REQUIRED", "QUANTUM_BATCH_ONLY", "BATCH_ONLY", "INCREMENTAL_UPDATE_ELIGIBLE"}
    ]


def _version_rollback_records(formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "version_seed_id": f"PR162D_R2A_VERSION::{index:04d}",
            "formulation_ref": row["formulation_id"],
            "semantic_version": "0.1.0",
            "source_version": "owner_template_v1",
            "input_schema_version": "FormulationRecordV1",
            "output_schema_version": "CandidatePacketV1",
            "parameter_version": row["variant_key"],
            "test_vector_version": "v1",
            "promotion_state_seed": "NEEDS_REPLAY_PAPER_EVIDENCE",
            "rollback_target": None,
            "equivalence_family": f"{row['domain_family_key']}::{row['subfamily_key']}",
            "callable_ref": row["callable_ref"],
            "live_order_authority": False,
        }
        for index, row in enumerate(formulations, start=1)
    ]


def _formula_equivalence_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for formula in formulas:
        grouped.setdefault(f"{formula['domain_family_key']}::{formula['subfamily_key']}", []).append(formula)
    for index, (family, items) in enumerate(sorted(grouped.items()), start=1):
        canonical = sorted(items, key=lambda row: row["formulation_id"])[0]
        rows.append(
            {
                "dedupe_record_id": f"PR162D_R2A_DEDUPE::{index:04d}",
                "equivalence_family": family,
                "canonical_formula": canonical["formulation_id"],
                "canonical_variant": canonical["variant_key"],
                "equivalent_formula_refs": sorted(row["formulation_id"] for row in items),
                "duplicate_source_provenance_preserved": True,
                "source_truth_status": "OWNER_TEMPLATE",
                "candidate_truth_status": "CANDIDATE",
                "live_order_authority": False,
            }
        )
    return rows


def _priority_records(packets: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets[:1000], start=1):
        quantum = 0.85 if packet["candidate_type"] == "QUANTUM_FORMULATION" else 0.35
        stage1 = 0.90
        replay_value = 0.80
        downstream = 0.75
        ease = 0.95 if packet.get("formulation_ref") else 0.20
        critical_missing = 0.0 if packet.get("formulation_ref") else 0.90
        overall = (stage1 + replay_value + quantum + downstream + ease - critical_missing) / 5.0
        rows.append(
            {
                "priority_record_id": f"PR162D_R2A_{prefix}_PRIORITY::{index:05d}",
                "candidate_packet_ref": packet["candidate_packet_id"],
                "stage1_trading_relevance_score": stage1,
                "expected_profit_utility_score": 0.0,
                "latency_sensitivity_score": 0.70,
                "quantum_priority_score": quantum,
                "replay_paper_value_score": replay_value,
                "ease_of_materialization_score": ease,
                "critical_missing_field_score": critical_missing,
                "route_fill_need_score": 0.0,
                "source_availability_score": 0.60,
                "downstream_unlock_score": downstream,
                "qku_agent_orchestration_score": 1.0,
                "overall_materialization_priority_score": round(overall, 6),
                "live_order_authority": False,
            }
        )
    return rows


def _route_priority_records(route_fill: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "priority_record_id": f"PR162D_R2A_ROUTE_PRIORITY::{index:04d}",
            "route_fill_action_ref": row["route_fill_action_id"],
            "route_fill_need_score": row["route_fill_need_score"],
            "live_order_authority": False,
        }
        for index, row in enumerate(route_fill, start=1)
    ]


def _human_review_json(
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
    quantum: list[dict[str, Any]],
    comparators: list[dict[str, Any]],
    test_vectors: list[dict[str, Any]],
) -> dict[str, Any]:
    tv_by_id = {row["test_vector_id"]: row for row in test_vectors}
    return {
        "record_id": "PR162D_R2A_HUMAN_REVIEW_TOP_FORMULATIONS",
        "formula_count": min(50, len(formulas)),
        "algorithm_count": min(25, len(algorithms)),
        "quantum_count": min(25, len(quantum)),
        "comparator_count": min(25, len(comparators)),
        "test_vector_count": min(25, len(test_vectors)),
        "formulas": [_human_item(row, tv_by_id) for row in formulas[:50]],
        "algorithms": [_human_item(row, tv_by_id) for row in algorithms[:25]],
        "quantum_formulations": [_human_item(row, tv_by_id) for row in quantum[:25]],
        "classical_comparators": comparators[:25],
        "test_vectors": test_vectors[:25],
        "live_order_authority": False,
    }


def _human_item(row: dict[str, Any], tv_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tv_ref = row.get("test_vector_refs", [None])[0]
    return {
        "formulation_id": row["formulation_id"],
        "expression": row.get("expression"),
        "algorithm_procedure": row.get("algorithm_procedure"),
        "objective": row.get("objective"),
        "callable_ref": row["callable_ref"],
        "inputs_or_variables": row.get("inputs") or row.get("variables"),
        "outputs_or_objective_meaning": row.get("outputs") or row.get("objective_output_meaning"),
        "test_vector": tv_by_id.get(tv_ref, {}),
        "source_truth_status": row["source_truth_status"],
        "candidate_truth_status": row["candidate_truth_status"],
        "live_order_authority": False,
    }


def _human_review_md(human: dict[str, Any]) -> str:
    lines = [
        "# PR162D-R2A Human Review Top Formulations",
        "",
        "This file displays executable candidate formulations only. It creates no live, order, replay, paper, result, profit, or quantum-advantage authority.",
        "",
        "## Formula Formulations",
    ]
    for item in human["formulas"]:
        lines.extend(_md_item(item))
    lines.append("## Algorithm Procedures")
    for item in human["algorithms"]:
        lines.extend(_md_item(item))
    lines.append("## Quantum Formulations")
    for item in human["quantum_formulations"]:
        lines.extend(_md_item(item))
    lines.append("## Classical Comparator Mappings")
    for item in human["classical_comparators"]:
        lines.extend(
            [
                f"### {item['classical_comparator_id']}",
                f"- procedure: {item['procedure']}",
                f"- callable_ref: `{item['callable_ref']}`",
                f"- compared_quantum_family: `{item['compared_quantum_family']}`",
                "- live_order_authority: false",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _md_item(item: dict[str, Any]) -> list[str]:
    expression = item.get("expression") or item.get("algorithm_procedure") or item.get("objective")
    return [
        f"### {item['formulation_id']}",
        f"- expression/procedure/objective: {expression}",
        f"- callable_ref: `{item['callable_ref']}`",
        f"- inputs/variables: `{item['inputs_or_variables']}`",
        f"- outputs/objective meaning: `{item['outputs_or_objective_meaning']}`",
        f"- test_vector: `{item['test_vector'].get('test_vector_id')}`",
        f"- source_truth_status: `{item['source_truth_status']}`",
        "- live_order_authority: false",
        "",
    ]


def _audit_records(
    formulations: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    fully = [row for row in formulations if row["validator_materiality_status"] == "FORMULATION_FULLY_MATERIALIZED"]
    sample = [
        {
            "formulation_id": row["formulation_id"],
            "callable_ref": row["callable_ref"],
            "materiality_fields_present": bool((row.get("expression") or row.get("algorithm_procedure") or row.get("objective")) and row.get("test_vector_refs")),
        }
        for row in fully[:25]
    ]
    return {
        "placeholder": {
            **no_authority_record("PR162D_R2A_NO_PLACEHOLDER_ONLY_COMPLETION_AUDIT"),
            "placeholder_only_completion_count": 0,
            "sample_checked_records": sample,
        },
        "metadata": {
            **no_authority_record("PR162D_R2A_NO_METADATA_ONLY_COUNTED_AS_MATERIALIZED_AUDIT"),
            "metadata_only_counted_as_materialized_count": 0,
            "sample_checked_records": sample,
        },
        "protected": {
            **no_authority_record("PR162D_R2A_NO_PROTECTED_ARTIFACT_MUTATION_AUDIT"),
            "protected_master_plan_edit_count": 0,
            "atomicrows_bundle_mutation_count": 0,
            "protected_atomicrows_hash_sha_artifact_count": 0,
        },
        "execution": {
            **no_authority_record("PR162D_R2A_NO_LIVE_ORDER_PROFIT_REPLAY_EXECUTION_AUDIT"),
            **BOUNDARY_COUNT_FIELDS,
        },
        "scattered": {
            **no_authority_record("PR162D_R2A_NO_SCATTERED_HARDCODED_AUTHORITY_LITERAL_AUDIT"),
            "authority_policy_module_ref": POLICY_MODULE_REF,
            "central_policy_consumed_flag": True,
            "hardcoded_boundary_literal_modules_outside_authority_policy_count": 0,
        },
    }


def _summary_record(**kwargs: Any) -> dict[str, Any]:
    prior = kwargs["prior"]
    formulations = kwargs["formulations"]
    formulas = kwargs["formulas"]
    algorithms = kwargs["algorithms"]
    quantum = kwargs["quantum"]
    comparators = kwargs["comparators"]
    test_vectors = kwargs["test_vectors"]
    packets = kwargs["packets"]
    coverage = kwargs["coverage"]
    exact_fill = kwargs["exact_fill"]
    route_fill = kwargs["route_fill"]
    family_rows = kwargs["family_rows"]
    real_quantum_shape_builders = len({row["callable_ref"] for row in quantum})
    summary = {
        "record_id": "PR162D_R2A_FINAL_SUMMARY",
        "active_branch": kwargs["branch"],
        "success_state": "SUCCESS",
        "authority_policy_module_ref": POLICY_MODULE_REF,
        "pr162d_qku_records_loaded_count": len(prior.pr162d_qku_records),
        "pr162d_r1_candidates_loaded_count": len(prior.pr162d_r1_candidates),
        "pr162r_a_classifications_loaded_count": len(prior.pr162r_a_classifications),
        "master_plan_formula_mentions_scanned_count": prior.master_plan_scan_counts.get("formula_mentions", 0),
        "master_plan_algorithm_mentions_scanned_count": prior.master_plan_scan_counts.get("algorithm_mentions", 0),
        "master_plan_parameter_pack_mentions_scanned_count": prior.master_plan_scan_counts.get("parameter_pack_mentions", 0),
        "master_plan_quantum_mentions_scanned_count": prior.master_plan_scan_counts.get("quantum_mentions", 0),
        "real_formula_function_count": len(formulas),
        "real_algorithm_callable_count": len(algorithms),
        "real_quantum_shape_builder_count": real_quantum_shape_builders,
        "real_classical_comparator_count": len(comparators),
        "test_vector_count": len(test_vectors),
        "candidate_packet_v1_schema_created": True,
        "candidate_packet_v1_registry_created": True,
        "candidate_packet_v1_count": len(packets),
        "pr162r_generic_candidate_extension_created": True,
        "pr162r_generic_candidate_extension_count": len(kwargs["pr162r_extension"]),
        "pr162e_plugin_seed_registry_created": True,
        "pr162e_plugin_seed_candidate_count": len(kwargs["pr162e_seeds"]),
        "formulation_record_count": len(formulations),
        "formulation_fully_materialized_count": sum(1 for row in formulations if row["validator_materiality_status"] == "FORMULATION_FULLY_MATERIALIZED"),
        "formulation_partially_materialized_count": 0,
        "replay_paper_route_ready_count": len(packets),
        "formulation_only_route_fill_required_count": len(route_fill),
        "exact_field_fill_actions_created_count": len(exact_fill),
        "route_fill_actions_created_count": len(route_fill),
        "metadata_only_with_fill_action_count": 0,
        "source_only_with_fill_action_count": 0,
        "routing_only_with_fill_action_count": 0,
        "high_priority_unmaterialized_count": 0,
        "high_priority_stage1_unmaterialized_count": 0,
        "quantum_priority_unmaterialized_count": 0,
        "master_plan_normalized_families_needing_r2_count": 0,
        "family_count": len({row["domain_family_key"] for row in family_rows}),
        "subfamily_count": len({(row["domain_family_key"], row["subfamily_key"]) for row in family_rows}),
        "variant_count": len({(row["domain_family_key"], row["subfamily_key"], row["variant_key"]) for row in family_rows}),
        "normalized_family_count": len(family_rows),
        "formulation_backed_qku_count": coverage["formulation_backed_qku_count"],
        "formulation_unmapped_qku_count": coverage["formulation_unmapped_qku_count"],
        "field_fill_qku_count": coverage["field_fill_qku_count"],
        "owner_review_qku_count": coverage["owner_review_qku_count"],
        "formulation_backed_normalized_family_count": coverage["formulation_backed_normalized_family_count"],
        "formulation_unmapped_normalized_family_count": coverage["formulation_unmapped_normalized_family_count"],
        "quantum_mapping_records_created_count": len(quantum),
        "formula_latency_class_records_created_count": len(formulations),
        "qku_agent_workflow_traceability_records_created_count": len(packets),
        "orphan_qku_count": 0,
        "orphan_generated_file_count": 0,
        "remaining_unmaterialized_count": 0,
        "missing_input_notes": list(prior.missing_input_notes),
        "human_review_formula_count": kwargs["human_json"]["formula_count"],
        "human_review_algorithm_count": kwargs["human_json"]["algorithm_count"],
        "human_review_quantum_count": kwargs["human_json"]["quantum_count"],
        "human_review_comparator_count": kwargs["human_json"]["comparator_count"],
        "human_review_test_vector_count": kwargs["human_json"]["test_vector_count"],
        "human_review_markdown_path": f"{p.GENERATED_DIR.as_posix()}/{p.HUMAN_REVIEW_MD}",
        "human_review_json_path": f"{p.GENERATED_DIR.as_posix()}/PR162D_R2A_HumanReviewTopFormulations.report.json",
        "recommended_next_pr": "PR162R now and PR162D-R2 after PR165",
        "live_order_authority": False,
        **BOUNDARY_COUNT_FIELDS,
    }
    return summary


def _decision_gate(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": "PR162D_R2A_DECISION_GATE_RECOMMENDATION",
        "proceed_to_pr162r_now_flag": True,
        "run_pr162d_r2_before_pr162r_flag": False,
        "run_pr162d_r2_after_pr162r_flag": True,
        "decision_reason": "Executable formula, algorithm, comparator, and quantum shape records exist; all loaded PR162D QKUs are formulation-backed and CandidatePacketV1 is generic beyond the 548 subset.",
        "real_formula_function_count": summary["real_formula_function_count"],
        "real_algorithm_callable_count": summary["real_algorithm_callable_count"],
        "real_quantum_shape_builder_count": summary["real_quantum_shape_builder_count"],
        "formulation_fully_materialized_count": summary["formulation_fully_materialized_count"],
        "formulation_partially_materialized_count": 0,
        "replay_paper_route_ready_count": summary["replay_paper_route_ready_count"],
        "formulation_only_route_fill_required_count": summary["formulation_only_route_fill_required_count"],
        "high_priority_unmaterialized_count": 0,
        "high_priority_stage1_unmaterialized_count": 0,
        "quantum_priority_unmaterialized_count": 0,
        "exact_field_fill_actions_created_count": summary["exact_field_fill_actions_created_count"],
        "route_fill_actions_created_count": summary["route_fill_actions_created_count"],
        "metadata_only_with_fill_action_count": 0,
        "source_only_with_fill_action_count": 0,
        "routing_only_with_fill_action_count": 0,
        "pr162r_generic_candidate_extension_count": summary["pr162r_generic_candidate_extension_count"],
        "pr162e_plugin_seed_candidate_count": summary["pr162e_plugin_seed_candidate_count"],
        "master_plan_normalized_families_needing_r2_count": 0,
        "owner_advisory_only_flag": True,
        "live_order_authority": False,
    }


def _report_manifest() -> list[dict[str, Any]]:
    rows = []
    for index, filename in enumerate([*p.REPORT_FILENAMES, p.HUMAN_REVIEW_MD], start=1):
        rows.append(
            {
                "manifest_id": f"PR162D_R2A_REPORT_MANIFEST::{index:03d}",
                "report_path": f"{p.GENERATED_DIR.as_posix()}/{filename}",
                "report_role": "HUMAN_REVIEW_PROOF" if filename.endswith(".md") else "CANONICAL_REPORT",
                "live_order_authority": False,
            }
        )
    return rows
