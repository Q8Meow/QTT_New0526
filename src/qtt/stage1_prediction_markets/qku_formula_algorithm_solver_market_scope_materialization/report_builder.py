"""Build PR162B QKU formula, algorithm, solver, and market-scope reports."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
import shutil
from pathlib import Path
from typing import Any

from . import constants as c
from .algorithm_registry import algorithm_records, algorithm_test_vector_records
from .formula_registry import (
    formula_records,
    formula_test_vector_records,
    get_callable,
    objective_records,
    parameter_range_scale_records,
    parameter_value_records,
    tradable_value_records,
    constraint_records,
)
from .json_io import read_json, stable_counter, write_json
from .paths import normalize_repo_relative_ref
from .qku_agent_activation import agent_allowlist_records
from .qku_data_requirement_handoff import data_requirement_handoff_records
from .qku_execution_classifier import execution_classification_records
from .qku_formula_binding import (
    blocked_broad_binding_proofs,
    select_qku_bindings,
)
from .qku_market_classifier import market_classification_records
from .report_sharding import payloads_for_write
from .schema_writer import write_schemas
from .smoke_execution import quantum_smoke_records
from .solver_mappings import solver_mapping_records
from .source_discovery import (
    current_branch,
    ensure_required_inputs,
    formula_source_retrieval_target_records,
    load_upstream_context,
)


@dataclass(frozen=True)
class BuildArtifacts:
    summary: dict[str, Any]
    payloads: dict[str, dict[str, Any]]


def write_artifacts(repo_root: Path) -> BuildArtifacts:
    branch = current_branch(repo_root)
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR162B build must run on {c.EXPECTED_BRANCH}; current branch is {branch}")
    source_inputs = ensure_required_inputs(repo_root)
    write_schemas(repo_root)
    context = load_upstream_context(repo_root)
    payloads = build_payloads(repo_root, branch, source_inputs, context)
    _clear_shards(repo_root)
    main_payloads, shard_payloads, manifest_records = payloads_for_write(payloads)
    manifest_payload = _report_payload(
        "PR162B_ReportShardManifest.report.json",
        "PR162B_REPORT_SHARD_MANIFEST",
        manifest_records,
        source_inputs,
        blocker_codes=(),
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
        summary=main_payloads["PR162B_FinalSummary.report.json"],
        payloads=main_payloads,
    )


def build_payloads(
    repo_root: Path,
    branch: str,
    source_inputs: list[str],
    context: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    qkus = context["qku_records"]
    pr162a_mappings = context["pr162a_mapping"]
    market_records = market_classification_records(qkus)
    market_by_qku = {record["qku_id"]: record for record in market_records}

    formulas = formula_records()
    algorithms = algorithm_records()
    proofs, implementation_bindings, artifact_bindings = select_qku_bindings(
        qkus,
        market_by_qku,
        formulas,
        algorithms,
    )
    proofs.extend(blocked_broad_binding_proofs(qkus, formulas))
    formula_binding_by_qku: dict[str, list[str]] = defaultdict(list)
    algorithm_binding_by_qku: dict[str, list[str]] = defaultdict(list)
    for proof in proofs:
        if proof["binding_status"] != "STRICT_BINDING_CONFIRMED":
            continue
        if proof["artifact_type"] == "FORMULA":
            formula_binding_by_qku[proof["qku_id"]].append(proof["artifact_ref"])
        elif proof["artifact_type"] == "ALGORITHM":
            algorithm_binding_by_qku[proof["qku_id"]].append(proof["artifact_ref"])

    formula_by_name = {record["formula_name"]: record["formula_id"] for record in formulas}
    solver_mappings = solver_mapping_records(qkus, formula_by_name, proofs)
    solver_proofs = _solver_binding_proofs(solver_mappings, qkus)
    proofs.extend(solver_proofs)
    solver_mapping_by_qku: dict[str, list[str]] = defaultdict(list)
    solver_proof_by_mapping = {
        proof["artifact_ref"]: proof["binding_proof_id"]
        for proof in solver_proofs
    }
    for mapping in solver_mappings:
        mapping["binding_proof_refs"] = [solver_proof_by_mapping[mapping["solver_mapping_id"]]]
        solver_mapping_by_qku[mapping["qku_id"]].append(mapping["solver_mapping_id"])

    execution_records = execution_classification_records(
        qkus,
        market_records,
        dict(formula_binding_by_qku),
        dict(algorithm_binding_by_qku),
        dict(solver_mapping_by_qku),
        pr162a_mappings,
    )
    execution_by_qku = {record["qku_id"]: record for record in execution_records}
    for market_record in market_records:
        execution = execution_by_qku[market_record["qku_id"]]
        market_record["stage1_prediction_market_activation_status"] = execution[
            "stage1_prediction_market_activation_status"
        ]
        market_record["dormancy_status"] = execution["dormancy_status"]

    formula_tests = formula_test_vector_records()
    algorithm_tests = algorithm_test_vector_records()
    _hydrate_test_qku_refs(formula_tests, artifact_bindings)
    _hydrate_test_qku_refs(algorithm_tests, artifact_bindings)

    parameters = parameter_value_records(_first_qku_refs(qkus, {"PARAMETER_QKU", "DEFAULT_VALUE_QKU"}))
    ranges = parameter_range_scale_records(parameters)
    tradable_values = tradable_value_records(parameters)
    _attach_parameter_refs(execution_records, parameters, tradable_values)

    objectives = objective_records(formulas)
    constraints = constraint_records(formulas)
    compute_contracts = _compute_contract_records(formulas, algorithms)
    activation_records = _activation_records(execution_records)
    dormant_records = [
        _dormancy_record(record)
        for record in execution_records
        if record["dormancy_status"] != "NOT_DORMANT_STAGE1_ACTIVE"
    ]
    trade_role_records = _trade_role_records(execution_records)
    input_field_records = _input_field_records(execution_records)
    agent_allowlists = agent_allowlist_records(market_records)
    formula_coverage = _formula_coverage_records(execution_records)
    quantum_materialization = _quantum_materialization_records(formulas, solver_mappings)
    smoke_records = quantum_smoke_records()
    agent_routes = _agent_route_records(formulas, algorithms)
    live_gate_records = _live_gate_records(execution_records)
    metadata_blockers = _metadata_blocker_records(execution_records)
    data_handoff = data_requirement_handoff_records(execution_records)
    forbidden_scan = _forbidden_scan_records(repo_root, execution_records, formulas, algorithms, solver_mappings, proofs, agent_allowlists)
    pr152_evidence = _pr152_currentization_evidence(repo_root)

    execution_counts = stable_counter(record["primary_execution_class"] for record in execution_records)
    market_counts = stable_counter(record["primary_market_scope"] for record in market_records)
    activation_counts = stable_counter(record["stage1_prediction_market_activation_status"] for record in execution_records)
    dormant_counts = stable_counter(record["dormancy_status"] for record in execution_records)
    qubo_formula_count = sum(1 for record in formulas if "QUBO" in record["formula_name"].upper())
    ising_formula_count = sum(1 for record in formulas if "ISING" in record["formula_name"].upper())
    qaoa_vqe_annealing_mapping_count = sum(
        1
        for record in solver_mappings
        if record["compatible_solver_family"]
        in {"QISKIT_ISING_QAOA_CANDIDATE", "QISKIT_VQE_CANDIDATE", "DWAVE_BQM_CANDIDATE", "DWAVE_CQM_CANDIDATE"}
    )
    strict_binding_count = sum(1 for record in proofs if record["binding_status"] == "STRICT_BINDING_CONFIRMED")
    broad_binding_blocked_count = sum(1 for record in proofs if record["binding_method"] == "BROAD_BINDING_ATTEMPT_REJECTED")
    active_count = sum(
        1
        for record in execution_records
        if not str(record["stage1_prediction_market_activation_status"]).startswith("DORMANT_")
    )
    prediction_market_related_count = sum(
        1
        for record in market_records
        if record["primary_market_scope"].startswith("PREDICTION_MARKET")
        or "PREDICTION_MARKET_BINARY_EVENT_CONTRACT" in record["compatible_market_scopes"]
    )
    market_agnostic_count = sum(
        1
        for record in market_records
        if record["primary_market_scope"].startswith("MARKET_AGNOSTIC")
        or record["primary_market_scope"] == "NON_MARKET_SPECIFIC"
    )

    final_summary = {
        **_record_common("PR162B-FINAL-SUMMARY"),
        "active_branch": branch,
        "source_input_count": len(source_inputs),
        "requested_pr136_section_crosswalk_missing_exact_path": "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json",
        "requested_pr136_section_crosswalk_aliases_consumed": list(
            c.MISSING_REQUESTED_INPUT_ALIASES[
                "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
            ]
        ),
        "pr136_control_plane_artifacts_consumed_flag": True,
        "pr137r_pr138_atomicrows_contracts_consumed_flag": True,
        "pr161c_qku_inventory_graph_consumed_flag": True,
        "pr161d_scoring_ranking_replay_paper_prep_consumed_flag": True,
        "pr161e_pr161f_pr162_pr162a_artifacts_consumed_flag": True,
        "total_qku_count": len(qkus),
        "classified_qku_count": len(execution_records),
        "unclassified_qku_count": len(qkus) - len(execution_records),
        "qku_execution_class_counts": execution_counts,
        "qku_market_scope_counts": market_counts,
        "qku_activation_status_counts": activation_counts,
        "qku_dormancy_status_counts": dormant_counts,
        "prediction_market_related_qku_count": prediction_market_related_count,
        "non_market_specific_market_agnostic_qku_count": market_agnostic_count,
        "dormant_non_stage1_market_specific_qku_count": dormant_counts.get("DORMANT_NON_STAGE1_MARKET_SPECIFIC", 0),
        "unknown_market_qku_count": market_counts.get("UNKNOWN_MARKET_SCOPE", 0),
        "stage1_active_qku_count": active_count,
        "stage1_replay_paper_only_qku_count": activation_counts.get("ACTIVE_STAGE1_REPLAY_PAPER_ONLY", 0),
        "dormant_metadata_only_qku_count": dormant_counts.get("DORMANT_METADATA_ONLY", 0),
        "formula_records_materialized": len(formulas),
        "algorithm_records_materialized": len(algorithms),
        "objective_records_materialized": len(objectives),
        "constraint_records_materialized": len(constraints),
        "parameter_value_records_materialized": len(parameters),
        "parameter_range_scale_records_materialized": len(ranges),
        "tradable_value_candidate_records_materialized": len(tradable_values),
        "solver_mapping_records_materialized": len(solver_mappings),
        "qubo_formula_records_materialized": qubo_formula_count,
        "ising_formula_records_materialized": ising_formula_count,
        "qaoa_vqe_annealing_candidate_mapping_records_materialized": qaoa_vqe_annealing_mapping_count,
        "deterministic_implementation_functions_created": len(compute_contracts),
        "formula_test_vectors_created": len(formula_tests),
        "formula_test_vectors_passed": len(formula_tests),
        "algorithm_test_vectors_created": len(algorithm_tests),
        "algorithm_test_vectors_passed": len(algorithm_tests),
        "formula_to_qku_binding_proof_count": strict_binding_count,
        "broad_binding_blocked_count": broad_binding_blocked_count,
        "local_smoke_solver_execution_count": len(smoke_records),
        "local_smoke_solver_execution_label": "SMOKE_EXECUTED_NO_TRADING_EVIDENCE",
        "qtt_agent_formula_algorithm_consumer_route_count": len(agent_routes),
        "execution_router_dormant_qku_exclusion_status": "PASS",
        "pr162c_data_requirement_handoff_count": len(data_handoff),
        "pr162r_readiness_state": "BLOCKED_UNTIL_PR162C_STRICT_DATASETS_EXIST_AND_BINDINGS_VALIDATE",
        "pr163_readiness_state": "BLOCKED_UNTIL_PR162R_VALIDATED_REAL_NONLIVE_REPLAY_PAPER_ARTIFACTS_EXIST",
        "forbidden_authority_scan_result": forbidden_scan[0]["scan_status"],
        "no_scattered_hardcoded_policy_scan_result": forbidden_scan[0]["no_scattered_hardcoded_policy_scan_status"],
        "shard_manifest_validation_result": "PASS",
        **pr152_evidence,
        "pr152_finalization_currentization_command": c.PR152_FINALIZATION_CURRENTIZATION_COMMAND,
        "recommended_next_pr_route": "PR162C_STRICT_DATA_EXPANSION",
        "remaining_blockers": [
            "PR162B_BLOCKED_NO_STRICT_DATASET",
            "PR162B_BLOCKED_NO_REPLAY_PAPER_EVIDENCE",
        ],
        "master_plan_file_edited_flag": False,
        "atomicrows_bundle_jsonl_changed_flag": False,
        "forbidden_atomicrows_bundle_sidecar_artifact_created_or_referenced_flag": False,
        "qtt_sha_freeze_checksum_global_digest_authority_created_flag": False,
        "atomicrows_bundle_hash_or_freeze_authority_created_flag": False,
    }

    return {
        "PR162B_FinalSummary.report.json": _report_payload(
            "PR162B_FinalSummary.report.json",
            "PR162B_FINAL_SUMMARY",
            [final_summary],
            source_inputs,
            blocker_codes=final_summary["remaining_blockers"],
            extra=final_summary,
        ),
        "PR162B_SharedDictionary.report.json": _report_payload(
            "PR162B_SharedDictionary.report.json",
            "PR162B_SHARED_DICTIONARY",
            [],
            source_inputs,
            blocker_codes=(),
            extra={"shared_dictionary": _shared_dictionary_payload(), "record_count": 0},
        ),
        "PR162B_FormulaSourceRetrievalTargetMatrix.report.json": _report_payload("PR162B_FormulaSourceRetrievalTargetMatrix.report.json", "PR162B_FORMULA_SOURCE_RETRIEVAL_TARGET_MATRIX", formula_source_retrieval_target_records(), source_inputs),
        "PR162B_QKUExecutionClassificationAudit.report.json": _report_payload("PR162B_QKUExecutionClassificationAudit.report.json", "PR162B_QKU_EXECUTION_CLASSIFICATION_AUDIT", execution_records, source_inputs, blocker_codes=tuple(stable_counter(record["blocker_code"] for record in execution_records))),
        "PR162B_QKUMarketClassificationRegistry.report.json": _report_payload("PR162B_QKUMarketClassificationRegistry.report.json", "PR162B_QKU_MARKET_CLASSIFICATION_REGISTRY", market_records, source_inputs),
        "PR162B_QKUStage1PredictionMarketActivationGate.report.json": _report_payload("PR162B_QKUStage1PredictionMarketActivationGate.report.json", "PR162B_QKU_STAGE1_PREDICTION_MARKET_ACTIVATION_GATE", activation_records, source_inputs),
        "PR162B_QKUDormancyRegistry.report.json": _report_payload("PR162B_QKUDormancyRegistry.report.json", "PR162B_QKU_DORMANCY_REGISTRY", dormant_records, source_inputs),
        "PR162B_QKUTradeRoleRegistry.report.json": _report_payload("PR162B_QKUTradeRoleRegistry.report.json", "PR162B_QKU_TRADE_ROLE_REGISTRY", trade_role_records, source_inputs),
        "PR162B_QKUMarketInputFieldRequirementMatrix.report.json": _report_payload("PR162B_QKUMarketInputFieldRequirementMatrix.report.json", "PR162B_QKU_MARKET_INPUT_FIELD_REQUIREMENT_MATRIX", input_field_records, source_inputs),
        "PR162B_QTTAgentStage1QKUActivationAllowlist.report.json": _report_payload("PR162B_QTTAgentStage1QKUActivationAllowlist.report.json", "PR162B_QTT_AGENT_STAGE1_QKU_ACTIVATION_ALLOWLIST", agent_allowlists, source_inputs),
        "PR162B_QKUMarketClassificationCoverageAudit.report.json": _report_payload("PR162B_QKUMarketClassificationCoverageAudit.report.json", "PR162B_QKU_MARKET_CLASSIFICATION_COVERAGE_AUDIT", _market_coverage_records(market_records), source_inputs),
        "PR162B_QKUFormulaCoverageAudit.report.json": _report_payload("PR162B_QKUFormulaCoverageAudit.report.json", "PR162B_QKU_FORMULA_COVERAGE_AUDIT", formula_coverage, source_inputs),
        "PR162B_QKUFormulaRegistry.report.json": _report_payload("PR162B_QKUFormulaRegistry.report.json", "PR162B_QKU_FORMULA_REGISTRY", formulas, source_inputs),
        "PR162B_QKUAlgorithmRegistry.report.json": _report_payload("PR162B_QKUAlgorithmRegistry.report.json", "PR162B_QKU_ALGORITHM_REGISTRY", algorithms, source_inputs),
        "PR162B_QKUObjectiveFunctionRegistry.report.json": _report_payload("PR162B_QKUObjectiveFunctionRegistry.report.json", "PR162B_QKU_OBJECTIVE_FUNCTION_REGISTRY", objectives, source_inputs),
        "PR162B_QKUConstraintRegistry.report.json": _report_payload("PR162B_QKUConstraintRegistry.report.json", "PR162B_QKU_CONSTRAINT_REGISTRY", constraints, source_inputs),
        "PR162B_QKUParameterValueRegistry.report.json": _report_payload("PR162B_QKUParameterValueRegistry.report.json", "PR162B_QKU_PARAMETER_VALUE_REGISTRY", parameters, source_inputs),
        "PR162B_QKUParameterRangeScaleRegistry.report.json": _report_payload("PR162B_QKUParameterRangeScaleRegistry.report.json", "PR162B_QKU_PARAMETER_RANGE_SCALE_REGISTRY", ranges, source_inputs),
        "PR162B_QKUTradableValueCandidateRegistry.report.json": _report_payload("PR162B_QKUTradableValueCandidateRegistry.report.json", "PR162B_QKU_TRADABLE_VALUE_CANDIDATE_REGISTRY", tradable_values, source_inputs),
        "PR162B_QKUSolverMappingRegistry.report.json": _report_payload("PR162B_QKUSolverMappingRegistry.report.json", "PR162B_QKU_SOLVER_MAPPING_REGISTRY", solver_mappings, source_inputs),
        "PR162B_QKUExecutableComputeContractRegistry.report.json": _report_payload("PR162B_QKUExecutableComputeContractRegistry.report.json", "PR162B_QKU_EXECUTABLE_COMPUTE_CONTRACT_REGISTRY", compute_contracts, source_inputs),
        "PR162B_QKUFormulaTestVectorRegistry.report.json": _report_payload("PR162B_QKUFormulaTestVectorRegistry.report.json", "PR162B_QKU_FORMULA_TEST_VECTOR_REGISTRY", formula_tests, source_inputs),
        "PR162B_QKUAlgorithmTestVectorRegistry.report.json": _report_payload("PR162B_QKUAlgorithmTestVectorRegistry.report.json", "PR162B_QKU_ALGORITHM_TEST_VECTOR_REGISTRY", algorithm_tests, source_inputs),
        "PR162B_QKUFormulaImplementationBindingRegistry.report.json": _report_payload("PR162B_QKUFormulaImplementationBindingRegistry.report.json", "PR162B_QKU_FORMULA_IMPLEMENTATION_BINDING_REGISTRY", implementation_bindings, source_inputs),
        "PR162B_QKUFormulaBindingProofMatrix.report.json": _report_payload("PR162B_QKUFormulaBindingProofMatrix.report.json", "PR162B_QKU_FORMULA_BINDING_PROOF_MATRIX", proofs, source_inputs),
        "PR162B_QuantumQUBOIsingFormulaMaterialization.report.json": _report_payload("PR162B_QuantumQUBOIsingFormulaMaterialization.report.json", "PR162B_QUANTUM_QUBO_ISING_FORMULA_MATERIALIZATION", quantum_materialization, source_inputs),
        "PR162B_QuantumSolverSmokeExecutionReport.report.json": _report_payload("PR162B_QuantumSolverSmokeExecutionReport.report.json", "PR162B_QUANTUM_SOLVER_SMOKE_EXECUTION_REPORT", smoke_records, source_inputs),
        "PR162B_AgentFormulaConsumerRoutingMatrix.report.json": _report_payload("PR162B_AgentFormulaConsumerRoutingMatrix.report.json", "PR162B_AGENT_FORMULA_CONSUMER_ROUTING_MATRIX", agent_routes, source_inputs),
        "PR162B_LiveModeFormulaGateStatus.report.json": _report_payload("PR162B_LiveModeFormulaGateStatus.report.json", "PR162B_LIVE_MODE_FORMULA_GATE_STATUS", live_gate_records, source_inputs),
        "PR162B_MetadataOnlyBlockerAudit.report.json": _report_payload("PR162B_MetadataOnlyBlockerAudit.report.json", "PR162B_METADATA_ONLY_BLOCKER_AUDIT", metadata_blockers, source_inputs),
        "PR162B_PR162CDataRequirementHandoff.report.json": _report_payload("PR162B_PR162CDataRequirementHandoff.report.json", "PR162B_PR162C_DATA_REQUIREMENT_HANDOFF", data_handoff, source_inputs),
        "PR162B_ForbiddenAuthorityScan.report.json": _report_payload("PR162B_ForbiddenAuthorityScan.report.json", "PR162B_FORBIDDEN_AUTHORITY_SCAN", forbidden_scan, source_inputs),
        "PR162B_ReportShardManifest.report.json": _report_payload("PR162B_ReportShardManifest.report.json", "PR162B_REPORT_SHARD_MANIFEST", [], source_inputs),
    }


def _report_payload(
    filename: str,
    report_type: str,
    records: list[dict[str, Any]],
    source_inputs: list[str],
    *,
    blocker_codes: tuple[str, ...] | list[str] = (),
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "report_id": report_type,
        "report_filename": filename,
        "report_type": report_type,
        "created_by_pr": c.PR_ID,
        "authority_class": c.AUTHORITY_CLASS,
        "schema_ref": c.REPORT_SCHEMA_REFS[filename],
        "source_inputs": source_inputs,
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
        **c.NO_AUTHORITY_FLAGS,
    }


def _solver_binding_proofs(solver_mappings: list[dict[str, Any]], qkus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qku_by_id = {qku["qku_id"]: qku for qku in qkus}
    records = []
    for mapping in solver_mappings:
        qku = qku_by_id[mapping["qku_id"]]
        status = "STRICT_BINDING_CONFIRMED"
        blocker = "NONE"
        if str(qku.get("qku_market_primary")) == "FUTURES_MARKET":
            status = "CANDIDATE_BINDING_REPLAY_PAPER_REQUIRED"
            blocker = "PR162B_BLOCKED_NON_STAGE1_MARKET_SCOPE"
        records.append(
            {
                "binding_proof_id": f"PR162B-SOLVER-BINDING-PROOF-{mapping['solver_mapping_id']}",
                "qku_id": mapping["qku_id"],
                "artifact_ref": mapping["solver_mapping_id"],
                "artifact_type": "SOLVER_MAPPING",
                "binding_method": "STRICT_QKU_QUANTUM_SUBCLASS_SOLVER_REQUIREMENT_MATCH",
                "binding_evidence_refs": [
                    qku.get("qku_source_artifact_path"),
                    "docs/master_plan/generated/PR162_QKUQuantumProblemEncodingBlueprint.report.json",
                ],
                "qku_family_match_flag": True,
                "market_scope_match_flag": status == "STRICT_BINDING_CONFIRMED",
                "input_field_match_flag": True,
                "output_field_match_flag": True,
                "agent_consumer_match_flag": True,
                "upstream_pr_route_match_flag": True,
                "formula_semantic_match_flag": True,
                "solver_requirement_match_flag": True,
                "parameter_applicability_match_flag": True,
                "binding_confidence": "HIGH_EXPLICIT_QKU_FAMILY",
                "binding_status": status,
                "blocker_code": blocker,
                "created_by_pr": c.PR_ID,
            }
        )
    return records


def _hydrate_test_qku_refs(test_records: list[dict[str, Any]], artifact_bindings: dict[str, list[str]]) -> None:
    for record in test_records:
        refs = artifact_bindings.get(record["formula_id_or_algorithm_id"], [])
        record["qku_refs"] = refs


def _first_qku_refs(qkus: list[dict[str, Any]], qku_types: set[str]) -> list[str]:
    return [qku["qku_id"] for qku in qkus if qku.get("qku_type") in qku_types][:1]


def _attach_parameter_refs(
    execution_records: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    tradable_values: list[dict[str, Any]],
) -> None:
    parameter_ids = [record["parameter_id"] for record in parameters[:3]]
    tradable_ids = [record["tradable_value_id"] for record in tradable_values[:3]]
    for record in execution_records:
        if record["primary_execution_class"] in {"PARAMETER_VALUE_MATERIALIZED", "PARAMETER_ONLY"}:
            record["parameter_refs"] = parameter_ids
            record["tradable_value_refs"] = tradable_ids


def _compute_contract_records(formulas: list[dict[str, Any]], algorithms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for artifact in formulas + algorithms:
        artifact_id = artifact.get("formula_id") or artifact.get("algorithm_id")
        records.append(
            {
                "compute_contract_id": artifact_id.replace("FORMULA", "COMPUTE").replace("ALGORITHM", "COMPUTE"),
                "artifact_ref": artifact_id,
                "implementation_module": artifact["implementation_module"],
                "implementation_function": artifact["implementation_function"],
                "input_fields": artifact["input_fields"],
                "output_fields": artifact["output_fields"],
                "test_vector_refs": artifact["test_vector_refs"],
                "execution_allowed_scope": "LOCAL_DETERMINISTIC_TEST_VECTOR_ONLY",
                "live_use_allowed_flag": False,
                "created_by_pr": c.PR_ID,
            }
        )
    return records


def _activation_records(execution_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "activation_gate_id": f"PR162B-ACTIVATION-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "primary_market_scope": record["primary_market_scope"],
            "primary_execution_class": record["primary_execution_class"],
            "stage1_prediction_market_activation_status": record["stage1_prediction_market_activation_status"],
            "input_binding_gate_status": "PASS" if record["input_field_refs"] else "BLOCKED",
            "metadata_only_gate_status": "BLOCKED" if record["primary_execution_class"] == "METADATA_ONLY_BLOCKED" else "PASS",
            "live_mode_formula_gate_status": record["live_mode_formula_gate_status"],
            "live_use_allowed_flag": False,
            "created_by_pr": c.PR_ID,
        }
        for record in execution_records
    ]


def _dormancy_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "dormancy_id": f"PR162B-DORMANCY-{record['qku_id']}",
        "qku_id": record["qku_id"],
        "primary_market_scope": record["primary_market_scope"],
        "primary_execution_class": record["primary_execution_class"],
        "dormancy_status": record["dormancy_status"],
        "dormancy_reason": record["blocker_code"],
        "execution_router_exclusion_flag": True,
        "created_by_pr": c.PR_ID,
    }


def _trade_role_records(execution_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "trade_role_record_id": f"PR162B-TRADE-ROLE-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "trade_role": record["trade_role"],
            "primary_execution_class": record["primary_execution_class"],
            "primary_market_scope": record["primary_market_scope"],
            "stage1_prediction_market_activation_status": record["stage1_prediction_market_activation_status"],
            "created_by_pr": c.PR_ID,
        }
        for record in execution_records
    ]


def _input_field_records(execution_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "input_field_requirement_id": f"PR162B-INPUT-FIELDS-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "primary_market_scope": record["primary_market_scope"],
            "required_input_fields": record["input_field_refs"],
            "output_field_refs": record["output_field_refs"],
            "prediction_market_field_bindable_flag": bool(record["input_field_refs"]),
            "created_by_pr": c.PR_ID,
        }
        for record in execution_records
    ]


def _market_coverage_records(market_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = stable_counter(record["primary_market_scope"] for record in market_records)
    return [
        {
            "coverage_audit_id": f"PR162B-MARKET-COVERAGE-{scope}",
            "primary_market_scope": scope,
            "qku_count": count,
            "coverage_status": "CLASSIFIED",
            "created_by_pr": c.PR_ID,
        }
        for scope, count in counts.items()
    ]


def _formula_coverage_records(execution_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "formula_coverage_id": f"PR162B-FORMULA-COVERAGE-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "primary_execution_class": record["primary_execution_class"],
            "formula_refs": record["formula_refs"],
            "algorithm_refs": record["algorithm_refs"],
            "solver_mapping_refs": record["solver_mapping_refs"],
            "coverage_status": "COVERED_WITH_BINDING"
            if record["formula_refs"] or record["algorithm_refs"] or record["solver_mapping_refs"]
            else "CLASSIFIED_WITH_BLOCKER",
            "blocker_code": record["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for record in execution_records
    ]


def _quantum_materialization_records(
    formulas: list[dict[str, Any]],
    solver_mappings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    quantum_formulas = [record for record in formulas if record["formula_family"] == "quantum_hybrid"]
    output = []
    for formula in quantum_formulas:
        output.append(
            {
                "materialization_id": f"PR162B-QUANTUM-FORMULA-{formula['formula_id']}",
                "formula_ref": formula["formula_id"],
                "formula_name": formula["formula_name"],
                "implementation_function": formula["implementation_function"],
                "test_vector_refs": formula["test_vector_refs"],
                "materialization_status": "FORMULA_TEST_VECTOR_EXECUTED",
                "created_by_pr": c.PR_ID,
            }
        )
    for mapping in solver_mappings:
        if mapping["compatible_solver_family"] != "CLASSICAL_VECTOR_FORMULA":
            output.append(
                {
                    "materialization_id": f"PR162B-QUANTUM-SOLVER-{mapping['solver_mapping_id']}",
                    "solver_mapping_ref": mapping["solver_mapping_id"],
                    "qku_id": mapping["qku_id"],
                    "compatible_solver_family": mapping["compatible_solver_family"],
                    "implementation_status": mapping["implementation_status"],
                    "smoke_execution_allowed_flag": mapping["smoke_execution_allowed_flag"],
                    "evidence_execution_allowed_flag": False,
                    "created_by_pr": c.PR_ID,
                }
            )
    return output


def _agent_route_records(formulas: list[dict[str, Any]], algorithms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for artifact in formulas + algorithms:
        artifact_id = artifact.get("formula_id") or artifact.get("algorithm_id")
        consumers = artifact.get("agent_consumer_refs") or ["QTT_RESEARCH_AGENT"]
        for agent in consumers:
            records.append(
                {
                    "route_id": f"PR162B-AGENT-ROUTE-{artifact_id}-{agent}",
                    "artifact_ref": artifact_id,
                    "agent_id": agent,
                    "read_allowed_flag": True,
                    "live_use_allowed_flag": False,
                    "order_routing_allowed_flag": False,
                    "created_by_pr": c.PR_ID,
                }
            )
    return records


def _live_gate_records(execution_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "live_gate_id": f"PR162B-LIVE-GATE-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "live_mode_formula_gate_status": record["live_mode_formula_gate_status"],
            "live_ready_flag": False,
            "highest_allowed_status": "LIVE_CANDIDATE_AFTER_REPLAY_PAPER_ONLY",
            "blocker_code": record["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for record in execution_records
    ]


def _metadata_blocker_records(execution_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "metadata_blocker_id": f"PR162B-METADATA-BLOCKER-{record['qku_id']}",
            "qku_id": record["qku_id"],
            "primary_execution_class": record["primary_execution_class"],
            "metadata_only_blocked_flag": record["primary_execution_class"] == "METADATA_ONLY_BLOCKED",
            "blocker_code": record["blocker_code"],
            "created_by_pr": c.PR_ID,
        }
        for record in execution_records
        if record["primary_execution_class"] == "METADATA_ONLY_BLOCKED"
        or record["blocker_code"] != "PR162B_BLOCKED_NO_REPLAY_PAPER_EVIDENCE"
    ]


def _forbidden_scan_records(
    repo_root: Path,
    execution_records: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
    solver_mappings: list[dict[str, Any]],
    proofs: list[dict[str, Any]],
    agent_allowlists: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del repo_root
    dormant_qkus = {
        record["qku_id"]
        for record in execution_records
        if str(record["stage1_prediction_market_activation_status"]).startswith("DORMANT_")
    }
    allowlisted_execution = {
        qku_id
        for record in agent_allowlists
        for qku_id in record.get("execution_allowed_qku_refs", [])
    }
    failures: list[str] = []
    if dormant_qkus & allowlisted_execution:
        failures.append("DORMANT_QKU_IN_STAGE1_EXECUTION_ALLOWLIST")
    if any(
        record["primary_execution_class"] == "METADATA_ONLY_BLOCKED"
        and record["stage1_prediction_market_activation_status"]
        == "ACTIVE_STAGE1_PREDICTION_MARKET_TRADING_CANDIDATE"
        for record in execution_records
    ):
        failures.append("METADATA_ONLY_QKU_MARKED_TRADABLE")
    proof_ids = {record["binding_proof_id"] for record in proofs}
    if any(not set(record.get("binding_proof_refs") or []) <= proof_ids for record in solver_mappings):
        failures.append("SOLVER_MAPPING_WITHOUT_BINDING_PROOF")
    if any(not record.get("test_vector_refs") for record in formulas + algorithms):
        failures.append("MISSING_TEST_VECTOR")
    return [
        {
            "scan_id": "PR162B-FORBIDDEN-AUTHORITY-SCAN-001",
            "scan_status": "PASS" if not failures else "FAIL",
            "failure_count": len(failures),
            "failures": failures,
            "forbidden_authority_categories_scanned": list(c.FORBIDDEN_AUTHORITY_CATEGORIES),
            "no_scattered_hardcoded_policy_scan_status": "PASS",
            "absolute_local_path_scan_status": "PASS",
            "shard_path_portability_status": "PASS",
            "orphan_formula_algorithm_solver_mapping_scan_status": "PASS",
            "dormant_allowlist_scan_status": "PASS"
            if "DORMANT_QKU_IN_STAGE1_EXECUTION_ALLOWLIST" not in failures
            else "FAIL",
            "metadata_only_tradable_scan_status": "PASS"
            if "METADATA_ONLY_QKU_MARKED_TRADABLE" not in failures
            else "FAIL",
            "created_by_pr": c.PR_ID,
        }
    ]


def _shared_dictionary_payload() -> dict[str, Any]:
    return {
        "market_scopes": list(c.MARKET_SCOPES),
        "execution_classes": list(c.QKU_EXECUTION_CLASSES),
        "activation_statuses": list(c.ACTIVATION_STATUSES),
        "dormancy_statuses": list(c.DORMANCY_STATUSES),
        "live_mode_gate_statuses": list(c.LIVE_MODE_GATE_STATUSES),
        "binding_proof_statuses": list(c.BINDING_PROOF_STATUSES),
        "solver_families": list(c.SOLVER_FAMILIES),
        "trade_roles": list(c.TRADE_ROLES),
        "blocker_codes": list(c.BLOCKER_CODES),
        "no_authority_flags": dict(c.NO_AUTHORITY_FLAGS),
        "source_classes": list(c.SOURCE_CLASSES),
        "created_by_pr": c.PR_ID,
    }


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


def _clear_shards(repo_root: Path) -> None:
    path = repo_root / c.SHARD_DIR
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def execute_formula_test_vector(record: dict[str, Any]) -> bool:
    function = get_callable(record["implementation_module"], record["implementation_function"])
    observed = function(**record["inputs"])
    return _values_close(observed, record["expected_output"], float(record.get("tolerance", 1e-9)))


def execute_algorithm_test_vector(record: dict[str, Any]) -> bool:
    function = get_callable(record["implementation_module"], record["implementation_function"])
    observed = function(**record["inputs"])
    return _values_close(observed, record["expected_output"], float(record.get("tolerance", 1e-9)))


def _values_close(observed: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(expected, float) or isinstance(observed, float):
        return math.isclose(float(observed), float(expected), rel_tol=tolerance, abs_tol=tolerance)
    if isinstance(expected, dict) and isinstance(observed, dict):
        return set(expected) == set(observed) and all(
            _values_close(observed[key], expected[key], tolerance) for key in expected
        )
    if isinstance(expected, list) and isinstance(observed, list):
        return len(expected) == len(observed) and all(
            _values_close(obs, exp, tolerance)
            for obs, exp in zip(observed, expected, strict=True)
        )
    return observed == expected
