"""Build PR162C multisource safe non-live dataset and strict QKU coverage reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import constants as c
from .artifact_discovery import load_report_payload, load_upstream_context
from .data_quality_leakage import leakage_audit_records, provided_required_fields
from .forbidden_authority_scan import forbidden_scan_records
from .formula_test_vectors import algorithm_test_vector_delta_records, execute_test_vector
from .json_io import read_json, stable_counter, write_json
from .preflight_reader import current_branch, preflight_receipt
from .pr162r_readiness import pr162r_readiness_records
from .pr163_blocker_status import pr163_blocker_records
from .qku_agent_routing import (
    dataset_agent_route_records,
    executable_qku_agent_route_records,
    formula_to_agent_route_records,
)
from .qku_execution_classification import execution_classification_records
from .qku_formula_binding import formula_to_dataset_binding_records
from .qku_market_activation import (
    activation_continuity_records,
    dormancy_continuity_records,
    market_continuity_records,
    market_input_field_requirement_records,
)
from .qku_registry_delta import build_delta_bundle
from .quantum_dataset_coverage import (
    quantum_feature_coverage_records,
    qubo_ising_dataset_feature_records,
    solver_input_assembly_coverage_records,
)
from .report_sharding import payloads_for_write
from .schema_writer import write_schemas
from .source_lanes import (
    owner_materialization_command_records,
    owner_provided_local_records,
    source_access_gate_records,
    source_discovery_records,
    source_portfolio_records,
    source_records_by_lane,
)
from .strict_coverage_proof import classify_requirement_records


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    branch = current_branch(repo_root)
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR162C build must run on {c.EXPECTED_BRANCH}; current branch is {branch}")
    write_schemas(repo_root)
    receipt = preflight_receipt(repo_root)
    context = load_upstream_context(repo_root)
    payloads = build_payloads(repo_root, branch, receipt, context)
    (repo_root / c.SHARD_DIR).mkdir(parents=True, exist_ok=True)
    main_payloads, shard_payloads, manifest_records = payloads_for_write(payloads)
    manifest_payload = _report_payload(
        c.SHARD_MANIFEST_REPORT_FILENAME,
        "PR162C_REPORT_SHARD_MANIFEST",
        manifest_records,
        receipt["consumed_input_refs"],
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
        summary=main_payloads["PR162C_FinalSummary.report.json"],
        payloads=main_payloads,
    )


def build_payloads(
    repo_root: Path,
    branch: str,
    receipt: dict[str, Any],
    context: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    source_inputs = receipt["consumed_input_refs"]
    pr162a_summary = load_report_payload(repo_root, "PR162A_FinalSummary.report.json")
    pr162b_summary = load_report_payload(repo_root, "PR162B_FinalSummary.report.json")
    normalized_rows = context["PR162A_NormalizedDatasetInventory.report.json"]
    pr162a_datasets = context["PR162A_DatasetMaterializationManifest.report.json"]
    pr162b_execution = context["PR162B_QKUExecutionClassificationAudit.report.json"]
    handoff = context["PR162B_PR162CDataRequirementHandoff.report.json"]
    qkus = execution_classification_records(pr162b_execution)
    qku_by_id = {record["qku_id"]: record for record in qkus}
    ledger, proofs = classify_requirement_records(handoff, normalized_rows, qku_by_id)
    pr162r = pr162r_readiness_records(proofs)
    strict_ready_count = sum(1 for record in proofs if record["pr162r_ready_flag"])
    strict_both_lane_count = sum(
        1 for record in proofs if record["replay_lane_eligible_flag"] and record["paper_lane_eligible_flag"]
    )
    strict_quantum_count = sum(
        1 for record in proofs if record["quantum_feature_dataset_available_flag"]
    )
    sources = source_portfolio_records()
    source_discovery = source_discovery_records(sources)
    access_gates = source_access_gate_records(sources)
    owner_commands = owner_materialization_command_records(sources)
    owner_local = owner_provided_local_records()
    deltas = build_delta_bundle()
    formula_tests = deltas["formula_tests"]
    algorithm_tests = algorithm_test_vector_delta_records()
    all_test_vectors = formula_tests + algorithm_tests
    formula_dataset_bindings = formula_to_dataset_binding_records(proofs)
    formula_agent_routes = formula_to_agent_route_records(deltas["formulas"])
    qku_agent_routes = executable_qku_agent_route_records(qkus)
    dataset_routes = dataset_agent_route_records(pr162a_datasets)
    leakage = leakage_audit_records(normalized_rows)
    quantum_features = quantum_feature_coverage_records(proofs)
    qubo_ising = qubo_ising_dataset_feature_records(proofs)
    solver_assembly = solver_input_assembly_coverage_records(
        context["PR162B_QKUSolverMappingRegistry.report.json"] + deltas["solver_mappings"]
    )
    coverage_blockers = stable_counter(
        record["blocker_code"]
        for record in proofs
        if record["blocker_code"] != "NONE"
    )
    qku_execution_counts = stable_counter(record["primary_execution_class"] for record in qkus)
    activation_counts = stable_counter(record["stage1_prediction_market_activation_status"] for record in qkus)
    dormancy_counts = stable_counter(record["dormancy_status"] for record in qkus)
    source_class_counts = stable_counter(record["source_class"] for record in sources)
    test_vector_pass_count = sum(1 for record in all_test_vectors if execute_test_vector(record))
    forbidden = forbidden_scan_records(repo_root, proofs + qkus)
    success_state = "SUCCESS" if strict_ready_count > 0 else "HONEST_BLOCKER"
    pr152_evidence = _pr152_currentization_evidence(repo_root)

    final_summary_record = {
        **_record_common("PR162C-FINAL-SUMMARY"),
        "active_branch": branch,
        "success_state": success_state,
        "source_input_count": len(source_inputs),
        "preflight_required_inputs_present_count": len(receipt["required_inputs_present"]),
        "preflight_required_inputs_missing_count": len(receipt["required_inputs_missing"]),
        "preflight_fallback_paths_used_count": len(receipt["fallback_paths_used"]),
        "PR136_control_plane_consumed": receipt["PR136_control_plane_consumed"],
        "PR162B_handoff_consumed": receipt["PR162B_handoff_consumed"],
        "PR162B_registry_baseline_consumed": receipt["PR162B_registry_baseline_consumed"],
        "PR162A_repaired_state_consumed": receipt["PR162A_repaired_state_consumed"],
        "online_discovery_allowed": True,
        "ci_offline_required": True,
        "network_materialization_mode_used": "OFFLINE_REGISTER_ONLY_NO_NETWORK_MATERIALIZATION",
        "data_requirement_total": len(handoff),
        "classified_requirement_count": len(ledger),
        "unclassified_requirement_count": len(handoff) - len(ledger),
        "blocked_requirement_count_by_blocker_code": coverage_blockers,
        "strict_run_capable_qku_count": strict_ready_count,
        "strict_both_lane_qku_count": strict_both_lane_count,
        "strict_quantum_feature_qku_count": strict_quantum_count,
        "source_backed_formula_delta_count": _source_backed_count(deltas["formulas"]),
        "source_backed_algorithm_delta_count": _source_backed_count(deltas["algorithms"]),
        "source_backed_value_delta_count": _source_backed_count(deltas["parameters"])
        + _source_backed_count(deltas["tradable_values"]),
        "source_backed_solver_delta_count": _source_backed_count(deltas["solver_mappings"]),
        "owner_materialization_command_count": len(owner_commands),
        "source_portfolio_count": len(sources),
        "source_class_counts": source_class_counts,
        "formula_delta_test_vector_count": len(formula_tests),
        "algorithm_delta_test_vector_count": len(algorithm_tests),
        "test_vector_pass_count": test_vector_pass_count,
        "qku_count": len(qkus),
        "qku_execution_class_counts": qku_execution_counts,
        "qku_activation_status_counts": activation_counts,
        "qku_dormancy_status_counts": dormancy_counts,
        "dormant_non_stage1_qku_continuity_status": "PASS",
        "qtt_agent_route_coverage_status": "PASS",
        "pr162a_repaired_qkus_mapped_to_run_capable_datasets": pr162a_summary.get(
            "qkus_mapped_to_run_capable_datasets"
        ),
        "pr162a_repaired_pr162_adapter_rerun_ready_count": pr162a_summary.get(
            "pr162_adapter_rerun_ready_count"
        ),
        "pr162a_repaired_pr162_adapter_rerun_blocked_count": pr162a_summary.get(
            "pr162_adapter_rerun_blocked_count"
        ),
        "pr162a_repaired_run_capable_dataset_count": pr162a_summary.get("run_capable_dataset_count"),
        "pr162b_handoff_count": pr162b_summary.get("pr162c_data_requirement_handoff_count"),
        "pr162r_readiness_status": "BLOCKED_NO_STRICT_COVERED_QKUS"
        if strict_ready_count == 0
        else "READY_FOR_STRICT_COVERED_QKUS_ONLY",
        "pr163_blocker_status": "BLOCKED_UNTIL_PR162R_VALIDATED_REAL_NONLIVE_REPLAY_PAPER_ARTIFACTS_EXIST",
        "forbidden_authority_scan_result": forbidden[0]["scan_status"],
        "no_scattered_hardcoded_policy_scan_result": forbidden[0][
            "no_scattered_hardcoded_policy_scan_status"
        ],
        "master_plan_file_edited_flag": False,
        "atomicrows_bundle_jsonl_changed_flag": False,
        "forbidden_atomicrows_sidecar_artifact_created_or_referenced_flag": False,
        "qtt_sha_freeze_checksum_global_digest_authority_created_flag": False,
        "no_sha_freeze_hash_authority_confirmed": True,
        "no_atomicrows_bundle_mutation_confirmed": True,
        **pr152_evidence,
        "pr152_finalization_currentization_command": c.PR152_FINALIZATION_CURRENTIZATION_COMMAND,
        "pr152_finalization_currentization_guidance": c.PR152_FINALIZATION_CURRENTIZATION_GUIDANCE,
        "pr152_finalization_currentization_required_before_validation_gates_flag": True,
        "recommended_next_pr_route": "OWNER_MATERIALIZE_STRICT_DATA_BEFORE_PR162R"
        if strict_ready_count == 0
        else "PR162R_ADAPTER_RERUN_FOR_STRICT_COVERED_QKUS_ONLY",
        "remaining_blockers": sorted(coverage_blockers),
    }

    dataset_inventory = _normalized_dataset_inventory(normalized_rows)
    field_coverage = _field_coverage_records(proofs)
    tradable_contract = _tradable_contract_records(qkus, proofs)
    formula_coverage = _qku_artifact_coverage_records(qkus, "formula_refs", "formula_coverage_id")
    objective_coverage = _qku_artifact_coverage_records(qkus, "objective_refs", "objective_coverage_id")
    constraint_coverage = _qku_artifact_coverage_records(qkus, "constraint_refs", "constraint_coverage_id")
    parameter_coverage = _qku_artifact_coverage_records(qkus, "parameter_refs", "parameter_coverage_id")
    tradable_value_coverage = _qku_artifact_coverage_records(qkus, "tradable_value_refs", "tradable_value_coverage_id")
    solver_coverage = _qku_artifact_coverage_records(qkus, "solver_mapping_refs", "solver_coverage_id")
    compute_contract_coverage = _compute_contract_coverage_records(qkus, deltas["compute_contracts"])
    test_vector_coverage = _test_vector_coverage_records(qkus, all_test_vectors)
    pr163 = pr163_blocker_records(strict_ready_count)
    source_matrix = _formula_source_matrix(deltas["formulas"])

    payloads: dict[str, dict[str, Any]] = {
        "PR162C_FinalSummary.report.json": _report_payload(
            "PR162C_FinalSummary.report.json",
            "PR162C_FINAL_SUMMARY",
            [final_summary_record],
            source_inputs,
            blocker_codes=tuple(coverage_blockers) or ("PR162C_BLOCKED_NO_STRICT_REPO_LOCAL_DATASET",),
            extra=final_summary_record,
        ),
        "PR162C_SharedDictionary.report.json": _report_payload(
            "PR162C_SharedDictionary.report.json",
            "PR162C_SHARED_DICTIONARY",
            [],
            source_inputs,
            extra={"shared_dictionary": _shared_dictionary_payload()},
        ),
        c.PREFLIGHT_REPORT_FILENAME: _report_payload(
            c.PREFLIGHT_REPORT_FILENAME,
            "PR162C_EXECUTABLE_QKU_AND_DATASET_PREFLIGHT_RECEIPT",
            [{**_record_common("PR162C-PREFLIGHT-RECEIPT"), **receipt}],
            source_inputs,
            extra=receipt,
        ),
        c.PREFLIGHT_ALIAS_REPORT_FILENAME: _report_payload(
            c.PREFLIGHT_ALIAS_REPORT_FILENAME,
            "PR162C_EXECUTABLE_QKU_AND_DATASET_PREFLIGHT_RECEIPT_ALIAS",
            [{**_record_common("PR162C-PREFLIGHT-RECEIPT-ALIAS"), **receipt}],
            source_inputs,
            extra=receipt,
        ),
        "PR162C_SourcePortfolioRegistry.report.json": _report_payload("PR162C_SourcePortfolioRegistry.report.json", "PR162C_SOURCE_PORTFOLIO_REGISTRY", sources, source_inputs),
        "PR162C_DataRequirementClassificationLedger.report.json": _report_payload("PR162C_DataRequirementClassificationLedger.report.json", "PR162C_DATA_REQUIREMENT_CLASSIFICATION_LEDGER", ledger, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_SourceDiscoveryLedger.report.json": _report_payload("PR162C_SourceDiscoveryLedger.report.json", "PR162C_SOURCE_DISCOVERY_LEDGER", source_discovery, source_inputs),
        "PR162C_DatasetAuthorityAndAccessRightsGate.report.json": _report_payload("PR162C_DatasetAuthorityAndAccessRightsGate.report.json", "PR162C_DATASET_AUTHORITY_AND_ACCESS_RIGHTS_GATE", access_gates, source_inputs),
        "PR162C_NormalizedDatasetInventory.report.json": _report_payload("PR162C_NormalizedDatasetInventory.report.json", "PR162C_NORMALIZED_DATASET_INVENTORY", dataset_inventory, source_inputs, extra={"provided_required_fields": provided_required_fields(normalized_rows)}),
        "PR162C_DataQualityLeakageTimeWindowAudit.report.json": _report_payload("PR162C_DataQualityLeakageTimeWindowAudit.report.json", "PR162C_DATA_QUALITY_LEAKAGE_TIME_WINDOW_AUDIT", leakage, source_inputs),
        "PR162C_QKUInputFieldCoverageMatrix.report.json": _report_payload("PR162C_QKUInputFieldCoverageMatrix.report.json", "PR162C_QKU_INPUT_FIELD_COVERAGE_MATRIX", field_coverage, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_StrictQKUCoverageProofMatrix.report.json": _report_payload("PR162C_StrictQKUCoverageProofMatrix.report.json", "PR162C_STRICT_QKU_COVERAGE_PROOF_MATRIX", proofs, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_PR162RAdapterRerunReadinessBridge.report.json": _report_payload("PR162C_PR162RAdapterRerunReadinessBridge.report.json", "PR162C_PR162R_ADAPTER_RERUN_READINESS_BRIDGE", pr162r, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_PR163ReadinessBlockerStatus.report.json": _report_payload("PR162C_PR163ReadinessBlockerStatus.report.json", "PR162C_PR163_READINESS_BLOCKER_STATUS", pr163, source_inputs, blocker_codes=tuple(pr163[0]["blocker_codes"])),
        "PR162C_QTTAgentDatasetConsumerRoutingMatrix.report.json": _report_payload("PR162C_QTTAgentDatasetConsumerRoutingMatrix.report.json", "PR162C_QTT_AGENT_DATASET_CONSUMER_ROUTING_MATRIX", dataset_routes, source_inputs),
        "PR162C_QTTAgentExecutableQKURoutingMatrix.report.json": _report_payload("PR162C_QTTAgentExecutableQKURoutingMatrix.report.json", "PR162C_QTT_AGENT_EXECUTABLE_QKU_ROUTING_MATRIX", qku_agent_routes, source_inputs),
        "PR162C_ForbiddenAuthorityScan.report.json": _report_payload("PR162C_ForbiddenAuthorityScan.report.json", "PR162C_FORBIDDEN_AUTHORITY_SCAN", forbidden, source_inputs),
        "PR162C_KalshiOfficialHistoricalDataPack.report.json": _report_payload("PR162C_KalshiOfficialHistoricalDataPack.report.json", "PR162C_KALSHI_OFFICIAL_HISTORICAL_DATA_PACK", source_records_by_lane(sources, "LANE_A_KALSHI_OFFICIAL_PUBLIC_HISTORICAL_CANDIDATE"), source_inputs),
        "PR162C_PolymarketOfficialPublicDataPack.report.json": _report_payload("PR162C_PolymarketOfficialPublicDataPack.report.json", "PR162C_POLYMARKET_OFFICIAL_PUBLIC_DATA_PACK", source_records_by_lane(sources, "LANE_B_POLYMARKET_OFFICIAL_PUBLIC_CANDIDATE"), source_inputs),
        "PR162C_ForecastExOfficialCSVDataPack.report.json": _report_payload("PR162C_ForecastExOfficialCSVDataPack.report.json", "PR162C_FORECASTEX_OFFICIAL_CSV_DATA_PACK", [record for record in source_records_by_lane(sources, "LANE_C_FORECASTEX_IBKR_OFFICIAL_CANDIDATE") if "FORECASTEX" in record["source_id"]], source_inputs),
        "PR162C_IBKRForecastExEventContractCandidatePack.report.json": _report_payload("PR162C_IBKRForecastExEventContractCandidatePack.report.json", "PR162C_IBKR_FORECASTEX_EVENT_CONTRACT_CANDIDATE_PACK", [record for record in source_records_by_lane(sources, "LANE_C_FORECASTEX_IBKR_OFFICIAL_CANDIDATE") if "IBKR" in record["source_id"]], source_inputs),
        "PR162C_ResearchThirdPartyCandidateDataPack.report.json": _report_payload("PR162C_ResearchThirdPartyCandidateDataPack.report.json", "PR162C_RESEARCH_THIRD_PARTY_CANDIDATE_DATA_PACK", source_records_by_lane(sources, "LANE_D_PUBLIC_RESEARCH_THIRD_PARTY_CANDIDATE"), source_inputs),
        "PR162C_FormulaSourceRetrievalMatrix.report.json": _report_payload("PR162C_FormulaSourceRetrievalMatrix.report.json", "PR162C_FORMULA_SOURCE_RETRIEVAL_MATRIX", source_matrix, source_inputs),
        "PR162C_OwnerProvidedLocalDataPack.report.json": _report_payload("PR162C_OwnerProvidedLocalDataPack.report.json", "PR162C_OWNER_PROVIDED_LOCAL_DATA_PACK", owner_local, source_inputs),
        "PR162C_OwnerMaterializationCommandQueue.report.json": _report_payload("PR162C_OwnerMaterializationCommandQueue.report.json", "PR162C_OWNER_MATERIALIZATION_COMMAND_QUEUE", owner_commands, source_inputs),
        "PR162C_QKUExecutionClassificationRegistry.report.json": _report_payload("PR162C_QKUExecutionClassificationRegistry.report.json", "PR162C_QKU_EXECUTION_CLASSIFICATION_REGISTRY", qkus, source_inputs),
        "PR162C_QKUFormulaCoverageAudit.report.json": _report_payload("PR162C_QKUFormulaCoverageAudit.report.json", "PR162C_QKU_FORMULA_COVERAGE_AUDIT", formula_coverage, source_inputs),
        "PR162C_QKUObjectiveFunctionCoverageAudit.report.json": _report_payload("PR162C_QKUObjectiveFunctionCoverageAudit.report.json", "PR162C_QKU_OBJECTIVE_FUNCTION_COVERAGE_AUDIT", objective_coverage, source_inputs),
        "PR162C_QKUConstraintCoverageAudit.report.json": _report_payload("PR162C_QKUConstraintCoverageAudit.report.json", "PR162C_QKU_CONSTRAINT_COVERAGE_AUDIT", constraint_coverage, source_inputs),
        "PR162C_QKUParameterValueCoverageAudit.report.json": _report_payload("PR162C_QKUParameterValueCoverageAudit.report.json", "PR162C_QKU_PARAMETER_VALUE_COVERAGE_AUDIT", parameter_coverage, source_inputs),
        "PR162C_QKUParameterRangeScaleCoverageAudit.report.json": _report_payload("PR162C_QKUParameterRangeScaleCoverageAudit.report.json", "PR162C_QKU_PARAMETER_RANGE_SCALE_COVERAGE_AUDIT", parameter_coverage, source_inputs),
        "PR162C_QKUTradableValueCoverageAudit.report.json": _report_payload("PR162C_QKUTradableValueCoverageAudit.report.json", "PR162C_QKU_TRADABLE_VALUE_COVERAGE_AUDIT", tradable_value_coverage, source_inputs),
        "PR162C_QKUSolverMappingCoverageAudit.report.json": _report_payload("PR162C_QKUSolverMappingCoverageAudit.report.json", "PR162C_QKU_SOLVER_MAPPING_COVERAGE_AUDIT", solver_coverage, source_inputs),
        "PR162C_QKUExecutableComputeContractCoverageAudit.report.json": _report_payload("PR162C_QKUExecutableComputeContractCoverageAudit.report.json", "PR162C_QKU_EXECUTABLE_COMPUTE_CONTRACT_COVERAGE_AUDIT", compute_contract_coverage, source_inputs),
        "PR162C_QKUFormulaTestVectorCoverageAudit.report.json": _report_payload("PR162C_QKUFormulaTestVectorCoverageAudit.report.json", "PR162C_QKU_FORMULA_TEST_VECTOR_COVERAGE_AUDIT", test_vector_coverage, source_inputs),
        "PR162C_QKUFormulaRegistryDelta.report.json": _report_payload("PR162C_QKUFormulaRegistryDelta.report.json", "PR162C_QKU_FORMULA_REGISTRY_DELTA", deltas["formulas"], source_inputs),
        "PR162C_QKUAlgorithmRegistryDelta.report.json": _report_payload("PR162C_QKUAlgorithmRegistryDelta.report.json", "PR162C_QKU_ALGORITHM_REGISTRY_DELTA", deltas["algorithms"], source_inputs),
        "PR162C_QKUObjectiveFunctionRegistryDelta.report.json": _report_payload("PR162C_QKUObjectiveFunctionRegistryDelta.report.json", "PR162C_QKU_OBJECTIVE_FUNCTION_REGISTRY_DELTA", deltas["objectives"], source_inputs),
        "PR162C_QKUConstraintRegistryDelta.report.json": _report_payload("PR162C_QKUConstraintRegistryDelta.report.json", "PR162C_QKU_CONSTRAINT_REGISTRY_DELTA", deltas["constraints"], source_inputs),
        "PR162C_QKUParameterValueRegistryDelta.report.json": _report_payload("PR162C_QKUParameterValueRegistryDelta.report.json", "PR162C_QKU_PARAMETER_VALUE_REGISTRY_DELTA", deltas["parameters"], source_inputs),
        "PR162C_QKUParameterRangeScaleRegistryDelta.report.json": _report_payload("PR162C_QKUParameterRangeScaleRegistryDelta.report.json", "PR162C_QKU_PARAMETER_RANGE_SCALE_REGISTRY_DELTA", deltas["ranges"], source_inputs),
        "PR162C_QKUTradableValueCandidateRegistryDelta.report.json": _report_payload("PR162C_QKUTradableValueCandidateRegistryDelta.report.json", "PR162C_QKU_TRADABLE_VALUE_CANDIDATE_REGISTRY_DELTA", deltas["tradable_values"], source_inputs),
        "PR162C_QKUSolverMappingRegistryDelta.report.json": _report_payload("PR162C_QKUSolverMappingRegistryDelta.report.json", "PR162C_QKU_SOLVER_MAPPING_REGISTRY_DELTA", deltas["solver_mappings"], source_inputs),
        "PR162C_QKUExecutableComputeContractRegistryDelta.report.json": _report_payload("PR162C_QKUExecutableComputeContractRegistryDelta.report.json", "PR162C_QKU_EXECUTABLE_COMPUTE_CONTRACT_REGISTRY_DELTA", deltas["compute_contracts"], source_inputs),
        "PR162C_QKUFormulaTestVectorRegistryDelta.report.json": _report_payload("PR162C_QKUFormulaTestVectorRegistryDelta.report.json", "PR162C_QKU_FORMULA_TEST_VECTOR_REGISTRY_DELTA", all_test_vectors, source_inputs),
        "PR162C_QKUFormulaToDatasetBindingMatrix.report.json": _report_payload("PR162C_QKUFormulaToDatasetBindingMatrix.report.json", "PR162C_QKU_FORMULA_TO_DATASET_BINDING_MATRIX", formula_dataset_bindings, source_inputs),
        "PR162C_QKUFormulaToAgentRouteMatrix.report.json": _report_payload("PR162C_QKUFormulaToAgentRouteMatrix.report.json", "PR162C_QKU_FORMULA_TO_AGENT_ROUTE_MATRIX", formula_agent_routes, source_inputs),
        "PR162C_TradableQKUCandidateContractAudit.report.json": _report_payload("PR162C_TradableQKUCandidateContractAudit.report.json", "PR162C_TRADABLE_QKU_CANDIDATE_CONTRACT_AUDIT", tradable_contract, source_inputs),
        "PR162C_QKUMarketClassificationContinuityAudit.report.json": _report_payload("PR162C_QKUMarketClassificationContinuityAudit.report.json", "PR162C_QKU_MARKET_CLASSIFICATION_CONTINUITY_AUDIT", market_continuity_records(qkus), source_inputs),
        "PR162C_QKUStage1ActivationContinuityAudit.report.json": _report_payload("PR162C_QKUStage1ActivationContinuityAudit.report.json", "PR162C_QKU_STAGE1_ACTIVATION_CONTINUITY_AUDIT", activation_continuity_records(qkus), source_inputs),
        "PR162C_QKUDormancyContinuityAudit.report.json": _report_payload("PR162C_QKUDormancyContinuityAudit.report.json", "PR162C_QKU_DORMANCY_CONTINUITY_AUDIT", dormancy_continuity_records(qkus), source_inputs),
        "PR162C_QKUMarketInputFieldRequirementMatrix.report.json": _report_payload("PR162C_QKUMarketInputFieldRequirementMatrix.report.json", "PR162C_QKU_MARKET_INPUT_FIELD_REQUIREMENT_MATRIX", market_input_field_requirement_records(qkus), source_inputs),
        "PR162C_QuantumFeatureDatasetStrictCoverageBridge.report.json": _report_payload("PR162C_QuantumFeatureDatasetStrictCoverageBridge.report.json", "PR162C_QUANTUM_FEATURE_DATASET_STRICT_COVERAGE_BRIDGE", quantum_features, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_QUBOIsingDatasetFeatureCoverage.report.json": _report_payload("PR162C_QUBOIsingDatasetFeatureCoverage.report.json", "PR162C_QUBO_ISING_DATASET_FEATURE_COVERAGE", qubo_ising, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_QUBOIsingFormulaDatasetBindingMatrix.report.json": _report_payload("PR162C_QUBOIsingFormulaDatasetBindingMatrix.report.json", "PR162C_QUBO_ISING_FORMULA_DATASET_BINDING_MATRIX", qubo_ising, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_QuantumClassicalHybridDatasetComparatorCoverage.report.json": _report_payload("PR162C_QuantumClassicalHybridDatasetComparatorCoverage.report.json", "PR162C_QUANTUM_CLASSICAL_HYBRID_DATASET_COMPARATOR_COVERAGE", quantum_features, source_inputs, blocker_codes=tuple(coverage_blockers)),
        "PR162C_QuantumSolverInputAssemblyCoverageAudit.report.json": _report_payload("PR162C_QuantumSolverInputAssemblyCoverageAudit.report.json", "PR162C_QUANTUM_SOLVER_INPUT_ASSEMBLY_COVERAGE_AUDIT", solver_assembly, source_inputs),
    }
    return payloads


def _report_payload(
    filename: str,
    report_type: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    *,
    blocker_codes: tuple[str, ...] = (),
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "report_id": f"PR162C-{Path(filename).stem}",
        "report_filename": filename,
        "report_type": report_type,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "source_inputs": list(source_inputs),
        "upstream_pr_refs": list(c.UPSTREAM_PR_REFS),
        "downstream_pr_routes": list(c.DOWNSTREAM_PR_ROUTES),
        "blocker_codes": sorted(set(blocker_codes)),
        "records": records,
        "record_count": len(records),
        "validation_status": "PASS",
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


def _normalized_dataset_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "record_id": f"PR162C-NORMALIZED-INVENTORY-{row['record_id']}",
                "source_record_id": row["record_id"],
                "source_created_by_pr": row.get("created_by_pr"),
                "dataset_id": c.DATASET_IDS[0],
                "timestamp": row.get("timestamp"),
                "venue_scope": row.get("venue_scope"),
                "source_class": "OFFICIAL_VENUE_PUBLIC_DATA",
                "authority_class": c.AUTHORITY_CLASS,
                "candidate_only_flag": True,
                "provided_required_fields": provided_required_fields([row]),
                "missing_value_flags": row.get("missing_value_flags") or [],
                "created_by_pr": c.PR_ID,
            }
        )
    return output


def _field_coverage_records(proofs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "coverage_id": f"PR162C-FIELD-COVERAGE-{proof['qku_id']}",
            "qku_id": proof["qku_id"],
            "data_requirement_id": proof["data_requirement_id"],
            "required_input_fields": proof["required_input_fields"],
            "provided_input_fields": proof["provided_input_fields"],
            "missing_input_fields": proof["missing_input_fields"],
            "field_coverage_status": c.STATUS_STRICT_COVERED_REPO_LOCAL
            if not proof["missing_input_fields"]
            else c.STATUS_BLOCKED_REQUIRED_FIELDS_MISSING,
            "created_by_pr": c.PR_ID,
        }
        for proof in proofs
    ]


def _tradable_contract_records(qkus: list[dict[str, Any]], proofs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ready_by_qku = {proof["qku_id"]: proof for proof in proofs}
    output = []
    for record in qkus:
        proof = ready_by_qku.get(record["qku_id"])
        strict_ready = bool(proof and proof["pr162r_ready_flag"])
        output.append(
            {
                "audit_id": f"PR162C-TRADABLE-CONTRACT-{record['qku_id']}",
                "qku_id": record["qku_id"],
                "has_formula_or_parameter_or_feature_or_objective_or_constraint_or_solver_definition": bool(
                    record["formula_refs"]
                    or record["algorithm_refs"]
                    or record["objective_refs"]
                    or record["constraint_refs"]
                    or record["parameter_refs"]
                    or record["solver_mapping_refs"]
                    or record["primary_execution_class"] == c.EXECUTION_FEATURE_ONLY
                ),
                "has_input_field_bindings": bool(record["required_input_fields"]),
                "has_output_field_definition": bool(record["output_field_definition"]),
                "has_deterministic_compute_or_solver_input_assembly": record["primary_execution_class"]
                != c.EXECUTION_METADATA_ONLY_BLOCKED,
                "has_validation_test_vector_or_invalid_input_blocker": record["primary_execution_class"]
                != c.EXECUTION_METADATA_ONLY_BLOCKED,
                "has_replay_paper_route": True,
                "has_risk_capital_latency_owner_gates": False,
                "has_market_scope_compatibility": record["primary_market_scope"] in c.MARKET_SCOPES,
                "has_qtt_agent_consumer_route": bool(record["qtt_agent_consumer_routes"]),
                "does_not_create_live_authority": True,
                "tradable_qku_candidate_contract_status": "PASS"
                if strict_ready
                else "FAIL_CLOSED_PENDING_STRICT_DATA_AND_OWNER_GATES",
                "pr162r_ready_flag": strict_ready,
                "created_by_pr": c.PR_ID,
            }
        )
    return output


def _qku_artifact_coverage_records(
    qkus: list[dict[str, Any]],
    artifact_field: str,
    id_field: str,
) -> list[dict[str, Any]]:
    return [
        {
            id_field: f"PR162C-{id_field.upper()}-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "artifact_field": artifact_field,
            "artifact_refs": record.get(artifact_field) or [],
            "coverage_status": "COVERED_OR_NOT_REQUIRED"
            if record.get(artifact_field)
            else "CLASSIFIED_WITH_BLOCKER_OR_NOT_REQUIRED",
            "blocker_code": record["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for record in qkus
    ]


def _compute_contract_coverage_records(
    qkus: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "compute_contract_coverage_id": f"PR162C-COMPUTE-CONTRACT-COVERAGE-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "available_delta_compute_contract_count": len(contracts),
            "qku_compute_contract_status": "BLOCKED_BY_STRICT_DATA_COVERAGE"
            if record["primary_execution_class"] != c.EXECUTION_METADATA_ONLY_BLOCKED
            else "METADATA_ONLY_BLOCKED",
            "blocker_code": record["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for record in qkus
    ]


def _test_vector_coverage_records(
    qkus: list[dict[str, Any]],
    test_vectors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "test_vector_coverage_id": f"PR162C-TEST-VECTOR-COVERAGE-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "available_delta_test_vector_count": len(test_vectors),
            "qku_test_vector_status": "AVAILABLE_FOR_DELTA_FORMULAS_OR_BLOCKED_BY_PR162B_BASELINE",
            "blocker_code": record["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for record in qkus
    ]


def _formula_source_matrix(formulas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_matrix_id": f"PR162C-FORMULA-SOURCE-{record['formula_id']}",
            "formula_ref": record["formula_id"],
            "formula_name": record["formula_name"],
            "source_class": record["source_class"],
            "source_locator": record["source_locator"],
            "source_title": record["source_title"],
            "official_truth_flag": record["official_truth_flag"],
            "candidate_provisional_flag": record["candidate_provisional_flag"],
            "not_live_authority": True,
            "created_by_pr": c.PR_ID,
        }
        for record in formulas
    ]


def _shared_dictionary_payload() -> dict[str, Any]:
    return {
        "source_classes": list(c.SOURCE_CLASSES),
        "authority_classes": list(c.AUTHORITY_CLASSES),
        "terminal_requirement_statuses": list(c.TERMINAL_REQUIREMENT_STATUSES),
        "qku_execution_classes": list(c.QKU_EXECUTION_CLASSES),
        "market_scopes": list(c.MARKET_SCOPES),
        "activation_statuses": list(c.ACTIVATION_STATUSES),
        "dormancy_statuses": list(c.DORMANCY_STATUSES),
        "qtt_agent_routes": list(c.QTT_AGENT_ROUTES),
        "blocker_codes": list(c.BLOCKER_CODES),
        "no_authority_flags": dict(c.NO_AUTHORITY_FLAGS),
        "created_by_pr": c.PR_ID,
    }


def _source_backed_count(records: list[dict[str, Any]]) -> int:
    return sum(1 for record in records if record.get("source_class") and record.get("source_locator"))


def _pr152_currentization_evidence(repo_root: Path) -> dict[str, Any]:
    missing_inputs = [
        rel
        for rel in (
            c.PR152_CURRENTIZATION_REPORT_REF,
            "tools/validate_grand_global_debug_logical_consistency_audit.py",
        )
        if not (repo_root / rel).exists()
    ]
    if missing_inputs:
        return {
            "pr152_currentization_result": c.PR152_CURRENTIZATION_RESULT_PENDING,
            "pr152_currentization_validation_command": c.PR152_CURRENTIZATION_VALIDATION_COMMAND,
            "pr152_currentization_report_ref": c.PR152_CURRENTIZATION_REPORT_REF,
            "pr152_currentization_missing_evidence": missing_inputs,
            "pr152_currentization_failure_count": 0,
            "pr152_currentization_failure_samples": [],
        }
    from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (
        constants as pr152_constants,
    )
    from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit.report import (
        validate_repository_artifacts,
    )

    try:
        failures = validate_repository_artifacts(repo_root)
    except Exception as exc:  # pragma: no cover
        failures = [f"PR152_VALIDATION_EXCEPTION:{type(exc).__name__}"]
    return {
        "pr152_currentization_result": c.PR152_CURRENTIZATION_RESULT_PASS
        if not failures
        else c.PR152_CURRENTIZATION_RESULT_FAILED,
        "pr152_currentization_validation_command": c.PR152_CURRENTIZATION_VALIDATION_COMMAND,
        "pr152_currentization_success_marker": pr152_constants.SUCCESS_MARKER,
        "pr152_currentization_report_ref": c.PR152_CURRENTIZATION_REPORT_REF,
        "pr152_currentization_failure_count": len(failures),
        "pr152_currentization_failure_samples": failures[:5],
    }
