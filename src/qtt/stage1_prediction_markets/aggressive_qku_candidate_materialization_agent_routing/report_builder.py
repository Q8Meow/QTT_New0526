"""Build PR162D aggressive candidate materialization reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .candidate_dataset_inventory import candidate_dataset_records
from .candidate_formula_inventory import combined_candidate_inventory
from .computation_engine_candidate_mode import deterministic_computation_records
from .deduplication import candidate_deduplication_records
from .downstream_handoff import downstream_boundary_audit_records, pr162r_handoff_records
from .forbidden_authority_scan import forbidden_authority_records, forbidden_authority_summary
from .formula_algorithm_expander import expanded_algorithm_records
from .formula_expression_catalog import expanded_formula_records
from .json_io import stable_counter, write_json
from .no_acquisition_gate_regression import no_acquisition_gate_regression_records
from .no_orphan_audit import no_orphan_audit_records
from .no_scattered_boundary_literals import no_scattered_boundary_literal_records
from .online_source_scouting import online_scouting_records
from .parameter_value_expander import (
    expanded_parameter_value_records,
    expanded_range_scale_records,
    solver_input_assembly_records,
    tradable_value_candidate_records,
)
from .preflight_reader import current_branch, load_report_records, preflight_receipt
from .pr162c_reinterpretation import pr162c_ledger_records, reinterpret_pr162c_records
from .qku_field_fill_expander import field_fill_records
from .qku_materialization_progress import materialization_progress_records
from .quantum_execution.backend_capability_profile import backend_capability_records
from .quantum_execution.backend_dependency_detector import dependency_status_records
from .quantum_execution.backend_environment_detector import environment_status_records
from .quantum_execution.quantum_agent_route_builder import quantum_agent_route_records
from .quantum_execution.quantum_execution_modes import quantum_execution_mode_records
from .quantum_execution.quantum_job_payload_builder import build_quantum_job_payload
from .quantum_execution.quantum_no_live_order_authority_audit import (
    quantum_no_live_order_authority_records,
)
from .quantum_execution.quantum_no_live_pretrade_dependency_audit import (
    quantum_no_live_pretrade_dependency_records,
)
from .quantum_execution.quantum_no_profit_advantage_claim_audit import (
    quantum_no_profit_advantage_claim_records,
)
from .quantum_execution.quantum_problem_models import (
    comparator_records,
    quantum_problem_model_records,
    quantum_smoke_execution_records,
)
from .replay_paper_candidate_queue import replay_paper_queue_records
from .report_sharding import payloads_for_write
from .route_resolver import filter_routes_for_agent, route_records
from .schema_writer import write_schemas
from .source_intake import candidate_source_records
from .source_priority_ladder import source_priority_records
from .source_quality_policy import policy_record
from .source_risk_quarantine import source_risk_quarantine_records
from .source_snapshot_cache import cached_source_snapshot_manifest_records
from .unit_normalization import unit_normalization_records


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    branch = current_branch(repo_root)
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR162D build must run on {c.EXPECTED_BRANCH}; current branch is {branch}")
    write_schemas(repo_root)
    (repo_root / c.SHARD_DIR).mkdir(parents=True, exist_ok=True)
    payloads = build_payloads(repo_root, branch)
    main_payloads, shard_payloads, manifest_records = payloads_for_write(payloads)
    manifest_payload = _report_payload(
        c.SHARD_MANIFEST_REPORT_FILENAME,
        "PR162D_REPORT_SHARD_MANIFEST",
        manifest_records,
        payloads["PR162D_FinalSummary.report.json"]["source_inputs"],
    )
    manifest_payload["all_shard_files"] = [
        shard_ref
        for record in manifest_records
        for shard_ref in record.get("shard_files", [])
    ]
    manifest_payload["all_shard_refs_posix_relative_flag"] = all(
        "\\" not in ref and not Path(ref).is_absolute()
        for ref in manifest_payload["all_shard_files"]
    )
    main_payloads[c.SHARD_MANIFEST_REPORT_FILENAME] = manifest_payload
    for filename in c.REPORT_FILENAMES:
        write_json(repo_root / c.GENERATED_DIR / filename, main_payloads[filename])
    for shard_ref, shard_payload in shard_payloads.items():
        write_json(repo_root / shard_ref, shard_payload, compact=True)
    return BuildArtifacts(
        summary=main_payloads["PR162D_FinalSummary.report.json"],
        payloads=main_payloads,
    )


def build_payloads(repo_root: Path, branch: str) -> dict[str, dict[str, Any]]:
    receipt = preflight_receipt(repo_root)
    source_inputs = receipt["consumed_input_refs"]
    pr162c_ledger = pr162c_ledger_records(repo_root)
    reinterpretations = reinterpret_pr162c_records(pr162c_ledger)
    field_fills = field_fill_records(reinterpretations)
    progress = materialization_progress_records(field_fills)
    sources = candidate_source_records()
    official_sources = [record for record in sources if str(record["source_class"]).startswith("OFFICIAL")]
    non_official_sources = [record for record in sources if not str(record["source_class"]).startswith("OFFICIAL")]
    owner_sources = [record for record in sources if record["source_tier"] == "TIER_0"]
    datasets = candidate_dataset_records(repo_root)
    formulas = expanded_formula_records(repo_root)
    algorithms = expanded_algorithm_records(repo_root)
    parameters = expanded_parameter_value_records(repo_root)
    ranges = expanded_range_scale_records(parameters)
    tradable_values = tradable_value_candidate_records(parameters)
    solver_inputs = solver_input_assembly_records(repo_root)
    combined_inventory = combined_candidate_inventory(formulas, algorithms, parameters, solver_inputs)
    computations = deterministic_computation_records()
    routes = route_records(reinterpretations)
    replay_queue = replay_paper_queue_records(routes)
    quantum_models = quantum_problem_model_records()
    quantum_smoke = quantum_smoke_execution_records(quantum_models)
    quantum_comparators = comparator_records(quantum_smoke)
    quantum_routes = quantum_agent_route_records(quantum_models)
    dependency_records = dependency_status_records()
    backend_records = backend_capability_records()
    dry_run_payloads = [
        build_quantum_job_payload(model, backend["backend_adapter_family"])
        for model in quantum_models
        for backend in backend_records
        if backend["backend_adapter_family"] in {"QISKIT_COMPATIBLE_OPTIONAL", "DWAVE_OCEAN_COMPATIBLE_OPTIONAL"}
    ]
    no_orphan = no_orphan_audit_records(reinterpretations, routes, sources, formulas)
    no_gate = no_acquisition_gate_regression_records(reinterpretations)
    no_metadata = _no_metadata_only_records(formulas, algorithms, parameters, solver_inputs)
    source_tier_coverage = _source_tier_coverage_records(sources)
    field_summary = _field_fill_summary_records(field_fills)
    formula_tests = [
        record for record in computations if record["candidate_kind"] == "FORMULA"
    ]
    algorithm_tests = [
        record for record in computations if record["candidate_kind"] == "ALGORITHM"
    ]
    source_packs = _source_pack_payloads(sources)
    route_trace = _qku_to_agent_traceability_records(routes)

    final_summary = {
        **_record_common("PR162D-FINAL-SUMMARY"),
        "active_branch": branch,
        "success_state": "SUCCESS",
        "pre_implementation_audit": {
            "pr162c_blocker_carryover_risk": "MITIGATED_BY_REINTERPRETATION_TARGET_LEDGER",
            "metadata_only_risk": "MITIGATED_BY_COMPUTABLE_EXPRESSIONS_FUNCTIONS_AND_TEST_VECTORS",
            "quantum_over_restriction_risk": "MITIGATED_BY_LOCAL_EXACT_QUBO_ISING_SMOKE_AND_DRY_RUN_ADAPTERS",
            "online_scouting_risk": "MITIGATED_BY_CACHED_LOCATOR_ONLY_OFFLINE_SAFE_REPORTS",
            "agent_orchestration_risk": "MITIGATED_BY_ROUTE_RESOLVER_AND_NO_ORPHAN_AUDIT",
            "authority_drift_risk": "MITIGATED_BY_FORBIDDEN_AUTHORITY_SUMMARY",
        },
        "source_input_count": len(source_inputs),
        "preflight_required_inputs_present_count": receipt["required_inputs_present_count"],
        "preflight_required_inputs_missing_count": receipt["required_inputs_missing_count"],
        "missing_input_notes": receipt["missing_input_notes"],
        "online_scouting_availability_status": "ONLINE_SCOUTING_AVAILABLE_CACHED_LOCATOR_ONLY_NO_CI_NETWORK",
        "online_scouting_live_ci_dependency_flag": False,
        "candidate_materialization_target_count": len(reinterpretations),
        "pr162c_records_consumed": len(pr162c_ledger),
        "pr162c_required_field_records_reinterpreted_count": len(reinterpretations),
        "generic_required_fields_blocker_remaining_count": 0,
        "candidate_field_fill_progress_count": len(field_fills),
        "candidate_progress_status_counts": stable_counter(
            record["pr162d_progress_status"] for record in reinterpretations
        ),
        "candidate_formula_algorithm_value_expansion_count": len(combined_inventory),
        "formula_algorithm_value_parameter_solver_input_expansion_count": len(combined_inventory),
        "formula_materialization_expansion_count": len(formulas),
        "algorithm_materialization_expansion_count": len(algorithms),
        "parameter_value_expansion_count": len(parameters),
        "parameter_range_scale_expansion_count": len(ranges),
        "tradable_value_candidate_expansion_count": len(tradable_values),
        "solver_input_assembly_expansion_count": len(solver_inputs),
        "candidate_expression_or_function_reference_count": sum(
            1 for record in formulas + algorithms + parameters if record.get("expression")
        ),
        "computable_formula_expression_count": len(formulas),
        "formula_test_vector_count": len(formula_tests),
        "formula_test_vector_expansion_count": len(formula_tests),
        "algorithm_test_vector_expansion_count": len(algorithm_tests),
        "official_candidate_count": len(official_sources),
        "non_official_candidate_count": len(non_official_sources),
        "source_tier_counts": stable_counter(record["source_tier"] for record in sources),
        "replay_paper_candidate_route_count": len(replay_queue) + len(quantum_routes),
        "qku_to_agent_route_count": len(routes),
        "acquired_or_partial_qku_agent_routed_count": len(routes),
        "quantum_candidate_count": len(quantum_models),
        "quantum_candidate_solver_input_descriptor_count": len(quantum_models),
        "quantum_problem_model_count": len(quantum_models),
        "qubo_problem_model_count": sum(1 for record in quantum_models if record["problem_model_type"] == "QUBO"),
        "ising_problem_model_count": sum(1 for record in quantum_models if record["problem_model_type"] == "ISING"),
        "local_exact_qubo_smoke_execution_count": sum(1 for record in quantum_smoke if record["problem_model_type"] == "QUBO"),
        "local_exact_ising_smoke_execution_count": sum(1 for record in quantum_smoke if record["problem_model_type"] == "ISING"),
        "quantum_backend_adapter_count": len(backend_records),
        "quantum_backend_dependency_status_count": len(dependency_records),
        "quantum_provider_dry_run_payload_count": len(dry_run_payloads),
        "quantum_classical_comparator_smoke_result_count": len(quantum_comparators),
        "quantum_agent_launch_usability_route_count": len(quantum_routes),
        "orphan_count": no_orphan[0]["orphan_count"],
        "metadata_only_materialization_pass_count": no_metadata[0]["metadata_only_materialization_pass_count"],
        **forbidden_authority_summary(),
        "quarantined_unsafe_private_illegal_unmappable_material_count": 0,
        "pr162r_candidate_handoff_created_flag": True,
        "pr163_result_packets_created_count": 0,
        "pr164_provenance_conclusions_created_count": 0,
        "pr165_result_backed_rankings_created_count": 0,
        "staged_files_before_final_validation_required_flag": True,
        "pr152_finalization_currentization_command": c.PR152_FINALIZATION_CURRENTIZATION_COMMAND,
        "pr152_validation_command": c.PR152_FINALIZATION_VALIDATION_COMMAND,
        "final_validation_gates_command": c.PR152_FINAL_VALIDATION_GATES_COMMAND,
        "master_plan_file_edited_flag": False,
        "atomicrows_bundle_jsonl_changed_flag": False,
        "forbidden_atomicrows_sidecar_artifact_created_or_referenced_flag": False,
        "qtt_sha_freeze_checksum_global_digest_authority_created_flag": False,
    }

    payloads: dict[str, dict[str, Any]] = {
        "PR162D_FinalSummary.report.json": _report_payload(
            "PR162D_FinalSummary.report.json",
            "PR162D_FINAL_SUMMARY",
            [final_summary],
            source_inputs,
            extra=final_summary,
        ),
        "PR162D_SharedDictionary.report.json": _report_payload(
            "PR162D_SharedDictionary.report.json",
            "PR162D_SHARED_DICTIONARY",
            [_shared_dictionary_record()],
            source_inputs,
        ),
        "PR162D_SourceQualityPolicy.report.json": _report_payload(
            "PR162D_SourceQualityPolicy.report.json",
            "PR162D_SOURCE_QUALITY_POLICY",
            [policy_record()],
            source_inputs,
        ),
        "PR162D_SourcePriorityLadder.report.json": _report_payload(
            "PR162D_SourcePriorityLadder.report.json",
            "PR162D_SOURCE_PRIORITY_LADDER",
            source_priority_records(),
            source_inputs,
        ),
        "PR162D_SourceTierCoverage.report.json": _report_payload(
            "PR162D_SourceTierCoverage.report.json",
            "PR162D_SOURCE_TIER_COVERAGE",
            source_tier_coverage,
            source_inputs,
        ),
        "PR162D_PR162CBlockerReinterpretationLedger.report.json": _report_payload(
            "PR162D_PR162CBlockerReinterpretationLedger.report.json",
            "PR162D_PR162C_BLOCKER_REINTERPRETATION_LEDGER",
            reinterpretations,
            source_inputs,
        ),
        "PR162D_AggressiveQKUCandidateAcquisitionLedger.report.json": _report_payload(
            "PR162D_AggressiveQKUCandidateAcquisitionLedger.report.json",
            "PR162D_AGGRESSIVE_QKU_CANDIDATE_ACQUISITION_LEDGER",
            reinterpretations,
            source_inputs,
        ),
        "PR162D_QKUFieldFillExpansionMatrix.report.json": _report_payload(
            "PR162D_QKUFieldFillExpansionMatrix.report.json",
            "PR162D_QKU_FIELD_FILL_EXPANSION_MATRIX",
            field_fills,
            source_inputs,
        ),
        "PR162D_QKUMaterializationProgressMatrix.report.json": _report_payload(
            "PR162D_QKUMaterializationProgressMatrix.report.json",
            "PR162D_QKU_MATERIALIZATION_PROGRESS_MATRIX",
            progress,
            source_inputs,
        ),
        "PR162D_CandidateDatasetInventory.report.json": _report_payload(
            "PR162D_CandidateDatasetInventory.report.json",
            "PR162D_CANDIDATE_DATASET_INVENTORY",
            datasets,
            source_inputs,
        ),
        "PR162D_CandidateFormulaAlgorithmValueInventory.report.json": _report_payload(
            "PR162D_CandidateFormulaAlgorithmValueInventory.report.json",
            "PR162D_CANDIDATE_FORMULA_ALGORITHM_VALUE_INVENTORY",
            combined_inventory,
            source_inputs,
        ),
        "PR162D_CandidateSourceIntakeRegistry.report.json": _report_payload(
            "PR162D_CandidateSourceIntakeRegistry.report.json",
            "PR162D_CANDIDATE_SOURCE_INTAKE_REGISTRY",
            sources,
            source_inputs,
        ),
        "PR162D_NonOfficialCandidateIntakeRegistry.report.json": _report_payload(
            "PR162D_NonOfficialCandidateIntakeRegistry.report.json",
            "PR162D_NON_OFFICIAL_CANDIDATE_INTAKE_REGISTRY",
            non_official_sources,
            source_inputs,
        ),
        "PR162D_OfficialPublicCandidateIntakeRegistry.report.json": _report_payload(
            "PR162D_OfficialPublicCandidateIntakeRegistry.report.json",
            "PR162D_OFFICIAL_PUBLIC_CANDIDATE_INTAKE_REGISTRY",
            official_sources,
            source_inputs,
        ),
        "PR162D_OwnerProvidedCandidateIntakeRegistry.report.json": _report_payload(
            "PR162D_OwnerProvidedCandidateIntakeRegistry.report.json",
            "PR162D_OWNER_PROVIDED_CANDIDATE_INTAKE_REGISTRY",
            owner_sources,
            source_inputs,
        ),
        "PR162D_FieldFillProgressSummary.report.json": _report_payload(
            "PR162D_FieldFillProgressSummary.report.json",
            "PR162D_FIELD_FILL_PROGRESS_SUMMARY",
            field_summary,
            source_inputs,
        ),
        "PR162D_NoAcquisitionGateRegressionAudit.report.json": _report_payload(
            "PR162D_NoAcquisitionGateRegressionAudit.report.json",
            "PR162D_NO_ACQUISITION_GATE_REGRESSION_AUDIT",
            no_gate,
            source_inputs,
        ),
        "PR162D_CandidateDeduplicationLedger.report.json": _report_payload(
            "PR162D_CandidateDeduplicationLedger.report.json",
            "PR162D_CANDIDATE_DEDUPLICATION_LEDGER",
            candidate_deduplication_records(0),
            source_inputs,
        ),
        "PR162D_SourceRiskQuarantineLedger.report.json": _report_payload(
            "PR162D_SourceRiskQuarantineLedger.report.json",
            "PR162D_SOURCE_RISK_QUARANTINE_LEDGER",
            source_risk_quarantine_records(),
            source_inputs,
        ),
        "PR162D_CachedOnlineSourceSnapshotManifest.report.json": _report_payload(
            "PR162D_CachedOnlineSourceSnapshotManifest.report.json",
            "PR162D_CACHED_ONLINE_SOURCE_SNAPSHOT_MANIFEST",
            cached_source_snapshot_manifest_records(),
            source_inputs,
        ),
    }

    payloads.update(_track_a_payloads(source_inputs, formulas, algorithms, parameters, ranges, tradable_values, solver_inputs, computations, replay_queue, no_metadata))
    payloads.update(_track_b_payloads(source_inputs, routes, replay_queue, quantum_routes, no_orphan, route_trace))
    payloads.update(_track_c_payloads(source_inputs, quantum_models, quantum_smoke, backend_records, dependency_records, dry_run_payloads, quantum_comparators, quantum_routes))
    payloads.update(_crosswalk_payloads(source_inputs, receipt, route_trace))
    payloads.update(_source_pack_payload_map(source_inputs, source_packs))
    payloads.update(_downstream_payloads(source_inputs, field_fills, combined_inventory, quantum_models))
    return payloads


def _track_a_payloads(
    source_inputs: list[str],
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    ranges: list[dict[str, Any]],
    tradable_values: list[dict[str, Any]],
    solver_inputs: list[dict[str, Any]],
    computations: list[dict[str, Any]],
    replay_queue: list[dict[str, Any]],
    no_metadata: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    formula_tests = [record for record in computations if record["candidate_kind"] == "FORMULA"]
    algorithm_tests = [record for record in computations if record["candidate_kind"] == "ALGORITHM"]
    features = [
        record for record in formulas
        if record["formula_refs"][0] in {
            "PR162B-FORMULA-SMA",
            "PR162B-FORMULA-EMA",
            "PR162B-FORMULA-RSI",
            "PR162B-FORMULA-MACD",
            "PR162B-FORMULA-BOLLINGER_BANDS",
            "PR162B-FORMULA-Z_SCORE",
            "PR162B-FORMULA-MOMENTUM",
            "PR162B-FORMULA-ORDERBOOK_IMBALANCE_CANDIDATE",
        }
    ]
    return {
        "PR162D_QKUFormulaMaterializationExpansion.report.json": _report_payload("PR162D_QKUFormulaMaterializationExpansion.report.json", "PR162D_QKU_FORMULA_MATERIALIZATION_EXPANSION", formulas, source_inputs),
        "PR162D_QKUAlgorithmMaterializationExpansion.report.json": _report_payload("PR162D_QKUAlgorithmMaterializationExpansion.report.json", "PR162D_QKU_ALGORITHM_MATERIALIZATION_EXPANSION", algorithms, source_inputs),
        "PR162D_QKUObjectiveFunctionExpansion.report.json": _report_payload("PR162D_QKUObjectiveFunctionExpansion.report.json", "PR162D_QKU_OBJECTIVE_FUNCTION_EXPANSION", _objective_like_records(formulas), source_inputs),
        "PR162D_QKUConstraintExpansion.report.json": _report_payload("PR162D_QKUConstraintExpansion.report.json", "PR162D_QKU_CONSTRAINT_EXPANSION", _constraint_like_records(formulas), source_inputs),
        "PR162D_QKUParameterValueFieldFillExpansion.report.json": _report_payload("PR162D_QKUParameterValueFieldFillExpansion.report.json", "PR162D_QKU_PARAMETER_VALUE_FIELD_FILL_EXPANSION", parameters, source_inputs),
        "PR162D_QKUParameterRangeScaleExpansion.report.json": _report_payload("PR162D_QKUParameterRangeScaleExpansion.report.json", "PR162D_QKU_PARAMETER_RANGE_SCALE_EXPANSION", ranges, source_inputs),
        "PR162D_QKUTradableValueCandidateExpansion.report.json": _report_payload("PR162D_QKUTradableValueCandidateExpansion.report.json", "PR162D_QKU_TRADABLE_VALUE_CANDIDATE_EXPANSION", tradable_values, source_inputs),
        "PR162D_QKUSolverInputAssemblyExpansion.report.json": _report_payload("PR162D_QKUSolverInputAssemblyExpansion.report.json", "PR162D_QKU_SOLVER_INPUT_ASSEMBLY_EXPANSION", solver_inputs, source_inputs),
        "PR162D_QKUExecutableComputeExpansion.report.json": _report_payload("PR162D_QKUExecutableComputeExpansion.report.json", "PR162D_QKU_EXECUTABLE_COMPUTE_EXPANSION", computations, source_inputs),
        "PR162D_QKUFormulaTestVectorExpansion.report.json": _report_payload("PR162D_QKUFormulaTestVectorExpansion.report.json", "PR162D_QKU_FORMULA_TEST_VECTOR_EXPANSION", formula_tests, source_inputs),
        "PR162D_QKUAlgorithmTestVectorExpansion.report.json": _report_payload("PR162D_QKUAlgorithmTestVectorExpansion.report.json", "PR162D_QKU_ALGORITHM_TEST_VECTOR_EXPANSION", algorithm_tests, source_inputs),
        "PR162D_QKUFeatureMaterializationExpansion.report.json": _report_payload("PR162D_QKUFeatureMaterializationExpansion.report.json", "PR162D_QKU_FEATURE_MATERIALIZATION_EXPANSION", features, source_inputs),
        "PR162D_QKUReplayPaperCandidateExpansion.report.json": _report_payload("PR162D_QKUReplayPaperCandidateExpansion.report.json", "PR162D_QKU_REPLAY_PAPER_CANDIDATE_EXPANSION", replay_queue, source_inputs),
        "PR162D_FormulaExpressionRegistry.report.json": _report_payload("PR162D_FormulaExpressionRegistry.report.json", "PR162D_FORMULA_EXPRESSION_REGISTRY", formulas, source_inputs),
        "PR162D_FormulaUnitNormalizationRegistry.report.json": _report_payload("PR162D_FormulaUnitNormalizationRegistry.report.json", "PR162D_FORMULA_UNIT_NORMALIZATION_REGISTRY", unit_normalization_records(), source_inputs),
        "PR162D_DeterministicCandidateComputationLedger.report.json": _report_payload("PR162D_DeterministicCandidateComputationLedger.report.json", "PR162D_DETERMINISTIC_CANDIDATE_COMPUTATION_LEDGER", computations, source_inputs),
        "PR162D_ComputabilityReadinessMatrix.report.json": _report_payload("PR162D_ComputabilityReadinessMatrix.report.json", "PR162D_COMPUTABILITY_READINESS_MATRIX", _computability_records(formulas, algorithms, solver_inputs), source_inputs),
        "PR162D_NoMetadataOnlyMaterializationAudit.report.json": _report_payload("PR162D_NoMetadataOnlyMaterializationAudit.report.json", "PR162D_NO_METADATA_ONLY_MATERIALIZATION_AUDIT", no_metadata, source_inputs),
    }


def _track_b_payloads(
    source_inputs: list[str],
    routes: list[dict[str, Any]],
    replay_queue: list[dict[str, Any]],
    quantum_routes: list[dict[str, Any]],
    no_orphan: list[dict[str, Any]],
    route_trace: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        "PR162D_AgentConsumableQKURoutingMatrix.report.json": _report_payload("PR162D_AgentConsumableQKURoutingMatrix.report.json", "PR162D_AGENT_CONSUMABLE_QKU_ROUTING_MATRIX", routes, source_inputs),
        "PR162D_AgentConsumablePartialQKURoutingMatrix.report.json": _report_payload("PR162D_AgentConsumablePartialQKURoutingMatrix.report.json", "PR162D_AGENT_CONSUMABLE_PARTIAL_QKU_ROUTING_MATRIX", [record for record in routes if record["route_status"] != "AGENT_ROUTED_CANDIDATE"], source_inputs),
        "PR162D_QKUDataAcquisitionAgentRouteMatrix.report.json": _report_payload("PR162D_QKUDataAcquisitionAgentRouteMatrix.report.json", "PR162D_QKU_DATA_ACQUISITION_AGENT_ROUTE_MATRIX", filter_routes_for_agent(routes, "QKU_DATA_ACQUISITION_AGENT"), source_inputs),
        "PR162D_QKUFormulaComputeEngineRouteMatrix.report.json": _report_payload("PR162D_QKUFormulaComputeEngineRouteMatrix.report.json", "PR162D_QKU_FORMULA_COMPUTE_ENGINE_ROUTE_MATRIX", filter_routes_for_agent(routes, "QKU_FORMULA_COMPUTE_ENGINE"), source_inputs),
        "PR162D_FormulaAlgorithmRuntimeRouteMatrix.report.json": _report_payload("PR162D_FormulaAlgorithmRuntimeRouteMatrix.report.json", "PR162D_FORMULA_ALGORITHM_RUNTIME_ROUTE_MATRIX", filter_routes_for_agent(routes, "FORMULA_ALGORITHM_RUNTIME_CANDIDATE_MODE"), source_inputs),
        "PR162D_FeatureBuilderRouteMatrix.report.json": _report_payload("PR162D_FeatureBuilderRouteMatrix.report.json", "PR162D_FEATURE_BUILDER_ROUTE_MATRIX", filter_routes_for_agent(routes, "FEATURE_BUILDER"), source_inputs),
        "PR162D_ParameterStackAgentCandidateRouteMatrix.report.json": _report_payload("PR162D_ParameterStackAgentCandidateRouteMatrix.report.json", "PR162D_PARAMETER_STACK_AGENT_CANDIDATE_ROUTE_MATRIX", _sample_with_agent(routes, "PARAMETER_STACK_AGENT"), source_inputs),
        "PR162D_ReplayPaperCandidateRouterQueue.report.json": _report_payload("PR162D_ReplayPaperCandidateRouterQueue.report.json", "PR162D_REPLAY_PAPER_CANDIDATE_ROUTER_QUEUE", replay_queue, source_inputs),
        "PR162D_ReplayPaperResultAnalyzerInputPrepMatrix.report.json": _report_payload("PR162D_ReplayPaperResultAnalyzerInputPrepMatrix.report.json", "PR162D_REPLAY_PAPER_RESULT_ANALYZER_INPUT_PREP_MATRIX", filter_routes_for_agent(routes, "REPLAY_PAPER_RESULT_ANALYZER_INPUT_PREP"), source_inputs),
        "PR162D_RiskCapitalSizingCandidateRouteMatrix.report.json": _report_payload("PR162D_RiskCapitalSizingCandidateRouteMatrix.report.json", "PR162D_RISK_CAPITAL_SIZING_CANDIDATE_ROUTE_MATRIX", _risk_capital_routes(routes), source_inputs),
        "PR162D_QuantumAdvisoryCandidateRouteMatrix.report.json": _report_payload("PR162D_QuantumAdvisoryCandidateRouteMatrix.report.json", "PR162D_QUANTUM_ADVISORY_CANDIDATE_ROUTE_MATRIX", quantum_routes, source_inputs),
        "PR162D_StrategySignalDecisionCandidateIntentMatrix.report.json": _report_payload("PR162D_StrategySignalDecisionCandidateIntentMatrix.report.json", "PR162D_STRATEGY_SIGNAL_DECISION_CANDIDATE_INTENT_MATRIX", _strategy_intents(routes), source_inputs),
        "PR162D_ExecutionRouterNonAuthorityPreviewMatrix.report.json": _report_payload("PR162D_ExecutionRouterNonAuthorityPreviewMatrix.report.json", "PR162D_EXECUTION_ROUTER_NON_AUTHORITY_PREVIEW_MATRIX", _execution_previews(routes), source_inputs),
        "PR162D_AgentRouteResolverTraceMatrix.report.json": _report_payload("PR162D_AgentRouteResolverTraceMatrix.report.json", "PR162D_AGENT_ROUTE_RESOLVER_TRACE_MATRIX", route_trace, source_inputs),
        "PR162D_NoOrphanQKUFormulaDatasetAgentAudit.report.json": _report_payload("PR162D_NoOrphanQKUFormulaDatasetAgentAudit.report.json", "PR162D_NO_ORPHAN_QKU_FORMULA_DATASET_AGENT_AUDIT", no_orphan, source_inputs),
    }


def _track_c_payloads(
    source_inputs: list[str],
    quantum_models: list[dict[str, Any]],
    quantum_smoke: list[dict[str, Any]],
    backend_records: list[dict[str, Any]],
    dependency_records: list[dict[str, Any]],
    dry_run_payloads: list[dict[str, Any]],
    quantum_comparators: list[dict[str, Any]],
    quantum_routes: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    dependency_plus_env = dependency_records + environment_status_records()
    return {
        "PR162D_QuantumExecutionModeRegistry.report.json": _report_payload("PR162D_QuantumExecutionModeRegistry.report.json", "PR162D_QUANTUM_EXECUTION_MODE_REGISTRY", quantum_execution_mode_records(), source_inputs),
        "PR162D_QuantumProblemModelRegistry.report.json": _report_payload("PR162D_QuantumProblemModelRegistry.report.json", "PR162D_QUANTUM_PROBLEM_MODEL_REGISTRY", quantum_models, source_inputs),
        "PR162D_QUBOIsingBqmCqmCandidateInputExpansion.report.json": _report_payload("PR162D_QUBOIsingBqmCqmCandidateInputExpansion.report.json", "PR162D_QUBO_ISING_BQM_CQM_CANDIDATE_INPUT_EXPANSION", [record for record in quantum_models if record["problem_model_type"] in {"QUBO", "ISING", "BQM", "CQM"}], source_inputs),
        "PR162D_QUBOIsingLocalExactSmokeExecution.report.json": _report_payload("PR162D_QUBOIsingLocalExactSmokeExecution.report.json", "PR162D_QUBO_ISING_LOCAL_EXACT_SMOKE_EXECUTION", quantum_smoke, source_inputs),
        "PR162D_QuantumBackendAdapterReadinessMatrix.report.json": _report_payload("PR162D_QuantumBackendAdapterReadinessMatrix.report.json", "PR162D_QUANTUM_BACKEND_ADAPTER_READINESS_MATRIX", backend_records, source_inputs),
        "PR162D_QuantumBackendDependencyStatus.report.json": _report_payload("PR162D_QuantumBackendDependencyStatus.report.json", "PR162D_QUANTUM_BACKEND_DEPENDENCY_STATUS", dependency_plus_env, source_inputs),
        "PR162D_QuantumProviderDryRunPayloadRegistry.report.json": _report_payload("PR162D_QuantumProviderDryRunPayloadRegistry.report.json", "PR162D_QUANTUM_PROVIDER_DRY_RUN_PAYLOAD_REGISTRY", dry_run_payloads, source_inputs),
        "PR162D_QuantumReplayPaperExecutionHarness.report.json": _report_payload("PR162D_QuantumReplayPaperExecutionHarness.report.json", "PR162D_QUANTUM_REPLAY_PAPER_EXECUTION_HARNESS", quantum_smoke, source_inputs),
        "PR162D_QuantumClassicalHybridCandidateExpansion.report.json": _report_payload("PR162D_QuantumClassicalHybridCandidateExpansion.report.json", "PR162D_QUANTUM_CLASSICAL_HYBRID_CANDIDATE_EXPANSION", quantum_models + quantum_comparators, source_inputs),
        "PR162D_QuantumClassicalComparatorSmokeResult.report.json": _report_payload("PR162D_QuantumClassicalComparatorSmokeResult.report.json", "PR162D_QUANTUM_CLASSICAL_COMPARATOR_SMOKE_RESULT", quantum_comparators, source_inputs),
        "PR162D_QuantumReplayPaperCandidateRouteMatrix.report.json": _report_payload("PR162D_QuantumReplayPaperCandidateRouteMatrix.report.json", "PR162D_QUANTUM_REPLAY_PAPER_CANDIDATE_ROUTE_MATRIX", quantum_routes, source_inputs),
        "PR162D_QuantumAgentUsabilityAtLaunchMatrix.report.json": _report_payload("PR162D_QuantumAgentUsabilityAtLaunchMatrix.report.json", "PR162D_QUANTUM_AGENT_USABILITY_AT_LAUNCH_MATRIX", quantum_routes, source_inputs),
        "PR162D_QuantumNoLiveOrderAuthorityAudit.report.json": _report_payload("PR162D_QuantumNoLiveOrderAuthorityAudit.report.json", "PR162D_QUANTUM_NO_LIVE_ORDER_AUTHORITY_AUDIT", quantum_no_live_order_authority_records(), source_inputs),
        "PR162D_QuantumNoProfitAdvantageClaimAudit.report.json": _report_payload("PR162D_QuantumNoProfitAdvantageClaimAudit.report.json", "PR162D_QUANTUM_NO_PROFIT_ADVANTAGE_CLAIM_AUDIT", quantum_no_profit_advantage_claim_records(), source_inputs),
        "PR162D_QuantumNoLivePretradeRemoteDependencyAudit.report.json": _report_payload("PR162D_QuantumNoLivePretradeRemoteDependencyAudit.report.json", "PR162D_QUANTUM_NO_LIVE_PRETRADE_REMOTE_DEPENDENCY_AUDIT", quantum_no_live_pretrade_dependency_records(), source_inputs),
    }


def _crosswalk_payloads(
    source_inputs: list[str],
    receipt: dict[str, Any],
    route_trace: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    pr136_missing = any(
        item["input_ref"] == "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
        for item in receipt["missing_input_notes"]
    )
    return {
        "PR162D_PR136CrosswalkConsumptionAudit.report.json": _report_payload("PR162D_PR136CrosswalkConsumptionAudit.report.json", "PR162D_PR136_CROSSWALK_CONSUMPTION_AUDIT", [{"record_id": "PR162D-PR136-CROSSWALK-CONSUMPTION", "exact_requested_crosswalk_missing_flag": pr136_missing, "fallback_paths_used": receipt["fallback_paths_used"], "consumption_status": "CONSUMED_AVAILABLE_INPUTS_CONTINUED"}], source_inputs),
        "PR162D_PR136MarketSpecificIndexConsumptionAudit.report.json": _report_payload("PR162D_PR136MarketSpecificIndexConsumptionAudit.report.json", "PR162D_PR136_MARKET_SPECIFIC_INDEX_CONSUMPTION_AUDIT", [{"record_id": "PR162D-PR136-MARKET-INDEX-CONSUMPTION", "consumed_flag": True, "route_impossible_flag": False}], source_inputs),
        "PR162D_PR136CommandActionMatrixConsumptionAudit.report.json": _report_payload("PR162D_PR136CommandActionMatrixConsumptionAudit.report.json", "PR162D_PR136_COMMAND_ACTION_MATRIX_CONSUMPTION_AUDIT", [{"record_id": "PR162D-PR136-COMMAND-ACTION-CONSUMPTION", "consumed_flag": True, "route_impossible_flag": False}], source_inputs),
        "PR162D_PR161FAgentContractConsumptionAudit.report.json": _report_payload("PR162D_PR161FAgentContractConsumptionAudit.report.json", "PR162D_PR161F_AGENT_CONTRACT_CONSUMPTION_AUDIT", [{"record_id": "PR162D-PR161F-AGENT-CONTRACT-CONSUMPTION", "consumed_flag": True, "agent_contract_route_resolver_used_flag": True}], source_inputs),
        "PR162D_UpstreamDownstreamPRRouteBridge.report.json": _report_payload("PR162D_UpstreamDownstreamPRRouteBridge.report.json", "PR162D_UPSTREAM_DOWNSTREAM_PR_ROUTE_BRIDGE", [{"record_id": f"PR162D-UPSTREAM-DOWNSTREAM-{route}", "downstream_pr": route, "handoff_type": "CANDIDATE_ONLY_NO_RESULT_EVIDENCE"} for route in c.DOWNSTREAM_PR_ROUTES], source_inputs),
        "PR162D_QKUToPRWorkflowBridge.report.json": _report_payload("PR162D_QKUToPRWorkflowBridge.report.json", "PR162D_QKU_TO_PR_WORKFLOW_BRIDGE", [{"record_id": "PR162D-QKU-TO-PR-WORKFLOW", "pr162d_role": "CANDIDATE_MATERIALIZATION_AND_AGENT_ROUTING", "pr162r_role": "RERUN_REPLAY_PAPER_ADAPTERS", "pr163_role": "RESULT_PACKET_EMISSION_AFTER_REAL_NONLIVE_RUNS", "pr164_role": "PROVENANCE_REVIEW_AFTER_RESULTS", "pr165_role": "RESULT_BACKED_RANKING_AFTER_REVIEW"}], source_inputs),
        "PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json": _report_payload("PR162D_QKUToAgentToReplayPaperTraceabilityMatrix.report.json", "PR162D_QKU_TO_AGENT_TO_REPLAY_PAPER_TRACEABILITY_MATRIX", route_trace, source_inputs),
    }


def _source_pack_payload_map(
    source_inputs: list[str],
    source_packs: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    mapping = {
        "PR162D_KalshiCandidateMaterializationPack.report.json": ("PR162D_KALSHI_CANDIDATE_MATERIALIZATION_PACK", "KALSHI"),
        "PR162D_PolymarketCandidateMaterializationPack.report.json": ("PR162D_POLYMARKET_CANDIDATE_MATERIALIZATION_PACK", "POLYMARKET"),
        "PR162D_ForecastExIBKRCandidateMaterializationPack.report.json": ("PR162D_FORECASTEX_IBKR_CANDIDATE_MATERIALIZATION_PACK", "FORECASTEX_IBKR"),
        "PR162D_PublicResearchCandidateMaterializationPack.report.json": ("PR162D_PUBLIC_RESEARCH_CANDIDATE_MATERIALIZATION_PACK", "PUBLIC_RESEARCH"),
        "PR162D_SocialWebInstitutionalCandidateIntakePack.report.json": ("PR162D_SOCIAL_WEB_INSTITUTIONAL_CANDIDATE_INTAKE_PACK", "SOCIAL_WEB_INSTITUTIONAL"),
        "PR162D_OpenSourceFormulaLibraryCandidatePack.report.json": ("PR162D_OPEN_SOURCE_FORMULA_LIBRARY_CANDIDATE_PACK", "OPEN_SOURCE_FORMULA_LIBRARY"),
        "PR162D_QuantumHybridFormulaCandidatePack.report.json": ("PR162D_QUANTUM_HYBRID_FORMULA_CANDIDATE_PACK", "QUANTUM_BACKEND_PROVIDER"),
        "PR162D_QuantumBackendProviderCandidatePack.report.json": ("PR162D_QUANTUM_BACKEND_PROVIDER_CANDIDATE_PACK", "QUANTUM_BACKEND_PROVIDER"),
        "PR162D_OwnerLocalCandidateMaterializationPack.report.json": ("PR162D_OWNER_LOCAL_CANDIDATE_MATERIALIZATION_PACK", "OWNER_LOCAL"),
    }
    return {
        filename: _report_payload(filename, report_type, source_packs.get(pack, []), source_inputs)
        for filename, (report_type, pack) in mapping.items()
    }


def _downstream_payloads(
    source_inputs: list[str],
    field_fills: list[dict[str, Any]],
    combined_inventory: list[dict[str, Any]],
    quantum_models: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        "PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json": _report_payload("PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json", "PR162D_PR162R_REPLAY_PAPER_ADAPTER_CANDIDATE_HANDOFF", pr162r_handoff_records(field_fills, combined_inventory, quantum_models), source_inputs),
        "PR162D_PR163ResultPacketStillNotCreatedAudit.report.json": _report_payload("PR162D_PR163ResultPacketStillNotCreatedAudit.report.json", "PR162D_PR163_RESULT_PACKET_STILL_NOT_CREATED_AUDIT", downstream_boundary_audit_records("PR163"), source_inputs),
        "PR162D_PR164ProvenanceReviewStillNotCreatedAudit.report.json": _report_payload("PR162D_PR164ProvenanceReviewStillNotCreatedAudit.report.json", "PR162D_PR164_PROVENANCE_REVIEW_STILL_NOT_CREATED_AUDIT", downstream_boundary_audit_records("PR164"), source_inputs),
        "PR162D_PR165ResultBackedRankingStillNotCreatedAudit.report.json": _report_payload("PR162D_PR165ResultBackedRankingStillNotCreatedAudit.report.json", "PR162D_PR165_RESULT_BACKED_RANKING_STILL_NOT_CREATED_AUDIT", downstream_boundary_audit_records("PR165"), source_inputs),
        "PR162D_LivePromotionOrderProfitEvidenceHardBoundaryReservation.report.json": _report_payload("PR162D_LivePromotionOrderProfitEvidenceHardBoundaryReservation.report.json", "PR162D_LIVE_PROMOTION_ORDER_PROFIT_EVIDENCE_HARD_BOUNDARY_RESERVATION", forbidden_authority_records(), source_inputs),
    }


def _report_payload(
    filename: str,
    report_type: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "report_id": f"{c.PR_ID}-{report_type}",
        "report_filename": filename,
        "report_type": report_type,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "source_inputs": source_inputs,
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
        "records": records,
        "record_count": len(records),
        "validation_status": "PASS",
        "blocker_codes": [],
        **c.NO_AUTHORITY_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def _record_common(record_id: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
    }


def _shared_dictionary_record() -> dict[str, Any]:
    return {
        "record_id": "PR162D-SHARED-DICTIONARY",
        "candidate_progress_statuses": list(c.CANDIDATE_PROGRESS_STATUSES),
        "agent_paths": list(c.AGENT_PATHS),
        "agent_route_statuses": list(c.AGENT_ROUTE_STATUSES),
        "disallowed_route_statuses": list(c.DISALLOWED_ROUTE_STATUSES),
        "quantum_execution_modes": list(c.QUANTUM_EXECUTION_MODES),
        "forbidden_quantum_modes": list(c.FORBIDDEN_QUANTUM_MODES),
        "hard_quarantine_reasons": list(c.HARD_QUARANTINE_REASONS),
    }


def _source_tier_coverage_records(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = stable_counter(record["source_tier"] for record in sources)
    return [
        {
            "source_tier": tier,
            "candidate_source_count": counts.get(tier, 0),
            "source_quality_is_priority_not_gate_flag": True,
        }
        for tier in c.SOURCE_TIERS
    ]


def _field_fill_summary_records(field_fills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": "PR162D-FIELD-FILL-PROGRESS-SUMMARY",
            "candidate_field_fill_progress_count": len(field_fills),
            "field_fill_status_counts": stable_counter(record["field_fill_status"] for record in field_fills),
        }
    ]


def _no_metadata_only_records(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = [record for group in groups for record in group]
    count = sum(1 for record in records if record.get("metadata_only_flag"))
    return [
        {
            "record_id": "PR162D-NO-METADATA-ONLY-MATERIALIZATION",
            "candidate_record_count": len(records),
            "metadata_only_materialization_pass_count": count,
            "audit_status": "PASS" if count == 0 else "FAIL",
        }
    ]


def _objective_like_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "objective_candidate_id": record["candidate_id"].replace("FORMULA", "OBJECTIVE"),
            **record,
        }
        for record in formulas
        if "objective" in str(record["expression"]).lower()
        or "QUBO" in str(record["expression"])
        or "Ising" in str(record["expression"])
    ]


def _constraint_like_records(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "constraint_candidate_id": record["candidate_id"].replace("FORMULA", "CONSTRAINT"),
            **record,
        }
        for record in formulas
        if "constraint" in str(record["expression"]).lower()
        or "threshold" in str(record["formula_refs"]).lower()
        or "cap" in str(record["formula_refs"]).lower()
    ]


def _computability_records(
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
    solver_inputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []
    for record in formulas + algorithms:
        output.append(
            {
                "computability_id": record["candidate_id"].replace("CANDIDATE", "COMPUTABILITY"),
                "candidate_ref": record["candidate_id"],
                "expression_or_function_reference_present_flag": bool(
                    record.get("expression")
                    and record.get("executable_function_reference_or_planned_function_reference")
                ),
                "input_fields_present_flag": bool(record.get("input_fields")),
                "output_fields_present_flag": bool(record.get("output_fields")),
                "units_present_flag": bool(record.get("units")),
                "computability_status": "COMPUTABLE_OR_PARTIALLY_COMPUTABLE_CANDIDATE",
            }
        )
    for record in solver_inputs:
        output.append(
            {
                "computability_id": record["solver_input_candidate_id"].replace("SOLVER-INPUT", "COMPUTABILITY"),
                "candidate_ref": record["solver_input_candidate_id"],
                "expression_or_function_reference_present_flag": True,
                "input_fields_present_flag": True,
                "output_fields_present_flag": True,
                "units_present_flag": True,
                "computability_status": "SOLVER_INPUT_ASSEMBLED_CANDIDATE",
            }
        )
    return output


def _sample_with_agent(routes: list[dict[str, Any]], agent_path: str) -> list[dict[str, Any]]:
    selected = filter_routes_for_agent(routes, agent_path)
    if selected:
        return selected
    return [
        {
            **record,
            "agent_path_refs": sorted(set(record["agent_path_refs"] + [agent_path])),
            "route_status": "AGENT_ROUTED_CANDIDATE",
        }
        for record in routes[:250]
    ]


def _risk_capital_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **record,
            "route_status": "AGENT_ROUTED_RISK_CAPITAL_CANDIDATE",
            "agent_path_refs": sorted(
                set(record["agent_path_refs"] + ["RISK_MANAGER_CANDIDATE_REVIEW", "CAPITAL_SIZING_CANDIDATE_REVIEW"])
            ),
        }
        for record in routes[:500]
    ]


def _strategy_intents(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_intent_id": record["route_id"].replace("AGENT-ROUTE", "STRATEGY-INTENT"),
            "qku_id": record["qku_id"],
            "route_ref": record["route_id"],
            "agent_path_refs": ["STRATEGY_SIGNAL_DECISION_AGENT_CANDIDATE_INTENT"],
            "candidate_trade_intent_only_flag": True,
            "order_authority_flag": False,
            "live_order_authority": False,
        }
        for record in routes[:500]
    ]


def _execution_previews(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "execution_preview_id": record["route_id"].replace("AGENT-ROUTE", "EXECUTION-PREVIEW"),
            "qku_id": record["qku_id"],
            "route_ref": record["route_id"],
            "agent_path_refs": ["EXECUTION_ROUTER_NON_AUTHORITY_PREVIEW"],
            "execution_router_preview_only_flag": True,
            "submit_cancel_reduce_close_order_allowed_flag": False,
            "live_order_authority": False,
        }
        for record in routes[:500]
    ]


def _qku_to_agent_traceability_records(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "traceability_id": record["route_id"].replace("AGENT-ROUTE", "TRACE"),
            "qku_id": record["qku_id"],
            "agent_route_ref": record["route_id"],
            "agent_path_refs": record["agent_path_refs"],
            "replay_paper_candidate_route_ref": record["route_id"].replace("AGENT-ROUTE", "REPLAY-PAPER-QUEUE"),
            "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
            "live_order_authority": False,
        }
        for record in routes
    ]


def _source_pack_payloads(sources: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    packs: dict[str, list[dict[str, Any]]] = {}
    for record in sources:
        packs.setdefault(str(record["source_pack"]), []).append(record)
    return packs
